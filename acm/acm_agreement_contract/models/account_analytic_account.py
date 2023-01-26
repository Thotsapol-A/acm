# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    agreement_id = fields.Many2one(
        comodel_name='agreement',
        string='Agreement',
        ondelete='restrict',
        readonly=True,
    )
    rent_product_id = fields.Many2one(
        comodel_name='product.product',
        compute='_compute_product_id',
        string='Rental Product',
        store=True,
    )
    group_id = fields.Many2one(
        string='Zone',
    )
    recurring_rule_type = fields.Selection(
        selection=[
            ('daily', 'Day(s)'),
            ('monthly', 'Month(s)'),
            ('yearly', 'Year(s)'),
        ],
    )
    income_type_id = fields.Many2one(
        comodel_name='agreement.income.type',
        string='Income Type',
        required=True,
        index=True,
    )

    @api.constrains('recurring_invoice_line_ids')
    def _check_recurring_invoice_line_ids(self):
        for rec in self:
            rent_products = \
                rec.recurring_invoice_line_ids.filtered(
                    lambda l: l.product_id.value_type == 'rent').mapped(
                        'product_id')
            if len(rent_products) > 1:
                raise UserError(_('Only one rental product is allowed.'))

    @api.depends('recurring_invoice_line_ids')
    def _compute_product_id(self):
        for rec in self:
            rent_products = rec.recurring_invoice_line_ids.filtered(
                lambda l: l.product_id.value_type == 'rent') \
                .mapped('product_id')
            if rent_products:
                rec.rent_product_id = rent_products[0]

    @api.model
    def _prepare_invoice_line(self, line, invoice_id):
        next_date = line.analytic_account_id.recurring_next_date
        # No create invoice lines
        if not (line.date_start or line.date_end):
            return {}
        if line.date_start and not line.date_end and \
           line.date_start > next_date:
            return {}
        if line.date_end and not line.date_start and next_date > line.date_end:
            return {}
        if not(line.date_start <= next_date <= line.date_end):
            return {}
        if line.manual:
            return {}
        invoice_line_vals = super(AccountAnalyticAccount, self)._prepare_invoice_line(line, invoice_id)
        # Overwrite account and taxes
        income_type = line.analytic_account_id.income_type_id
        if income_type and line.product_id.value_type == income_type.value_type:
            if income_type.account_id:
                invoice_line_vals['account_id'] = income_type.account_id.id
            if income_type.tax_ids:
                invoice_line_vals['invoice_line_tax_ids'] = [(6, 0, income_type.tax_ids.ids)]
        return invoice_line_vals

    @api.multi
    def recurring_create_invoice(self):
        """Create invoice only if Invoice contain some lines."""
        invoices = super().recurring_create_invoice()
        no_line_invs = invoices.filtered(lambda inv: not inv.invoice_line_ids)
        invoices -= no_line_invs
        no_line_invs.unlink()
        # Update date of next invoice
        for contract in self:
            agreement = contract.agreement_id
            if not agreement.agreement_invoice_line:
                continue
            next_date = contract.recurring_next_date
            invoice_date_days = agreement.invoice_date_days
            if next_date.day == invoice_date_days:
                continue
            contract.write({
                'recurring_next_date': '%s-%s-%s' % (
                    next_date.year, next_date.month, invoice_date_days)
            })
        return invoices

    @api.multi
    def _create_invoice(self, invoice=False):
        self.ensure_one()
        # Can not create invoice after termination date
        termination_date = self.agreement_id.termination_date
        if not self.active:
            raise ValidationError(_("Can not create invoice of %s with inactive contract.") % self.name)
        if termination_date and self.recurring_next_date > termination_date:
            raise ValidationError(_("Can not create invoice of %s after termination date.") % self.name)
        # Create invoice
        inv = super()._create_invoice(invoice=invoice)
        # Update invoice type
        type2 = 'rent'
        income_type = self.income_type_id
        if income_type and self.rent_product_id.value_type == income_type.value_type:
            type2 = income_type.invoice_type
        inv.write({
            'type2': type2,
            'name': self.rent_product_id.name,
        })
        return inv


class AccountAnalyticGroup(models.Model):
    _inherit = 'account.analytic.group'

    weight1 = fields.Char(
        string='Load weight',
    )
    weight2 = fields.Char(
        string='Other weight',
    )
    market_zone_map_ids = fields.One2many(
        comodel_name='market.zone.map',
        inverse_name='group_id',
        string='Market Zone Map',
    )


class MarketZoneMap(models.Model):
    _name = 'market.zone.map'
    _description = 'Market Zone Map'

    use_for_lock = fields.Selection(
        selection=[
            ('all', 'All'),
            ('custom', 'Custom')
        ],
        string='Use For Lock',
        default='all',
        required=True,
    )
    start_lock_number = fields.Char(
        strong='Start Lock Number',
    )
    end_lock_number = fields.Char(
        string='End Lock Number',
    )
    map = fields.Binary(
        string='Map',
    )
    group_id = fields.Many2one(
        comodel_name='account.analytic.group',
        string='Analytic Group',
    )

    @api.onchange("use_for_lock")
    def _onchange_use_for_lock(self):
        self.update({
            "start_lock_number": False,
            "end_lock_number": False,
        })

    @api.multi
    def has_map(self, lock_number):
        self.ensure_one()
        has_map = False
        if self.map:
            if self.use_for_lock == 'all':
                has_map = True
            elif self.use_for_lock == 'custom':
                try:
                    if float(self.start_lock_number) <= float(lock_number) <= float(self.end_lock_number):
                        has_map = True
                except Exception as ex:
                    has_map = False
        return has_map
