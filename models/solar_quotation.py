# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

_logger.info("=== LOADING SPARKS QUOTATION ===")

class SolarQuotation(models.Model):
    _name = 'sparks.solar.quotation'
    _description = 'Solar Energy System Quotation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Basic Information
    name = fields.Char(
        string='Quotation Number', 
        required=True, 
        copy=False, 
        readonly=True, 
        default=lambda self: _('New')
    )
    partner_id = fields.Many2one(
        'res.partner', 
        string='Customer', 
        required=True, 
        tracking=True
    )
    meter_ids = fields.Many2many(
        'sparks.energy.meter',
        'quotation_meter_rel',
        'quotation_id',
        'meter_id',
        string='Energy Meters',
        domain="[('partner_id', '=', partner_id)]",
        help="Select one or more meters for this quotation. Consumption will be accumulated."
    )
    meter_count = fields.Integer(
        string='Number of Meters',
        compute='_compute_meter_count',
        store=True
    )
    
    # Location Information
    installation_address = fields.Text(
        string='Installation Address',
        compute='_compute_installation_address',
        store=True,
        readonly=False
    )
    city_id = fields.Many2one(
        'sparks.solar.radiation', 
        string='City', 
        required=True,
        compute='_compute_city_from_meters',
        store=True,
        readonly=False
    )
    
    # Consumption Data
    consumption_line_ids = fields.One2many(
        'sparks.consumption.line', 
        'quotation_id', 
        string='Monthly Consumption'
    )
    
    # System Design
    selected_panel_id = fields.Many2one(
        'sparks.solar.panel.product',
        string='Selected Solar Panel',
        help="Solar panel model selected for this quotation"
    )
    system_power_kw = fields.Float(
        string='System Power (kW)', 
        compute='_compute_system_specifications',
        store=True
    )
    panel_quantity = fields.Integer(
        string='Number of Panels',
        compute='_compute_system_specifications',
        store=True
    )
    actual_system_power_kw = fields.Float(
        string='Actual System Power (kW)',
        compute='_compute_system_specifications',
        store=True,
        help="Actual power based on selected panels and quantity"
    )
    total_panel_area_m2 = fields.Float(
        string='Total Panel Area (m²)',
        compute='_compute_system_specifications',
        store=True
    )
    panel_power_wp = fields.Float(
        string='Panel Power (Wp)', 
        related='selected_panel_id.power_wp',
        store=True
    )
    panel_area_m2 = fields.Float(
        string='Panel Area (m²)',
        related='selected_panel_id.area_m2',
        store=True
    )
    system_efficiency = fields.Float(string='System Efficiency (%)', default=85.0)
    
    # Financial Information
    subtotal_investment = fields.Monetary(
        string='Subtotal Investment',
        compute='_compute_financial_data',
        store=True,
        currency_field='currency_id'
    )
    tax_rate = fields.Float(string='Tax Rate (%)', default=12.0)
    tax_amount = fields.Monetary(
        string='Tax Amount',
        compute='_compute_financial_data',
        store=True,
        currency_field='currency_id'
    )
    total_investment = fields.Monetary(
        string='Total Investment',
        compute='_compute_financial_data',
        store=True,
        currency_field='currency_id'
    )
    monthly_savings = fields.Monetary(
        string='Average Monthly Savings',
        compute='_compute_financial_data',
        store=True,
        currency_field='currency_id'
    )
    payback_period_years = fields.Float(
        string='Payback Period (Years)',
        compute='_compute_financial_data',
        store=True
    )
    
    # Computed consumption data
    total_annual_consumption = fields.Float(
        string='Annual Consumption (kWh)',
        compute='_compute_consumption_data',
        store=True
    )
    average_monthly_consumption = fields.Float(
        string='Average Monthly Consumption (kWh)',
        compute='_compute_consumption_data',
        store=True
    )
    peak_monthly_consumption = fields.Float(
        string='Peak Monthly Consumption (kWh)',
        compute='_compute_consumption_data',
        store=True
    )
    
    # Energy production calculations
    estimated_annual_production = fields.Float(
        string='Estimated Annual Production (kWh)',
        compute='_compute_energy_production',
        store=True
    )
    coverage_percentage = fields.Float(
        string='Energy Coverage (%)',
        compute='_compute_energy_production',
        store=True
    )
    
    # Solar radiation field
    annual_solar_radiation = fields.Float(
        string='Annual Solar Radiation (kWh/m²)',
        related='city_id.total_radiation_adjusted',
        store=True
    )
    
    # Status and workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculated', 'Calculated'),
        ('sent', 'Sent'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Additional fields
    currency_id = fields.Many2one(
        'res.currency', 
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        'res.company', 
        string='Company',
        default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        'res.users', 
        string='Salesperson',
        default=lambda self: self.env.user,
        tracking=True
    )
    
    # Dates
    quotation_date = fields.Date(string='Quotation Date', default=fields.Date.today)
    validity_date = fields.Date(string='Valid Until')
    
    # Notes
    description = fields.Html(string='Description')
    terms_conditions = fields.Html(string='Terms and Conditions')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sparks.solar.quotation') or _('New')
        return super().create(vals)

    @api.depends('meter_ids')
    def _compute_meter_count(self):
        for record in self:
            record.meter_count = len(record.meter_ids)

    @api.depends('meter_ids.installation_address')
    def _compute_installation_address(self):
        for record in self:
            if record.meter_ids:
                # Use the first meter's address or concatenate if different
                addresses = record.meter_ids.mapped('installation_address')
                unique_addresses = [addr for addr in addresses if addr]
                if len(set(unique_addresses)) == 1:
                    # All meters have same address
                    record.installation_address = unique_addresses[0] if unique_addresses else ""
                elif unique_addresses:
                    # Multiple addresses, concatenate
                    record.installation_address = "\n".join(f"Meter {meter.name}: {meter.installation_address}" 
                                                           for meter in record.meter_ids 
                                                           if meter.installation_address)
                else:
                    record.installation_address = record.partner_id.contact_address if record.partner_id else ""
            elif not record.installation_address and record.partner_id:
                record.installation_address = record.partner_id.contact_address

    @api.depends('meter_ids.city_id')
    def _compute_city_from_meters(self):
        for record in self:
            if record.meter_ids:
                # Use the most common city or the first one
                cities = record.meter_ids.mapped('city_id')
                cities = cities.filtered(lambda c: c)
                if cities:
                    record.city_id = cities[0]

    @api.onchange('city_id')
    def _onchange_city_id(self):
        """Validate city selection based on installation location"""
        if self.city_id and self.installation_address:
            # You can add validation logic here if needed
            pass

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Reset meters when customer changes"""
        if self.partner_id:
            self.meter_ids = False
            # If customer has only one meter, auto-select it
            meters = self.env['sparks.energy.meter'].search([('partner_id', '=', self.partner_id.id)])
            if len(meters) == 1:
                self.meter_ids = [(6, 0, [meters.id])]

    @api.onchange('meter_ids')
    def _onchange_meter_ids(self):
        """Auto-populate consumption data from selected meters"""
        if self.meter_ids:
            # Clear existing consumption lines
            self.consumption_line_ids = [(5, 0, 0)]
            
            # Aggregate consumption data from all selected meters
            consumption_by_month = {}
            
            for meter in self.meter_ids:
                # Get latest 12 months of consumption for each meter
                latest_consumptions = meter.consumption_line_ids.sorted('year desc, month desc')[:12]
                
                for consumption in latest_consumptions:
                    month_key = consumption.month
                    if month_key not in consumption_by_month:
                        consumption_by_month[month_key] = {
                            'energy_kwh': 0,
                            'energy_cost': 0,
                        }
                    
                    consumption_by_month[month_key]['energy_kwh'] += consumption.energy_kwh
                    consumption_by_month[month_key]['energy_cost'] += (consumption.energy_cost or 0)
            
            # Create consumption lines with aggregated data
            if consumption_by_month:
                consumption_lines = []
                for month, data in consumption_by_month.items():
                    consumption_lines.append((0, 0, {
                        'month': str(month),
                        'energy_kwh': data['energy_kwh'],
                        'energy_cost': data['energy_cost'],
                    }))
                self.consumption_line_ids = consumption_lines

    @api.depends('consumption_line_ids.energy_kwh')
    def _compute_consumption_data(self):
        for record in self:
            consumption_data = record.consumption_line_ids.mapped('energy_kwh')
            if consumption_data:
                record.total_annual_consumption = sum(consumption_data)
                record.average_monthly_consumption = record.total_annual_consumption / 12
                record.peak_monthly_consumption = max(consumption_data)
            else:
                record.total_annual_consumption = 0.0
                record.average_monthly_consumption = 0.0
                record.peak_monthly_consumption = 0.0

    @api.depends('total_annual_consumption', 'city_id', 'system_efficiency', 'panel_power_wp')
    def _compute_system_specifications(self):
        for record in self:
            if record.total_annual_consumption and record.city_id:
                # Calculate required system power based on consumption and solar radiation
                annual_radiation = record.city_id.total_radiation_adjusted or record.city_id.total_radiation
                if annual_radiation > 0:
                    # System power calculation considering efficiency losses
                    efficiency_factor = record.system_efficiency / 100.0
                    record.system_power_kw = (
                        record.total_annual_consumption / 
                        (annual_radiation * efficiency_factor)
                    )
                    
                    # Calculate number of panels and actual system power
                    if record.selected_panel_id and record.panel_power_wp > 0:
                        record.panel_quantity = int(
                            (record.system_power_kw * 1000) / record.panel_power_wp
                        ) + 1  # Round up
                        
                        # Calculate actual system power based on panel quantity
                        record.actual_system_power_kw = (record.panel_quantity * record.panel_power_wp) / 1000
                        
                        # Calculate total panel area
                        record.total_panel_area_m2 = record.panel_quantity * (record.panel_area_m2 or 0)
                    else:
                        record.panel_quantity = 0
                        record.actual_system_power_kw = record.system_power_kw
                        record.total_panel_area_m2 = 0.0
                else:
                    record.system_power_kw = 0.0
                    record.panel_quantity = 0
                    record.actual_system_power_kw = 0.0
                    record.total_panel_area_m2 = 0.0
            else:
                record.system_power_kw = 0.0
                record.panel_quantity = 0
                record.actual_system_power_kw = 0.0
                record.total_panel_area_m2 = 0.0

    @api.depends('actual_system_power_kw', 'city_id', 'system_efficiency')
    def _compute_energy_production(self):
        for record in self:
            if record.actual_system_power_kw and record.city_id:
                annual_radiation = record.city_id.total_radiation_adjusted or record.city_id.total_radiation
                efficiency_factor = record.system_efficiency / 100.0
                
                record.estimated_annual_production = (
                    record.actual_system_power_kw * annual_radiation * efficiency_factor
                )
                
                if record.total_annual_consumption > 0:
                    record.coverage_percentage = min(
                        (record.estimated_annual_production / record.total_annual_consumption) * 100,
                        100.0
                    )
                else:
                    record.coverage_percentage = 0.0
            else:
                record.estimated_annual_production = 0.0
                record.coverage_percentage = 0.0

    @api.depends('actual_system_power_kw', 'estimated_annual_production', 'tax_rate')
    def _compute_financial_data(self):
        for record in self:
            if record.actual_system_power_kw:
                # Get cost per kW from solar kit data (simplified)
                cost_per_kw = 1200.0  # Default cost per kW USD
                solar_kit = self.env['sparks.solar.kit.detail'].search([
                    ('power_capacity_id.power', '>=', record.actual_system_power_kw)
                ], limit=1, order='power_capacity_id.power asc')
                
                if solar_kit:
                    cost_per_kw = solar_kit.cost_per_kw
                
                # Calculate subtotal and total with taxes
                record.subtotal_investment = record.actual_system_power_kw * cost_per_kw
                record.tax_amount = record.subtotal_investment * (record.tax_rate / 100)
                record.total_investment = record.subtotal_investment + record.tax_amount
                
                # Calculate monthly savings based on energy production
                if record.estimated_annual_production:
                    # Get current energy price
                    current_year = fields.Date.today().year
                    energy_price = self.env['sparks.energy.projection'].search([
                        ('name', '=', str(current_year))
                    ], limit=1)
                    
                    if energy_price:
                        annual_savings = record.estimated_annual_production * energy_price.projected_price
                        record.monthly_savings = annual_savings / 12
                        
                        # Calculate payback period
                        if record.monthly_savings > 0:
                            record.payback_period_years = record.total_investment / (record.monthly_savings * 12)
                        else:
                            record.payback_period_years = 0.0
                    else:
                        record.monthly_savings = 0.0
                        record.payback_period_years = 0.0
                else:
                    record.monthly_savings = 0.0
                    record.payback_period_years = 0.0
            else:
                record.subtotal_investment = 0.0
                record.tax_amount = 0.0
                record.total_investment = 0.0
                record.monthly_savings = 0.0
                record.payback_period_years = 0.0

    def action_calculate_system(self):
        """Recalculate system specifications"""
        self.ensure_one()
        if not self.consumption_line_ids:
            raise ValidationError(_("Please add monthly consumption data before calculating the system."))
        
        # Trigger recalculation
        self._compute_consumption_data()
        self._compute_system_specifications()
        self._compute_energy_production()
        self._compute_financial_data()
        
        self.state = 'calculated'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('System Calculated'),
                'message': _('Solar system specifications have been calculated successfully.'),
                'type': 'success',
            }
        }

    def action_send_quotation(self):
        """Send quotation to customer"""
        self.ensure_one()
        if self.state != 'calculated':
            raise ValidationError(_("Please calculate the system first."))
        
        self.state = 'sent'
        # Here you can add email sending logic
        
        return True

    def action_confirm_quotation(self):
        """Confirm quotation and create sale order"""
        self.ensure_one()
        self.state = 'confirmed'
        
        # Create sale order logic can be added here
        return True

    def action_reset_to_draft(self):
        """Reset quotation to draft"""
        self.state = 'draft'
        return True

_logger.info("=== SPARKS QUOTATION LOADED SUCCESSFULLY ===")
