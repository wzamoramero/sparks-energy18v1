# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Energy meters related fields
    energy_meter_ids = fields.One2many(
        'sparks.energy.meter', 
        'partner_id', 
        string='Energy Meters'
    )
    energy_meter_count = fields.Integer(
        string='Energy Meters Count',
        compute='_compute_energy_meter_count'
    )

    # Solar quotation related fields
    solar_quotation_ids = fields.One2many(
        'sparks.solar.quotation', 
        'partner_id', 
        string='Solar Quotations'
    )
    solar_quotation_count = fields.Integer(
        string='Solar Quotations Count',
        compute='_compute_solar_quotation_count'
    )
    
    # Energy consumption information
    total_monthly_consumption = fields.Float(
        string='Total Monthly Consumption (kWh)',
        compute='_compute_energy_stats',
        help="Sum of average monthly consumption from all meters"
    )
    total_installed_capacity = fields.Float(
        string='Total Installed Capacity (kW)',
        compute='_compute_energy_stats',
        help="Total solar capacity from confirmed quotations"
    )
    
    # Customer preferences
    preferred_panel_type = fields.Selection([
        ('mono', 'Monocrystalline'),
        ('poly', 'Polycrystalline'),
        ('thin', 'Thin Film'),
        ('bifacial', 'Bifacial')
    ], string='Preferred Panel Type')
    
    installation_type = fields.Selection([
        ('roof', 'Rooftop'),
        ('ground', 'Ground Mount'),
        ('carport', 'Carport'),
        ('tracker', 'Solar Tracker')
    ], string='Installation Type')
    
    energy_goals = fields.Text(string='Energy Goals & Requirements')

    @api.depends('energy_meter_ids')
    def _compute_energy_meter_count(self):
        for partner in self:
            partner.energy_meter_count = len(partner.energy_meter_ids)

    @api.depends('solar_quotation_ids')
    def _compute_solar_quotation_count(self):
        for partner in self:
            partner.solar_quotation_count = len(partner.solar_quotation_ids)

    @api.depends('energy_meter_ids.average_monthly_consumption', 'solar_quotation_ids.system_power_kw', 'solar_quotation_ids.state')
    def _compute_energy_stats(self):
        for partner in self:
            # Calculate total consumption from all meters
            meters = partner.energy_meter_ids
            if meters:
                partner.total_monthly_consumption = sum(meters.mapped('average_monthly_consumption'))
            else:
                partner.total_monthly_consumption = 0.0
            
            # Calculate total installed capacity from confirmed quotations
            confirmed_quotations = partner.solar_quotation_ids.filtered(lambda q: q.state == 'confirmed')
            partner.total_installed_capacity = sum(confirmed_quotations.mapped('system_power_kw'))

    def action_view_energy_meters(self):
        """Smart button action to view energy meters"""
        self.ensure_one()
        action = self.env.ref('sparks.action_energy_meter').read()[0]
        
        if len(self.energy_meter_ids) > 1:
            action['domain'] = [('partner_id', '=', self.id)]
        elif len(self.energy_meter_ids) == 1:
            action['views'] = [(self.env.ref('sparks.view_energy_meter_form').id, 'form')]
            action['res_id'] = self.energy_meter_ids.id
        else:
            # No meters exist, create new one
            action = {
                'type': 'ir.actions.act_window',
                'name': 'New Energy Meter',
                'res_model': 'sparks.energy.meter',
                'view_mode': 'form',
                'target': 'current',
                'context': {'default_partner_id': self.id}
            }
        
        return action

    def action_view_solar_quotations(self):
        """Smart button action to view solar quotations"""
        self.ensure_one()
        action = self.env.ref('sparks.action_solar_quotation').read()[0]
        
        if len(self.solar_quotation_ids) > 1:
            action['domain'] = [('partner_id', '=', self.id)]
        elif len(self.solar_quotation_ids) == 1:
            action['views'] = [(self.env.ref('sparks.view_solar_quotation_form').id, 'form')]
            action['res_id'] = self.solar_quotation_ids.id
        else:
            # No quotations exist, create new one
            action = {
                'type': 'ir.actions.act_window',
                'name': 'New Solar Quotation',
                'res_model': 'sparks.solar.quotation',
                'view_mode': 'form',
                'target': 'current',
                'context': {'default_partner_id': self.id}
            }
        
        return action

    def create_solar_quotation(self):
        """Create a new solar quotation for this customer"""
        self.ensure_one()
        
        # Check if customer has multiple meters
        meter_count = len(self.energy_meter_ids)
        
        if meter_count == 0:
            # No meters, create simple quotation
            return {
                'type': 'ir.actions.act_window',
                'name': 'New Solar Quotation',
                'res_model': 'sparks.solar.quotation',
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'default_partner_id': self.id,
                    'default_installation_address': self.contact_address,
                }
            }
        elif meter_count == 1:
            # Single meter, create quotation with pre-selected meter
            return {
                'type': 'ir.actions.act_window',
                'name': 'New Solar Quotation',
                'res_model': 'sparks.solar.quotation',
                'view_mode': 'form',
                'target': 'current',
                'context': {
                    'default_partner_id': self.id,
                    'default_meter_ids': [(6, 0, self.energy_meter_ids.ids)],
                    'default_installation_address': self.energy_meter_ids[0].installation_address,
                }
            }
        else:
            # Multiple meters, open wizard for meter selection
            return {
                'type': 'ir.actions.act_window',
                'name': 'Create Multi-Meter Quotation',
                'res_model': 'sparks.multi.meter.quotation.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_partner_id': self.id,
                }
            }

    def action_create_multi_meter_quotation(self):
        """Directly open multi-meter quotation wizard"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Multi-Meter Quotation',
            'res_model': 'sparks.multi.meter.quotation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
            }
        }
