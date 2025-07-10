from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ConsumptionLine(models.Model):
    _name = 'sparks.consumption.line'
    _description = 'Monthly Energy Consumption Line'
    _order = 'month'

    quotation_id = fields.Many2one(
        'sparks.solar.quotation', 
        string='Quotation', 
        required=True,
        ondelete='cascade'
    )
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Month', required=True)
    
    energy_kwh = fields.Float(string='Energy Consumption (kWh)', required=True)
    energy_cost = fields.Monetary(
        string='Energy Cost',
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        related='quotation_id.currency_id',
        store=True
    )

    @api.constrains('month', 'quotation_id')
    def _check_unique_month(self):
        for record in self:
            existing = self.search([
                ('quotation_id', '=', record.quotation_id.id),
                ('month', '=', record.month),
                ('id', '!=', record.id)
            ])
            if existing:
                month_name = dict(self._fields['month'].selection)[record.month]
                raise ValidationError(
                    _("Month %s is already defined for this quotation.") % month_name
                )