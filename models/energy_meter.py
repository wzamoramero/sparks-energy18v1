# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class EnergyMeter(models.Model):
    _name = 'sparks.energy.meter'
    _description = 'Energy Meter'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'

    # Basic Information
    name = fields.Char(
        string='Meter Code', 
        required=True,
        help="Internal meter identification code"
    )
    supply_number = fields.Char(
        string='Supply Number', 
        required=True,
        help="Official supply number from electricity company"
    )
    meter_serial = fields.Char(
        string='Meter Serial Number',
        help="Physical meter serial number"
    )
    
    # Customer and Location
    partner_id = fields.Many2one(
        'res.partner', 
        string='Customer', 
        required=True,
        tracking=True
    )
    installation_address = fields.Text(
        string='Installation Address',
        help="Specific address where this meter is installed"
    )
    city_id = fields.Many2one(
        'sparks.solar.radiation', 
        string='City/Location',
        help="City for solar radiation data"
    )
    
    # Meter Configuration
    meter_type = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial')
    ], string='Meter Type', default='residential', tracking=True)
    
    voltage_level = fields.Selection([
        ('low', 'Low Voltage (110-240V)'),
        ('medium', 'Medium Voltage (1-35kV)'),
        ('high', 'High Voltage (>35kV)')
    ], string='Voltage Level', default='low')
    
    phases = fields.Selection([
        ('single', 'Single Phase'),
        ('three', 'Three Phase')
    ], string='Phases', default='single')
    
    # Status and Dates
    status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('disconnected', 'Disconnected'),
        ('maintenance', 'Under Maintenance')
    ], string='Status', default='active', tracking=True)
    
    installation_date = fields.Date(string='Installation Date')
    last_reading_date = fields.Date(string='Last Reading Date')
    
    # Consumption Data
    consumption_line_ids = fields.One2many(
        'sparks.meter.consumption', 
        'meter_id', 
        string='Historical Consumption'
    )
    
    # Solar Quotations
    quotation_ids = fields.Many2many(
        'sparks.solar.quotation',
        'quotation_meter_rel',
        'meter_id',
        'quotation_id',
        string='Solar Quotations'
    )
    quotation_count = fields.Integer(
        string='Quotations Count',
        compute='_compute_quotation_count'
    )
    
    # Computed Statistics
    average_monthly_consumption = fields.Float(
        string='Average Monthly Consumption (kWh)',
        compute='_compute_consumption_stats',
        store=True
    )
    peak_monthly_consumption = fields.Float(
        string='Peak Monthly Consumption (kWh)',
        compute='_compute_consumption_stats',
        store=True
    )
    total_annual_consumption = fields.Float(
        string='Annual Consumption (kWh)',
        compute='_compute_consumption_stats',
        store=True
    )
    last_12_months_consumption = fields.Float(
        string='Last 12 Months Consumption (kWh)',
        compute='_compute_consumption_stats',
        store=True
    )
    
    # Display name
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    # Additional fields
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one(
        'res.company', 
        string='Company',
        default=lambda self: self.env.company
    )

    @api.depends('name', 'supply_number', 'partner_id')
    def _compute_display_name(self):
        for meter in self:
            parts = []
            if meter.name:
                parts.append(meter.name)
            if meter.supply_number:
                parts.append(f"({meter.supply_number})")
            if meter.partner_id:
                parts.append(f"- {meter.partner_id.name}")
            meter.display_name = " ".join(parts)

    @api.depends('quotation_ids')
    def _compute_quotation_count(self):
        for meter in self:
            meter.quotation_count = len(meter.quotation_ids)

    @api.depends('consumption_line_ids.energy_kwh')
    def _compute_consumption_stats(self):
        for meter in self:
            consumptions = meter.consumption_line_ids
            if consumptions:
                consumption_values = consumptions.mapped('energy_kwh')
                meter.total_annual_consumption = sum(consumption_values)
                meter.average_monthly_consumption = meter.total_annual_consumption / len(consumption_values) if consumption_values else 0
                meter.peak_monthly_consumption = max(consumption_values) if consumption_values else 0
                
                # Last 12 months (assuming we have chronological data)
                recent_consumptions = consumptions.sorted('year_month', reverse=True)[:12]
                meter.last_12_months_consumption = sum(recent_consumptions.mapped('energy_kwh'))
            else:
                meter.total_annual_consumption = 0
                meter.average_monthly_consumption = 0
                meter.peak_monthly_consumption = 0
                meter.last_12_months_consumption = 0

    @api.constrains('supply_number')
    def _check_unique_supply_number(self):
        for meter in self:
            if meter.supply_number:
                existing = self.search([
                    ('supply_number', '=', meter.supply_number),
                    ('id', '!=', meter.id)
                ])
                if existing:
                    raise ValidationError(_("Supply number '%s' already exists for meter '%s'") % 
                                        (meter.supply_number, existing.display_name))


    @api.onchange('city_id')
    def _onchange_city_id(self):
        """Update installation address suggestions based on city"""
        if self.city_id and self.city_id.city:
            if not self.installation_address:
                # Suggest city name in address if empty
                self.installation_address = f"{self.city_id.city}, {self.city_id.state_id.name if self.city_id.state_id else 'Ecuador'}"

    def action_view_quotations(self):
        """View solar quotations for this meter"""
        self.ensure_one()
        action = self.env.ref('sparks.action_solar_quotation').read()[0]
        
        if len(self.quotation_ids) > 1:
            action['domain'] = [('meter_ids', 'in', [self.id])]
        elif len(self.quotation_ids) == 1:
            action['views'] = [(self.env.ref('sparks.view_solar_quotation_form').id, 'form')]
            action['res_id'] = self.quotation_ids.id
        else:
            # Create new quotation
            action = {
                'type': 'ir.actions.act_window',
                'name': 'New Solar Quotation',
                'res_model': 'sparks.solar.quotation',
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'default_partner_id': self.partner_id.id,
                    'default_meter_ids': [(6, 0, [self.id])],
                    'default_installation_address': self.installation_address,
                    'default_city_id': self.city_id.id if self.city_id else False,
                }
            }
        
        return action

    def action_create_quotation(self):
        """Create new solar quotation for this meter"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'New Solar Quotation',
            'res_model': 'sparks.solar.quotation',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_meter_ids': [(6, 0, [self.id])],
                'default_installation_address': self.installation_address,
                'default_city_id': self.city_id.id if self.city_id else False,
            }
        }

    def action_import_consumption(self):
        """Import consumption data for this meter"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Import Consumption Data',
            'res_model': 'sparks.import.meter.consumption.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_meter_id': self.id,
            }
        }


