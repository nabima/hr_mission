# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions
from datetime import datetime


class HrMission(models.Model):
    _name = 'hr.employee.mission'
    _description = 'Mission object'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    
    _STATES = { 'new':      [('readonly', False)], 
                'confirme': [('readonly', True)],
                'visa1':    [('readonly', True)],
                'visa2':    [('readonly', True)],
                'valide':   [('readonly', True)],
                'valide_mg':[('readonly', True)],
                'refuse':   [('readonly', True)],
                'annule':   [('readonly', True)],
              }
    @api.depends("hotel","peage","repas","carburant")
    @api.one
    def _budget(self):
        self.budget = self.hotel + self.peage + self.carburant + self.repas
    
    employee_id =           fields.Many2one('hr.employee', string=u'Employée', help="Employee sent on mission", ondelete='restrict',required=True,track_visibility="onchange",states = _STATES)
    mission_id =            fields.Char(string=u'Réference', help="Mission reference. Define by company own organisation", size=20, required=True, default="/" , copy=False,track_visibility="onchange",states = _STATES)
    name =                  fields.Char(string='Objet de la Mission', help="Mission aim task to do", size=80, required=True,track_visibility="onchange",states = _STATES)
    mission_objective =     fields.Text(string='Objectif', help="Mission objective",track_visibility="onchange",states = _STATES)
    mission_start_date =    fields.Datetime(string=u"Date de début",help="Mission start date", required=True,track_visibility="onchange",states = _STATES)
    mission_end_date =      fields.Datetime(string=u"Date de fin",  help="Mission end date", required=True,track_visibility="onchange",states = _STATES)
    mission_partner =       fields.Many2one('hr.agence', string='Agence', required=True,track_visibility="onchange",states = _STATES)
    mission_location =      fields.Char(string='Lieu de mission', help="Location where the mission will be take place",track_visibility="onchange",states = _STATES)
    mission_partner_manager = fields.Many2one('res.employee', string='Mission manager', help="Responsible of this mission", required=False,track_visibility="onchange",states = _STATES)
    mission_duration =      fields.Char(compute='_get_duration', default=0, string=u"Durée", readonly=True,track_visibility="onchange",states = _STATES)
    mission_evaluation =    fields.Text(string='Evaluation',track_visibility="onchange",states = _STATES)
    mission_notes =         fields.Text(string='Notes',track_visibility="onchange",states = _STATES)
    mission_car =           fields.Selection([('pc', 'Voiture personnelle'), ('cc', u"Voiture d'entreprise"),
                                              ('tp', 'Transport public(Train,Car,Taxi..)'),
                                              ('other', 'Autre')], string=u"Motorité",track_visibility="onchange",states = _STATES)
    mission_type =          fields.Many2one('hr.mission.type', string='Type de mission', required=False,track_visibility="onchange",states = _STATES)
    mission_budget =        fields.Float(string=u"Budget alloué", help="Allocated budget for this mission",track_visibility="onchange",states = _STATES)
    budget  =               fields.Float(string=u"Budget alloué", help="Allocated budget for this mission", required=True,track_visibility="onchange",states = _STATES,compute=_budget,store=True)
    hotel= fields.Float(u"Hôtel")
    peage= fields.Float(u"Péage")
    repas= fields.Float(u"Repas")
    carburant= fields.Float(u"Carburant")
    use = fields.Boolean(u"Usé")
    
    
    # Mission state for workflow implementation
    state = fields.Selection([
         ('new', "Nouveau"),
         ('confirme', u"Confirmé"),
         ('visa1', "Validation responsable"),
         ('visa2', "Chef de département"),
         ('valide', "Validation RH"),
         ('valide_mg', "Validation MG"),
         ('refuse', u"Refusé"),
         ('annule', u"Annulé"),
     ], default='new',track_visibility="onchange")
    
    @api.multi
    def forcer_validation(self):
        for o in self:
            o.signal_workflow("visa1")
            o.signal_workflow("visa2")
            o.signal_workflow("valide")
            o.message_post(subject=u"VALIDATION FORCEE!",body="Document Validé par l'utilisateur ci-dessous'")
    @api.multi
    def cancel_draft(self):
        for o in self:
            o.delete_workflow()
            o.create_workflow()
            o.state = "new"
            o.message_post(subject=u"Réinitialisation forcée!",body="Document réinitialisé par l'utilisateur ci-dessous'")
    
    @api.one
    def user(self):
        return self.user
        
#    @api.model
#    def get_own_missions(self):
#        self.env.cr.execute('SELECT date FROM hr_mission_ where id=119')
#        return self.env.cr.fetchone()
    
    @api.model
    def create(self,vals):
        if vals.get('mission_id', '/') == '/':
            agence = self.env['hr.agence'].sudo().browse(vals['mission_partner'])
            seq = self.env.ref("base.mission_sequence").next_by_code('nabi.mission') 
            vals['mission_id'] = seq.replace('OM-','OM-%s-' % agence.code)
            
        new_id = super(HrMission, self).create(vals)
        new_id.message_post(body=u"Demande créée")
        return new_id
        
        
        
    
        
        
    @api.constrains('mission_end_date')
    @api.onchange('mission_start_date', 'mission_end_date')
    def _get_duration(self):
        for rec in self:
            if rec.mission_start_date and rec.mission_end_date:
                # get the date today as 2018-07-19
                td = datetime.now().strftime('%Y-%m-%d')
                today = datetime.strptime(td, "%Y-%m-%d")
                start = datetime.strptime(rec.mission_start_date, "%Y-%m-%d %H:%M:%S")

                if today.date() > start.date():
                    pass
                    #raise exceptions.ValidationError("Your mission start date must be higher or equal to"
                    #                                 " today date")

                if rec.mission_end_date > rec.mission_start_date:
                    time1 = datetime.strptime(rec.mission_start_date, "%Y-%m-%d %H:%M:%S")
                    time2 = datetime.strptime(rec.mission_end_date, "%Y-%m-%d %H:%M:%S")
                    delta = str(time2 - time1)
                    rec.mission_duration = delta
                else:
                    pass
                    #raise exceptions.ValidationError("Your mission end date must be higher than"
                    #                                 " mission start date ! %s" % rec.mission_end_date)

#    @api.multi
#    def action_draft(self):
#        self.state = 'draft'

#    @api.multi
#    def action_to_approve(self):
#        self.state = 'to_approve'

#    @api.multi
#    def action_approve(self):
#        self.state = 'approved'

#    @api.multi
#    def action_reject(self):
#        self.state = 'rejected'
#        
#    


class HrEmployee(models.Model):
    _name = "hr.employee"
    _description = "Employee Category"
    _inherit = "hr.employee"

    in_mission = fields.Boolean(string="En mission")
    missions_ids = fields.One2many('hr.employee.mission', 'employee_id', string='Missions')


class HrExpense(models.Model):
    _name = 'hr.expense.expense'
    _description = "Expense"
    _inherit = 'hr.expense.expense'

    mission_id = fields.Many2one('hr.employee.mission', 'Missions ID', help='Related mission if exist')


class HrMissionType(models.Model):
    _name = "hr.mission.type"
    _description = "Mission Type"

    name = fields.Char('Nom', Required=True)
    description = fields.Char(u'Déscription', help='Describe this mission type aim !')
