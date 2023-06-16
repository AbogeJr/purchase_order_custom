from odoo import models


class PartnerXlsx(models.AbstractModel):
    _name = "report.purchase_order_autolamps.purchase_order_xlsx"
    _inherit = "report.report_xlsx.abstract"

    def generate_xlsx_report(self, workbook, data, po):
        sheet = workbook.add_worksheet()
        header = workbook.add_format(
            {"font_size": 16, "align": "center", "bg_color": "#D3D3D3", "bold": True}
        )
        bold = workbook.add_format({"font_size": 10, "bold": True})
        normal = workbook.add_format({"font_size": 10})
        currency = workbook.add_format({"font_size": 10, "num_format": "#,##0.00"})
        currency_bold = workbook.add_format(
            {"font_size": 10, "num_format": "#,##0.00", "bold": True}
        )

        sheet.merge_range("B1:K1", "Purchase Order: %s" % po.name, header)
        sheet.merge_range("B2:C2", "Supplier:", bold)
        sheet.merge_range("D2:E2", po.partner_id.name, normal)
        sheet.merge_range("B3:C3", "Order Date:", bold)
        sheet.merge_range("D3:E3", po.date_order.date(), normal)
        sheet.merge_range("B4:C4", "Currency:", bold)
        sheet.merge_range("D4:E4", po.currency_id.name, normal)

        # Adjust height: top row
        sheet.set_row(0, 20)

        # Adjust column sizes
        sheet.set_column(0, 0, 5)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 5)
        sheet.set_column(4, 4, 10)
        sheet.set_column(6, 6, 12)

        # Table Headers
        row = 4
        sheet.write(row, 0, "No.", bold)
        sheet.write(row, 1, "Product Sequence", bold)
        sheet.write(row, 2, "Automan ID", bold)
        sheet.write(row, 3, "Supplier Product Code", bold)
        sheet.write(row, 4, "Product Code", bold)
        sheet.write(row, 5, "Product Description", bold)
        sheet.write(row, 6, "Qty", bold)
        sheet.write(row, 7, "FoB", bold)
        sheet.write(row, 8, "Units", bold)
        sheet.write(row, 9, "Measurements", bold)
        sheet.write(row, 10, "Sub-total", bold)

        # Table data
        index = 1
        row += 1
        for line in po.order_line:
            product_code = line.product_id.default_code
            supplier_code = ""
            supplier = line.product_id.seller_ids.filtered(
                lambda s: s.partner_id.id == po.partner_id.id
            )
            if supplier:
                supplier_code = supplier[0].product_code
            sheet.write(row, 0, index, normal)
            sheet.write(row, 1, line.product_id.sequence, normal)
            sheet.write(row, 2, line.product_id.id or "", normal)
            sheet.write(row, 3, supplier_code or "N\A", normal)
            sheet.write(row, 4, product_code or "N\A", normal)
            sheet.write(row, 5, line.product_id.name, normal)
            sheet.write(row, 6, line.product_qty, normal)
            sheet.write(row, 7, line.price_unit, currency)
            sheet.write(row, 8, line.product_uom.name, normal)
            sheet.write(row, 9, line.product_uom.name or "", normal)
            sheet.write(row, 10, line.price_subtotal, currency)

            row += 1
            index += 1

        # write sub-totals
        row += 1
        sheet.write(row, 9, "Taxes:", bold)
        sheet.write(row, 10, po.amount_tax, currency_bold)
        row += 1
        sheet.write(row, 9, "Totals:", bold)
        sheet.write(row, 10, po.amount_total, currency_bold)