class MeterConsumption(models.Model):
    _name = 'sparks.meter.consumption'
    _description = 'Historical Energy Consumption by Meter'
    _order = 'year_month desc'

    meter_id = fields.Many2one(
        'sparks.energy.meter', 
        string='Energy Meter', 
        required=True,
        ondelete='cascade'
    )
    
    # Date fields
    year = fields.Integer(string='Year', required=True)
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True)
    
    year_month = fields.Char(
        string='Year-Month',
        compute='_compute_year_month',
        store=True,
        index=True
    )
    
    # Consumption data
    energy_kwh = fields.Float(
        string='Energy Consumption (kWh)', 
        required=True
    )
    energy_cost = fields.Monetary(
        string='Energy Cost',
        currency_field='currency_id'
    )
    
    # Additional meter readings
    power_factor = fields.Float(string='Power Factor')
    max_demand_kw = fields.Float(string='Max Demand (kW)')
    peak_hours_kwh = fields.Float(string='Peak Hours (kWh)')
    off_peak_hours_kwh = fields.Float(string='Off-Peak Hours (kWh)')
    
    # Bill information
    bill_number = fields.Char(string='Bill Number')
    bill_date = fields.Date(string='Bill Date')
    due_date = fields.Date(string='Due Date')
    
    # Currency
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # Notes
    notes = fields.Text(string='Notes')

    @api.depends('year', 'month')
    def _compute_year_month(self):
        for record in self:
            if record.year and record.month:
                record.year_month = f"{record.year}-{record.month:02d}"
            else:
                record.year_month = ""

    @api.constrains('year', 'month', 'meter_id')
    def _check_unique_month_per_meter(self):
        for record in self:
            existing = self.search([
                ('meter_id', '=', record.meter_id.id),
                ('year', '=', record.year),
                ('month', '=', record.month),
                ('id', '!=', record.id)
            ])
            if existing:
                month_name = dict(self._fields['month'].selection)[record.month]
                raise ValidationError(
                    _("Consumption for %s %d already exists for meter '%s'") % 
                    (month_name, record.year, record.meter_id.display_name)
                )

    @api.constrains('energy_kwh')
    def _check_positive_consumption(self):
        for record in self:
            if record.energy_kwh < 0:
                raise ValidationError(_("Energy consumption cannot be negative"))
