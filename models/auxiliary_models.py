# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EnergyProjection(models.Model):
    _name = 'sparks.energy.projection'
    _description = 'Energy Price Projection by Year'
    _order = 'name desc'

    name = fields.Char(
        string='Year', 
        size=4, 
        required=True,
        help="Year for price projection (e.g., 2024)"
    )
    actual_price = fields.Float(
        string='Actual Price (USD/kWh)',
        digits=(16, 4),
        help="Current energy price per kWh"
    )
    projected_price = fields.Float(
        string='Projected Price (USD/kWh)',
        digits=(16, 4),
        help="Projected energy price per kWh"
    )
    inflation_rate = fields.Float(
        string='Inflation Rate (%)',
        help="Expected annual inflation rate for energy prices"
    )
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Status', default='active')
    
    calculation_allowed = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ], string='Calculation Allowed', default='active')

    @api.constrains('name')
    def _check_year_format(self):
        for record in self:
            try:
                year = int(record.name)
                if year < 2020 or year > 2100:
                    raise ValidationError(_("Year must be between 2020 and 2100"))
            except ValueError:
                raise ValidationError(_("Year must be a valid number (e.g., 2024)"))


class SolarRadiation(models.Model):
    _name = 'sparks.solar.radiation'
    _description = 'Solar Radiation Data by Location'
    _rec_name = 'display_name'

    name = fields.Char(string='Record Name', required=True)
    year = fields.Many2one(
        'sparks.energy.projection', 
        string='Year', 
        required=True
    )
    country_id = fields.Many2one(
        'res.country', 
        string='Country', 
        required=True
    )
    state_id = fields.Many2one(
        'res.country.state', 
        string='Province/State', help="Province or state where the solar radiation is measured"
        #required=True
    )
    city = fields.Char(string='City', required=True)
    
    # Radiation adjustment
    percentage_adjustment = fields.Float(
        string='Adjustment (%)', 
        default=0.0,
        help="Percentage adjustment for local conditions"
    )
    
    # Monthly radiation data
    radiation_line_ids = fields.One2many(
        'sparks.solar.radiation.month', 
        'radiation_id', 
        string='Monthly Solar Radiation Data'
    )

    # Computed radiation values
    average_radiation = fields.Float(
        string='Average Daily Radiation (kWh/m²)',
        compute='_compute_radiation_totals',
        store=True
    )
    total_radiation = fields.Float(
        string='Total Annual Radiation (kWh/m²)',
        compute='_compute_radiation_totals',
        store=True
    )
    average_radiation_adjusted = fields.Float(
        string='Adjusted Average Radiation (kWh/m²)',
        compute='_compute_radiation_totals',
        store=True
    )
    total_radiation_adjusted = fields.Float(
        string='Adjusted Annual Radiation (kWh/m²)',
        compute='_compute_radiation_totals',
        store=True
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('city', 'state_id', 'country_id', 'year')
    def _compute_display_name(self):
        for record in self:
            parts = []
            if record.city:
                parts.append(record.city)
            if record.state_id:
                parts.append(record.state_id.name)
            if record.country_id:
                parts.append(record.country_id.name)
            if record.year:
                parts.append(f"({record.year.name})")
            
            record.display_name = " - ".join(parts)

    @api.depends('radiation_line_ids.radiation', 'radiation_line_ids.radiation_adjusted', 'percentage_adjustment')
    def _compute_radiation_totals(self):
        for record in self:
            radiation_data = record.radiation_line_ids.mapped('radiation')
            radiation_adjusted_data = record.radiation_line_ids.mapped('radiation_adjusted')
            
            if radiation_data:
                record.total_radiation = sum(radiation_data)
                record.average_radiation = record.total_radiation / 12
            else:
                record.total_radiation = 0.0
                record.average_radiation = 0.0
            
            if radiation_adjusted_data:
                record.total_radiation_adjusted = sum(radiation_adjusted_data)
                record.average_radiation_adjusted = record.total_radiation_adjusted / 12
            else:
                record.total_radiation_adjusted = 0.0
                record.average_radiation_adjusted = 0.0

    @api.model
    def create(self, vals):
        record = super().create(vals)
        # Create 12 months of radiation data automatically
        if not record.radiation_line_ids:
            record._create_monthly_lines()
        return record

    def _create_monthly_lines(self):
        """Create 12 monthly radiation lines"""
        month_data = [
            ('1', 'January'), ('2', 'February'), ('3', 'March'),
            ('4', 'April'), ('5', 'May'), ('6', 'June'),
            ('7', 'July'), ('8', 'August'), ('9', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')
        ]
        
        for month_num, month_name in month_data:
            self.env['sparks.solar.radiation.month'].create({
                'radiation_id': self.id,
                'month': month_num,
                'radiation': 4.5,  # Default value
            })
    # Agregar este método en la clase SolarRadiation (después del método _create_monthly_lines)

    @api.model
    def _get_state_by_code(self, country_code, state_code):
        """Helper method to get state by country and state code"""
        return self.env['res.country.state'].search([
            ('code', '=', state_code),
            ('country_id.code', '=', country_code)
        ], limit=1)

    def _set_default_state_ecuador(self):
        """Set default state for Ecuador if not specified"""
        if not self.state_id and self.country_id and self.country_id.code == 'EC':
            # Default to Manabí (code 13) for Ecuador
            default_state = self._get_state_by_code('EC', '13')
            if default_state:
                self.state_id = default_state
    


class SolarRadiationMonth(models.Model):
    _name = 'sparks.solar.radiation.month'
    _description = 'Monthly Solar Radiation Data'
    _order = 'month'

    radiation_id = fields.Many2one(
        'sparks.solar.radiation', 
        string='Solar Radiation Record',
        required=True,
        ondelete='cascade'
    )
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month', required=True)
    
    radiation = fields.Float(
        string='Daily Radiation (kWh/m²/day)', 
        required=True,
        help="Average daily solar radiation for this month"
    )
    days_in_month = fields.Integer(
        string='Days in Month',
        compute='_compute_days_in_month',
        store=True
    )
    radiation_adjusted = fields.Float(
        string='Adjusted Radiation (kWh/m²/day)',
        compute='_compute_radiation_adjusted',
        store=True
    )
    monthly_total = fields.Float(
        string='Monthly Total (kWh/m²)',
        compute='_compute_monthly_total',
        store=True
    )

    @api.depends('month')
    def _compute_days_in_month(self):
        days_per_month = {
            '1': 31, '2': 28, '3': 31, '4': 30, '5': 31, '6': 30,
            '7': 31, '8': 31, '9': 30, '10': 31, '11': 30, '12': 31
        }
        for record in self:
            record.days_in_month = days_per_month.get(record.month, 30)

    @api.depends('radiation', 'radiation_id.percentage_adjustment')
    def _compute_radiation_adjusted(self):
        for record in self:
            adjustment = record.radiation_id.percentage_adjustment / 100.0
            record.radiation_adjusted = record.radiation * (1 + adjustment)

    @api.depends('radiation_adjusted', 'days_in_month')
    def _compute_monthly_total(self):
        for record in self:
            record.monthly_total = record.radiation_adjusted * record.days_in_month

    @api.constrains('month', 'radiation_id')
    def _check_unique_month(self):
        for record in self:
            existing = self.search([
                ('radiation_id', '=', record.radiation_id.id),
                ('month', '=', record.month),
                ('id', '!=', record.id)
            ])
            if existing:
                month_name = dict(self._fields['month'].selection)[record.month]
                raise ValidationError(_("Month %s is already defined for this radiation record.") % month_name)


class SolarKitPowerCapacity(models.Model):
    _name = 'sparks.solar.kit.capacity'
    _description = 'Solar Kit Power Capacity Options'
    _order = 'power'

    name = fields.Char(
        string='Description', 
        required=True,
        help="Description of the power capacity (e.g., '5kW System')"
    )
    power = fields.Float(
        string='Power Capacity (kW)', 
        required=True,
        help="Power capacity in kilowatts"
    )
    recommended_usage = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('all', 'All Applications')
    ], string='Recommended Usage', default='all')
    
    active = fields.Boolean(string='Active', default=True)

    @api.constrains('power')
    def _check_power_positive(self):
        for record in self:
            if record.power <= 0:
                raise ValidationError(_("Power capacity must be positive"))


