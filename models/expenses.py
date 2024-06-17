from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AsftPetttycashExpense(models.Model):
    _name = 'asft.pettycash.expense'
    _description = "Pettycash Expense"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Document Number')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='user', default=lambda self: self.env.user.id)
    state = fields.Selection([("draft","Draft"),("submit","Submit"),("approved","Approved"),("rejected","Rejected"),("posted","Posted")],tracking=True, string='State', default='draft')
    pettycash_type = fields.Many2one('asft.pettycash.type', string='Pettycash')
    account = fields.Many2one('account.account', string='Account', compute='_get_account_pettycash', store=True,)
    submit_date = fields.Date(string='Submit Date')
    journal_id = fields.Many2one('account.journal', string='Journal Expense')
    line_ids = fields.One2many('asft.pettycash.expense.line', 'expense_id', string='Expense')
    price_total = fields.Float(string='Total', compute='_get_price_total', store=True,)
    account_move_id = fields.Many2one('account.move', string='Jurnal Entries')
    has_reported = fields.Boolean(string='Reported', default=False)

    @api.depends('line_ids')
    def _get_price_total(self):
        for doc in self:
            doc.price_total = sum(doc.line_ids.mapped('price_total'))
    

    @api.depends('pettycash_type')
    def _get_account_pettycash(self):
        for doc in self:
            doc.account = doc.pettycash_type.account.id
            doc.journal_id = doc.pettycash_type.journal_exp_id.id

    @api.model
    def create(self,vals):
       nomor = self.env['ir.sequence'].sudo().next_by_code('asft.pettycash.expense')
       vals['name'] = nomor
       res = super(AsftPetttycashExpense,self).create(vals)
       return res
    
    def unlink(self):
        for doc in self:
            if doc.state != "draft":
                raise UserError('Document status not draft')
        return super(AsftPetttycashExpense,self).unlink()

    def action_submit(self):
        if self.price_total == 0:
            raise UserError('Expense total cannot 0')
        else:
            self.state = 'submit'
            self.submit_date = fields.Date.today()

    def action_rejected(self):
        self.state = 'rejected'
    
    def action_draft(self):
        self.state = 'draft'
    
    def action_approve(self):
        if not self.account.id  or not self.journal_id.id:
            raise UserError('Account dan Journal harus diisi')
        else:
            self._create_journal()
            self.state = 'approved'
    
    def _create_journal(self):
        journal_data = {}
        journal_data['ref'] = "Expense Pettycash " + str(self.name)
        journal_data['date'] = fields.Date.today()
        journal_data['journal_id'] = self.journal_id.id
        data_items = []
        data_items.append((0,0,{"account_id": self.account.id,"partner_id": self.user_id.partner_id.id,"name": "Expense Pettycash "+ str(self.name),"credit": self.price_total, "debit": 0}))
        for baris in self.line_ids:
            data_items.append((0,0,{"account_id": baris.account_id.id,"partner_id": self.user_id.partner_id.id,"name": "Expense Pettycash "+ str(self.name)+" "+str(baris.name),"credit": 0, "debit": baris.price_total}))
        journal_data['line_ids'] = data_items
        create_jurnal = self.env['account.move'].sudo().create(journal_data)
        self.account_move_id = create_jurnal.id
    
    def action_posted(self):
        get_account_move = self.env['account.move'].sudo().search([('id','=',self.account_move_id.id)])
        if len(get_account_move) > 0:
            get_account_move.action_post()
            self.state = "posted"
        else:
            raise UserError('Account Move not set')
    
class AsftPetttycashExpenseItems(models.Model):
    _name = 'asft.pettycash.expense.line'
    _description = "Pettycash Expense lines"

    name = fields.Char(string='Description', compute='_get_product_name', store=True,)
    product_id = fields.Many2one('product.product', string='Product Item')
    expense_id = fields.Many2one('asft.pettycash.expense', string='expense id')
    quantity = fields.Float(string='Quantity')
    price = fields.Float(string='Price')
    date_expense = fields.Date(string='Date', default=fields.Date.today())
    attachment = fields.Binary(string='Attachment')
    price_total = fields.Float(string='Total', compute='_get_price_total', store=True,)
    account_id = fields.Many2one('account.account', string='Expense Account', store=True, compute='_get_product_name',)
    tax_ids = fields.Many2many(comodel_name='account.tax', relation='pettycash_expense_tax_rel', string='Taxes') 

    def _get_price_total(self):
        for doc in self:
            doc.price_total = doc.quantity * doc.price

    @api.depends('product_id')
    def _get_product_name(self):
        for doc in self:
            if doc.product_id.id != False:
                doc.name = doc.product_id.name
                product_account = doc.product_id.property_account_expense_id.id
                if product_account == False:
                    product_account = doc.product_id.categ_id.property_account_expense_categ_id.id
                if product_account == False:
                    raise UserError('Product Account expense / Product Category Expense not set')
                doc.account_id = product_account

    @api.depends('quantity', 'price')
    def _get_price_total(self):
        for doc in self:
            doc.price_total = doc.quantity * doc.price