from odoo import fields, models, api


class InheritLandedCost(models.Model):
    _inherit = "stock.landed.cost"

    currency_factor = fields.Float(string="Currency Rate", default=1)
    landed_cost_factor = fields.Float(default=1)
    base_pricing_factor = fields.Float(default=1)
    pricing_preference = fields.Selection(
        [
            ("strict", "Strict"),
            ("high", "Prefer higher Price"),
            ("low", "Prefer Lower Price"),
        ]
    )

    def adjust_costing(self):
        for record in self:
            for valuation_line in record.valuation_adjustment_lines:
                valuation_line.product_id.lst_price = valuation_line.new_price
                valuation_line.product_id.standard_price = valuation_line.new_cost

    def revert_costing(self):
        for record in self:
            for valuation_line in record.valuation_adjustment_lines:
                valuation_line.product_id.lst_price = valuation_line.old_price
                valuation_line.product_id.standard_price = valuation_line.former_cost


class InheritStockValuationAjdjustmentLines(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    cost_difference = fields.Float(string="Cost Difference", readonly=True)
    price_difference = fields.Float(string="Price Difference", readonly=True)
    computed_price = fields.Float(string="Computed Price", readonly=True)
    new_price = fields.Float(string="New Price")
    old_price = fields.Float(string="New Price")
    new_cost = fields.Float(string="New Cost")