class SolarKitReferenceCost(models.Model):
    _name = 'sparks.solar.kit.reference'
    _description = 'Solar Kit Reference Cost by Year'

    name = fields.Char(
        string='Description', 
        required=True,
        help="Description of the cost reference"
    )
    year = fields.Many2one(
        'sparks.energy.projection', 
        string='Reference Year', 
        required=True
    )
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    detail_line_ids = fields.One2many(
        'sparks.solar.kit.detail', 
        'reference_id', 
        string='Cost Details by Capacity'
    )
    
    active = fields.Boolean(string='Active', default=True)


class SolarKitDetail(models.Model):
    _name = 'sparks.solar.kit.detail'
    _description = 'Solar Kit Cost Detail by Power Capacity'

    reference_id = fields.Many2one(
        'sparks.solar.kit.reference', 
        string='Reference Cost', 
        required=True,
        ondelete='cascade'
    )
    power_capacity_id = fields.Many2one(
        'sparks.solar.kit.capacity', 
        string='Power Capacity', 
        required=True
    )
    
    # Cost components
    equipment_cost = fields.Monetary(
        string='Equipment Cost',
        currency_field='currency_id',
        help="Cost of panels, inverters, and equipment"
    )
    installation_cost = fields.Monetary(
        string='Installation Cost',
        currency_field='currency_id',
        help="Labor and installation costs"
    )
    freight_cost = fields.Monetary(
        string='Freight Cost',
        currency_field='currency_id',
        help="Shipping and logistics costs"
    )
    other_costs = fields.Monetary(
        string='Other Costs',
        currency_field='currency_id',
        help="Permits, miscellaneous costs"
    )
    
    # Totals
    total_cost = fields.Monetary(
        string='Total Cost',
        currency_field='currency_id',
        compute='_compute_total_cost',
        store=True
    )
    cost_per_kw = fields.Monetary(
        string='Cost per kW',
        currency_field='currency_id',
        compute='_compute_cost_per_kw',
        store=True
    )
    
    currency_id = fields.Many2one(
        related='reference_id.currency_id',
        store=True
    )

    @api.depends('equipment_cost', 'installation_cost', 'freight_cost', 'other_costs')
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = (
                record.equipment_cost + 
                record.installation_cost + 
                record.freight_cost + 
                record.other_costs
            )

    @api.depends('total_cost', 'power_capacity_id.power')
    def _compute_cost_per_kw(self):
        for record in self:
            if record.power_capacity_id.power > 0:
                record.cost_per_kw = record.total_cost / record.power_capacity_id.power
            else:
                record.cost_per_kw = 0.0

    @api.constrains('power_capacity_id', 'reference_id')
    def _check_unique_capacity(self):
        for record in self:
            existing = self.search([
                ('reference_id', '=', record.reference_id.id),
                ('power_capacity_id', '=', record.power_capacity_id.id),
                ('id', '!=', record.id)
            ])
            if existing:
                raise ValidationError(
                    _("Power capacity %s is already defined for this reference cost.") % 
                    record.power_capacity_id.name
                )
