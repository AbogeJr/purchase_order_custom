from odoo import fields, models, api


class PurchaseLandedCost(models.Model):
    _name = "purchase.landed.cost"
    _description = "Relation for Purchase Landed Costs"

    vendor_id = fields.Many2one("res.partner", string="Vendor")
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Integer()
    price = fields.Float()
    # taxes = fields.Many2many("account.tax")
    taxes = fields.Many2many(
        "account.tax",
        "purchase_landed_cost",
        "vendor_bill_id",
        "vendor_id",
        string="Taxes",
    )
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
                    "ref": record.purchase_id.name,  # Set the invoice reference
                }
            )
            # Calculate invoice lines
            quantity = record.quantity
            price = record.price
            taxes = record.taxes
            product = record.product_id
            purchase = record.purchase_id

            # Create the first invoice line
            line1 = AccountMoveLine.create(
                {
                    "name": product.name,
                    "product_id": product.id,
                    "tax_ids": [(6, 0, taxes.ids)],
                    "price_unit": price,
                    "is_landed_costs_line": True,
                    "purchase_order_id": purchase.id,
                    "quantity": quantity,
                    "move_id": invoice.id,
                }
            )

            # Set the invoice lines on the invoice
            invoice.write(
                {
                    "invoice_line_ids": [
                        (4, line1.id),
                    ]
                }
            )

            # Post the invoice
            invoice.state = "posted"

            # Set the created invoice on the property
            record.vendor_bill_id = invoice.id

    def create_landed_cost(self):
        LandedCost = self.env["stock.landed.cost"]
        for record in self:
            # Create an empty landed cost
            if record.vendor_bill_id:
                landed_cost = LandedCost.create(
                    {
                        "vendor_bill_id": record.vendor_bill_id.id,
                        "account_journal_id": record.purchase_id.journal_id.id,
                        "cost_lines": [
                            (
                                0,
                                0,
                                {
                                    "product_id": record.product_id.id,
                                    "name": record.product_id.name,
                                    "split_method": "by_quantity",
                                    "price_unit": record.price,
                                },
                            )
                        ],
                    }
                )
                # Compute the landed cost
                landed_cost.compute_landed_cost()
