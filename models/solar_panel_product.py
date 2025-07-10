# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SolarPanelProduct(models.Model):
    _name = 'sparks.solar.panel.product'
    _description = 'Solar Panel Product Catalog'
    _rec_name = 'display_name'
    _order = 'power_wp desc, efficiency desc'

    # Basic Information
    name = fields.Char(
        string='Panel Model', 
        required=True,
        help="Commercial name of the solar panel (e.g., 'Jinko Solar JKM550M-7RL4-V')"
    )
    
    manufacturer = fields.Char(
        string='Manufacturer',
        required=True,
        help="Panel manufacturer (e.g., 'Jinko Solar', 'Canadian Solar')"
    )
    
    model_code = fields.Char(
        string='Model Code',
        help="Internal model code or SKU"
    )
    
    # Technical Specifications
    power_wp = fields.Float(
        string='Power (Wp)',
        required=True,
        help="Nominal power in Watts peak under standard test conditions"
    )
    
    efficiency = fields.Float(
        string='Efficiency (%)',
        required=True,
        help="Panel efficiency percentage"
    )
    
    # Physical Dimensions
    length_mm = fields.Float(
        string='Length (mm)',
        required=True,
        help="Panel length in millimeters"
    )
    
    width_mm = fields.Float(
        string='Width (mm)',
        required=True,
        help="Panel width in millimeters"
    )
    
    thickness_mm = fields.Float(
        string='Thickness (mm)',
        help="Panel thickness in millimeters"
    )
    
    # Calculated Areas
    area_m2 = fields.Float(
        string='Area (m²)',
        compute='_compute_area',
        store=True,
        help="Panel area in square meters"
    )
    
    power_density = fields.Float(
        string='Power Density (W/m²)',
        compute='_compute_power_density',
        store=True,
        help="Power per square meter"
    )
    
    # Technology and Quality
    technology = fields.Selection([
        ('mono', 'Monocrystalline'),
        ('poly', 'Polycrystalline'),
        ('thin_film', 'Thin Film'),
        ('bifacial', 'Bifacial'),
        ('perc', 'PERC'),
        ('hjt', 'Heterojunction (HJT)'),
        ('topcon', 'TOPCon')
    ], string='Technology', default='mono', required=True)
    
    # Performance Specifications
    voltage_vmp = fields.Float(string='Vmp (V)', help="Voltage at maximum power point")
    current_imp = fields.Float(string='Imp (A)', help="Current at maximum power point")
    voltage_voc = fields.Float(string='Voc (V)', help="Open circuit voltage")
    current_isc = fields.Float(string='Isc (A)', help="Short circuit current")
    
    # Temperature Coefficients
    temp_coeff_power = fields.Float(
        string='Power Temp. Coeff. (%/°C)',
        help="Power temperature coefficient"
    )
    temp_coeff_voltage = fields.Float(
        string='Voltage Temp. Coeff. (%/°C)',
        help="Voltage temperature coefficient"
    )
    
    # Commercial Information
    unit_cost = fields.Monetary(
        string='Unit Cost (Before Tax)',
        currency_field='currency_id',
        help="Cost per panel before taxes"
    )
    
    warranty_years = fields.Integer(
        string='Warranty (Years)',
        default=25,
        help="Product warranty in years"
    )
    
    # Status and Categories
    active = fields.Boolean(string='Active', default=True)
    is_preferred = fields.Boolean(
        string='Preferred Panel',
        help="Mark as preferred for quotations"
    )
    
    application = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('industrial', 'Industrial'),
        ('utility', 'Utility Scale'),
        ('all', 'All Applications')
    ], string='Recommended Application', default='all')
    
    # Additional Information
    description = fields.Text(string='Description')
    notes = fields.Text(string='Technical Notes')
    datasheet_url = fields.Url(string='Datasheet URL')
    
    # System Integration
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
    
    # Display name
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('length_mm', 'width_mm')
    def _compute_area(self):
        for panel in self:
            if panel.length_mm and panel.width_mm:
                # Convert mm² to m²
                panel.area_m2 = (panel.length_mm * panel.width_mm) / 1000000
            else:
                panel.area_m2 = 0.0

    @api.depends('power_wp', 'area_m2')
    def _compute_power_density(self):
        for panel in self:
            if panel.area_m2 > 0:
                panel.power_density = panel.power_wp / panel.area_m2
            else:
                panel.power_density = 0.0

    @api.depends('manufacturer', 'name', 'power_wp')
    def _compute_display_name(self):
        for panel in self:
            parts = []
            if panel.manufacturer:
                parts.append(panel.manufacturer)
            if panel.name:
                parts.append(panel.name)
            if panel.power_wp:
                parts.append(f"({int(panel.power_wp)}W)")
            panel.display_name = " ".join(parts)

    @api.constrains('power_wp')
    def _check_power_positive(self):
        for panel in self:
            if panel.power_wp <= 0:
                raise ValidationError(_("Panel power must be positive"))

    @api.constrains('efficiency')
    def _check_efficiency_range(self):
        for panel in self:
            if not (0 < panel.efficiency <= 100):
                raise ValidationError(_("Panel efficiency must be between 0 and 100"))

    @api.constrains('length_mm', 'width_mm')
    def _check_dimensions_positive(self):
        for panel in self:
            if panel.length_mm <= 0 or panel.width_mm <= 0:
                raise ValidationError(_("Panel dimensions must be positive"))

    def get_panels_needed_for_power(self, required_power_kw):
        """Calculate number of panels needed for required power"""
        self.ensure_one()
        if self.power_wp <= 0:
            return 0
        
        required_power_wp = required_power_kw * 1000
        panels_needed = required_power_wp / self.power_wp
        return int(panels_needed) + (1 if panels_needed % 1 > 0 else 0)  # Round up

    def get_total_area_for_panels(self, panel_quantity):
        """Calculate total area needed for given number of panels"""
        self.ensure_one()
        return panel_quantity * self.area_m2

    def get_actual_power_for_panels(self, panel_quantity):
        """Calculate actual power for given number of panels"""
        self.ensure_one()
        return (panel_quantity * self.power_wp) / 1000  # Return in kW

    @api.model
    def get_best_panel_for_power(self, required_power_kw, application='all', preferred_only=False):
        """Find the best panel for required power based on various criteria"""
        domain = [('active', '=', True)]
        
        if application != 'all':
            domain.append(('application', 'in', [application, 'all']))
        
        if preferred_only:
            domain.append(('is_preferred', '=', True))
        
        # Get all suitable panels
        panels = self.search(domain)
        
        if not panels:
            return False
        
        # Score panels based on multiple criteria
        panel_scores = []
        for panel in panels:
            panels_needed = panel.get_panels_needed_for_power(required_power_kw)
            actual_power = panel.get_actual_power_for_panels(panels_needed)
            total_area = panel.get_total_area_for_panels(panels_needed)
            total_cost = panels_needed * (panel.unit_cost or 0)
            
            # Calculate score (higher is better)
            score = 0
            
            # Prefer higher efficiency
            score += panel.efficiency * 2
            
            # Prefer less area usage
            if total_area > 0:
                score += (1000 / total_area)  # Inverse of area
            
            # Prefer lower cost per kW
            if total_cost > 0 and actual_power > 0:
                cost_per_kw = total_cost / actual_power
                score += (10000 / cost_per_kw)  # Inverse of cost per kW
            
            # Prefer preferred panels
            if panel.is_preferred:
                score += 50
            
            # Prefer newer technology
            tech_bonus = {
                'hjt': 30, 'topcon': 25, 'perc': 20, 'bifacial': 15,
                'mono': 10, 'poly': 5, 'thin_film': 0
            }
            score += tech_bonus.get(panel.technology, 0)
            
            panel_scores.append((panel, score, panels_needed, actual_power, total_area))
        
        # Return best panel based on score
        best_panel_data = max(panel_scores, key=lambda x: x[1])
        return {
            'panel': best_panel_data[0],
            'panels_needed': best_panel_data[2],
            'actual_power_kw': best_panel_data[3],
            'total_area_m2': best_panel_data[4],
            'score': best_panel_data[1]
        }