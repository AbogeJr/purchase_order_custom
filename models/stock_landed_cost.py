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
        pass

    def revert_costing(self):
        pass


class InheritStockValuationAjdjustmentLines(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    cost_difference = fields.Float(string="Cost Difference", readonly=True)
    price_difference = fields.Float(string="Price Difference", readonly=True)
    computed_price = fields.Float(string="Computed Price", readonly=True)
    new_price = fields.Float(string="New Price")
