# Copyright 2019 Ecosoft Co., Ltd (https://ecosoft.co.th/)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models, fields, api
from odoo.addons import decimal_precision as dp
from odoo.tools import pycompat


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    width = fields.Float(
        string='Width',
    )
    length1 = fields.Float(
        string='Length',
    )
    area = fields.Float(
        string='Area For Lease',
        digits=dp.get_precision('Area'),
    )
    working_hours_id = fields.Many2one(
        comodel_name='acm.working.hours',
        string='Working Hours',
        compute='_compute_working_hours_id',
        inverse='_set_working_hours_id',
        domain="[('type', '=', 'in_time')]",
        store=True,
    )
    working_hours2_id = fields.Many2one(
        comodel_name='acm.working.hours',
        string='Not Working Hours',
        compute='_compute_working_hours2_id',
        inverse='_set_working_hours2_id',
        domain="[('type', '=', 'out_time')]",
        store=True,
    )
    value_type = fields.Selection(
        selection=[
            ('rent', 'Rent'),
            ('lump_sum_rent', 'Lump Sum Rent'),
            ('security_deposit', 'Security Deposit'),
            ('transfer', 'Transfer'),
        ],
        string='Value Type',
    )
    # goods_type = fields.Char(
    #     string='Goods Type',
    #     compute='_compute_goods_type',
    #     inverse='_set_goods_type',
    #     store=True,
    # )
    # goods_category_id = fields.Many2one(
    #     comodel_name='goods.category',
    #     string='Goods Category',
    #     compute='_compute_goods_category_id',
    #     inverse='_set_goods_category_id',
    #     store=True,
    # )
    group_id = fields.Many2one(
        comodel_name='account.analytic.group',
        string='Zone',
    )
    subzone = fields.Char(
        string='Subzone',
    )
    lock_number = fields.Char(
        string='Number',
    )
    lock_attribute = fields.Many2one(
        comodel_name='lock.attribute',
    )
    manual = fields.Boolean()
    inactive_date = fields.Date(
        string='Inactive Date',
    )

    _sql_constraints = [
        ('name_uniq', 'UNIQUE(name)', 'Name must be unique!'),
    ]

    # @api.depends('product_variant_ids', 'product_variant_ids.goods_type')
    # def _compute_goods_type(self):
    #     unique_variants = self.filtered(
    #         lambda template: len(template.product_variant_ids) == 1)
    #     for template in unique_variants:
    #         template.goods_type = template.product_variant_ids.goods_type
    #     for template in (self - unique_variants):
    #         template.goods_type = ''

    # @api.one
    # def _set_goods_type(self):
    #     if len(self.product_variant_ids) == 1:
    #         self.product_variant_ids.goods_type = self.goods_type

    # @api.depends('product_variant_ids',
    #              'product_variant_ids.goods_category_id')
    # def _compute_goods_category_id(self):
    #     unique_variants = self.filtered(
    #         lambda template: len(template.product_variant_ids) == 1)
    #     for template in unique_variants:
    #         template.goods_category_id = \
    #             template.product_variant_ids.goods_category_id.id
    #     for template in (self - unique_variants):
    #         template.goods_category_id = False

    # @api.one
    # def _set_goods_category_id(self):
    #     if len(self.product_variant_ids) == 1:
    #         self.product_variant_ids.goods_category_id = \
    #             self.goods_category_id.id

    @api.depends('product_variant_ids',
                 'product_variant_ids.working_hours_id')
    def _compute_working_hours_id(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.working_hours_id = \
                template.product_variant_ids.working_hours_id.id
        for template in (self - unique_variants):
            template.working_hours_id = False

    @api.one
    def _set_working_hours_id(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.working_hours_id = \
                self.working_hours_id.id

    @api.depends('product_variant_ids',
                 'product_variant_ids.working_hours2_id')
    def _compute_working_hours2_id(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.working_hours2_id = \
                template.product_variant_ids.working_hours2_id.id
        for template in (self - unique_variants):
            template.working_hours2_id = False

    @api.one
    def _set_working_hours2_id(self):
        if len(self.product_variant_ids) == 1:
            self.product_variant_ids.working_hours2_id = \
                self.working_hours2_id.id

    @api.onchange('group_id', 'subzone', 'lock_number')
    def _onchange_group_number(self):
        """
            If product type is rent, format name should be GROUP-SUBZONE-LOCK_NUMBER
            Ex: 1A-001 or 1F-T-001
        """
        names = []
        if self.group_id:
            names.append(self.group_id.name)
        if self.subzone:
            names.append(self.subzone)
        if self.lock_number:
            names.append(self.lock_number)
        self.name = '-'.join(names)

    @api.onchange('manual')
    def _onchange_manual(self):
        """ If select manual field, let reset width, length and area """
        self.width = 0
        self.length1 = 0
        self.area = 0

    @api.onchange('width', 'length1')
    def _onchange_width_length(self):
        """ Area = Width x Length """
        self.area = self.width * self.length1

    @api.model_create_multi
    def create(self, vals_list):
        templates = super(ProductTemplate, self).create(vals_list)
        for template, vals in pycompat.izip(templates, vals_list):
            related_vals = {}
            if vals.get('working_hours_id'):
                related_vals['working_hours_id'] = vals['working_hours_id']
            if vals.get('working_hours2_id'):
                related_vals['working_hours2_id'] = vals['working_hours2_id']
            # if vals.get('goods_type'):
            #     related_vals['goods_type'] = vals['goods_type']
            # if vals.get('goods_category_id'):
            #     related_vals['goods_category_id'] = vals['goods_category_id']
            if related_vals:
                template.write(related_vals)
        return templates

    @api.multi
    def write(self, vals):
        """"Update inactive date when archive product"""
        if 'active' in vals:
            vals['inactive_date'] = False
            if not vals['active']:
                vals['inactive_date'] = fields.Date.context_today(self)
        res = super(ProductTemplate, self).write(vals)
        # Update inactive date in product variant
        if 'inactive_date' in vals:
            self.with_context(active_test=False).mapped('product_variant_ids').filtered(
                lambda l: not l.active and l.inactive_date != vals['inactive_date']
            ).write({'inactive_date': vals['inactive_date']})
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # goods_type = fields.Char(
    #     string='Goods Type',
    # )
    # goods_category_id = fields.Many2one(
    #     comodel_name='goods.category',
    #     string='Goods Category',
    # )
    working_hours_id = fields.Many2one(
        comodel_name='acm.working.hours',
        string='Working Hours',
        domain="[('type', '=', 'in_time')]",
    )
    working_hours2_id = fields.Many2one(
        comodel_name='acm.working.hours',
        string='Not Working Hours',
        domain="[('type', '=', 'out_time')]",
    )
    inactive_date = fields.Date(
        string='Inactive Date',
    )

    @api.onchange('group_id', 'subzone', 'lock_number')
    def _onchange_group_number(self):
        """
            If product type is rent, format name should be GROUP-SUBZONE-LOCK_NUMBER
            Ex: 1A-001 or 1F-T-001
        """
        names = []
        if self.group_id:
            names.append(self.group_id.name)
        if self.subzone:
            names.append(self.subzone)
        if self.lock_number:
            names.append(self.lock_number)
        self.name = '-'.join(names)

    @api.onchange('manual')
    def _onchange_manual(self):
        """ If select manual field, let reset width, length and area """
        self.width = 0
        self.length1 = 0
        self.area = 0

    @api.onchange('width', 'length1')
    def _onchange_width_length(self):
        """ Area = Width x Length """
        self.area = self.width * self.length1

    @api.multi
    def write(self, vals):
        """"Update inactive date when archive product"""
        if 'active' in vals:
            vals['inactive_date'] = False
            if not vals['active']:
                vals['inactive_date'] = fields.Date.context_today(self)
        return super(ProductProduct, self).write(vals)
