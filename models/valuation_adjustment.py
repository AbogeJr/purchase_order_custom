from odoo import fields, models


class InheritValuationAdjustment(models.Model):
    _inherit = "stock.valuation.adjustment.lines"

    cost_difference = fields.Float(
        string="Cost Difference",
        # compute="_compute_cost_difference",
        store=True,
    )
    compute_price = fields.Float(
        string="Compute Price",
        # compute="_compute_compute_price",
        store=True,
        # readonly=False,
    )
    new_price = fields.Float(
        string="New Price",
        # compute="_compute_new_price",
        store=True,
        # readonly=False,
    )
    price_difference = fields.Float(
        string="Price Difference",
        # compute="_compute_price_difference",
        store=True,
        # readonly=False,
    )
