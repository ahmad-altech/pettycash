from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError

class AsftPettycashJenisPettycash(models.Model):
    _name = 'asft.pettycash.type'
    _description = 'Pettycash Type'

    name = fields.Char(string='Description')
    account = fields.Many2one('account.account', string='Account')
    active = fields.Boolean(string='Active', default=True)
    pic = fields.Many2one('res.users', string='PIC')
    journal_id = fields.Many2one('account.journal', string='Journal Bank/Cash')
    journal_exp_id = fields.Many2one('account.journal', string='Journal Expense')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    fullfillment = fields.Boolean(string='Fullfilment', help="Set Pettycash Type to Fullfilment Method")
    treshold_min = fields.Integer(string='Minimum Amout')
    treshold_max = fields.Integer(string='Maximum Amount')

    @api.constrains('account')
    def _check_account_duplicate(self):
        for doc in self:
            get_data = doc.env['asft.pettycash.type'].search([('company_id','=',doc.company_id.id),('account','=', doc.account.id),('id','!=',doc.id)])
            if len(get_data) > 0:
                raise ValidationError("Account sudah di set pada Pettycash  "+ str(get_data[0].name))