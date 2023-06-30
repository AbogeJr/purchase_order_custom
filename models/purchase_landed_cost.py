from odoo import fields, models, api


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
        readonly=True,
    )
    state = fields.Selection(
        [("draft", "Draft"), ("billed", "Billed"), ("done", "Done")],
        default="draft",
    )

    @api.onchange("state")
    def _onchange_state(self):
        if self.state == "billed":
            self.create_vendor_bill()
        # elif self.state == "done":
        #     self.create_landed_cost()

    def create_vendor_bill(self):
        AccountMove = self.env["account.move"]
        AccountMoveLine = self.env["account.move.line"]
        for record in self:
            # Create an empty invoice
            invoice = AccountMove.create(
                {
                    "move_type": "in_invoice",
                    "partner_id": record.vendor_id.id,  # Set the customer/partner for the invoice
                    "invoice_date": fields.Date.today(),  # Set the invoice date
                }
            )
            # Calculate invoice lines
            quantity = record.quantity
            price = record.price
            taxes = record.taxes

            # Create the first invoice line
            line1 = AccountMoveLine.create(
                {
                    "name": "Product Info",  # Name of the invoice line
                    "quantity": 1,  # Quantity of the item
                    "move_id": invoice.id,  # Assign the invoice to the line
                }
            )

            # Create the second invoice line
            line2 = AccountMoveLine.create(
                {
                    "name": "Administrative Fees",  # Name of the invoice line
                    "quantity": 1,  # Quantity of the item
                    "move_id": invoice.id,  # Assign the invoice to the line
                }
            )

            # Set the invoice lines on the invoice
            invoice.write({"invoice_line_ids": [(4, line1.id), (4, line2.id)]})

            # Set the created invoice on the property
            record.vendor_bill_id = invoice.id

    # def create_landed_cost(self):
    #     self.ensure_one()
    #     if not self.vendor_bill_id:
    #         self.vendor_bill_id = self.create_vendor_bill().id
    #     landed_costs = self.env["stock.landed.cost"].create(
    #         [
    #             {
    #                 "account_journal_id": self.expenses_journal.id,
    #                 "cost_lines": [
    #                     (
    #                         0,
    #                         0,
    #                         {
    #                             "name": "equal split",
    #                             "split_method": "equal",
    #                             "price_unit": self.price_unit,
    #                             "product_id": self.landed_cost.id,
    #                         },
    #                     )
    #                 ],
    #             }
    #         ]
    #     )
    #     landed_costs.compute_landed_cost()
    #     landed_costs.button_validate()
