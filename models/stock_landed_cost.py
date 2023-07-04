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

    def compute_landed_cost(self):
        adjustment_lines = self.valuation_adjustment_lines

        for line in adjustment_lines:
            line.new_price = line.new_price * self.base_pricing_factor
            line.new_cost = line.former_cost * self.landed_cost_factor
            line.computed_price = line.computed_price * self.base_pricing_factor
            print("LINES")
            print(line)
            print(line.new_price)
            print(line.new_cost)

        return super(InheritLandedCost, self).compute_landed_cost()

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
    price_difference = fields.Float(
        string="Price Difference", compute="_compute_price_difference", store=True
    )
    computed_price = fields.Float(string="Computed Price", readonly=True)
    new_price = fields.Float(string="New Price")
    old_price = fields.Float(string="Old Price")
    new_cost = fields.Float(string="New Cost")

    @api.depends("former_cost", "final_cost")
    def _compute_price_difference(self):
        for record in self:
            record.cost_difference = record.final_cost - record.former_cost
