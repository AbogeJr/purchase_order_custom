from odoo import fields, models


class PurchaseLandedCost(models.Model):
    _name = "purchase.landed.cost"
    _description = "Relation for Purchase Landed Costs"

    vendor_id = fields.Many2one("res.partner", string="Vendor")
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Integer()
    price = fields.Float()
    taxes = fields.Many2many("account.tax")
    purchase_id = fields.Many2one("purchase.order")
    vendor_bill_id = fields.Many2one(
        "account.move",
        "Vendor Bill",
        copy=False,
        domain=[("move_type", "=", "in_invoice")],
    )
    picking_ids = fields.Many2many("stock.picking")

    def create_landed_cost(self):
        self.ensure_one()
        if not self.vendor_bill_id:
            self.vendor_bill_id = self.create_vendor_bill().id
        landed_costs = self.env["stock.landed.cost"].create(
            [
                {
                    "account_journal_id": self.expenses_journal.id,
                    "cost_lines": [
                        (
                            0,
                            0,
                            {
                                "name": "equal split",
                                "split_method": "equal",
                                "price_unit": self.price_unit,
                                "product_id": self.landed_cost.id,
                            },
                        )
                    ],
                }
            ]
        )
        landed_costs.compute_landed_cost()
        landed_costs.button_validate()

    def create_vendor_bill(self):
        journal = self.env["account.invoice"]._default_journal().id
        supplier_line = {
            "product_id": self.product_id.id,
            "name": self.product_id.name,
            "type": "in_invoice",
            "quantity": 1,
            "account_id": journal,
            "price_unit": self.purchase_id.price_unit,
        }
        record_line = {
            "partner_id": self.user_id.id,
            "invoice_line_ids": [(0, 0, supplier_line)],
        }
        record = self.env["account.invoice"].create(record_line)
        self.env["account.invoice"].action_invoice_open()
        return record
