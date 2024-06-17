from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AsftPattyCash(models.Model):
    _name = 'asft.pettycash'
    _description = 'Pettycash'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Document Number')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='user', default=lambda self: self.env.user.id)
    submit_date = fields.Date(string='Submit Date')
    state = fields.Selection([("draft","Draft"),("submit","Submit"),("approved","Approved"),("rejected","Rejected"),("posted","Posted")],tracking=True, string='State', default='draft')
    pettycash_type = fields.Many2one('asft.pettycash.type', string='Pettycash')
    request_amount = fields.Float(string='Request Amount',tracking=True)
    account = fields.Many2one('account.account', string='Account', compute='_get_account_pettycash', store=True,)
    credit_account = fields.Many2one('account.account', string='Credit Account')
    journal_id = fields.Many2one('account.journal', string='Journal')
    account_move_id = fields.Many2one('account.move', string='Jurnal Entries')
    notes = fields.Text(string='Notes')

    @api.depends('pettycash_type')
    def _get_account_pettycash(self):
        for doc in self:
            doc.account = doc.pettycash_type.account.id
            doc.journal_id = doc.pettycash_type.journal_id.id

    @api.model
    def create(self,vals):
       nomor = self.env['ir.sequence'].sudo().next_by_code('asft.pettycash')
       vals['name'] = nomor
       res = super(AsftPattyCash,self).create(vals)
       return res
    
    def action_submit(self):
        if self.request_amount == 0:
            raise UserError('Request cannot 0')
        else:
            self.state = 'submit'
            self.submit_date = fields.Date.today()

    def action_rejected(self):
        self.state = 'rejected'
    
    def action_draft(self):
        self.state = 'draft'

    def action_approve(self):
        if not self.credit_account.id  or not self.journal_id.id:
            raise UserError('credit Account dan Journal harus diisi')
        else:
            #create journal
            journal_data = {}
            journal_data['ref'] = "Pengisian Pettycash " + str(self.name)
            journal_data['date'] = fields.Date.today()
            journal_data['journal_id'] = self.journal_id.id
            data_items = []
            data_items.append((0,0,{"account_id": self.credit_account.id,"partner_id": self.user_id.partner_id.id,"name": "Pettycash "+ str(self.name),"credit": self.request_amount, "debit": 0}))
            data_items.append((0,0,{"account_id": self.account.id,"partner_id": self.user_id.partner_id.id,"name": "Pettycash "+ str(self.name),"credit": 0, "debit": self.request_amount}))
            journal_data['line_ids'] = data_items
            create_jurnal = self.env['account.move'].sudo().create(journal_data)
            self.account_move_id = create_jurnal.id
            self.state = 'approved'
    
    def action_posted(self):
        get_account_move = self.env['account.move'].sudo().search([('id','=',self.account_move_id.id)])
        if len(get_account_move) > 0:
            get_account_move.action_post()
            self.state = "posted"
        else:
            raise UserError('Account Move not set')
    
    def unlink(self):
        for doc in self:
            if doc.state != "draft":
                raise UserError('Document status not draft')
        return super(AsftPattyCash,self).unlink()