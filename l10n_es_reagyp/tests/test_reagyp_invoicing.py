# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install", "l10n_es_reagyp")
class TestReagypInvoicing(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("es")
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env["account.chart.template"].with_company(cls.env.company)
        cls.fp = cls.template.ref("fp_reagyp_sale")
        cls.reagyp_journal = cls.template.ref("reagyp_sale")
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Cooperativa Test",
                "property_account_position_id": cls.fp.id,
            }
        )

    def test_posted_invoice_compensation_posts_to_701090(self):
        """Posted invoice with REAGYP compensation tax books 12% to account 701090."""
        tax = self.template.ref("tax_reagyp_s_12")
        compensation_account = self.template.ref("account_reagyp_compensation")
        revenue_account = self.company_data["default_account_revenue"]
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": "2026-06-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "REAGYP sale",
                            "quantity": 1,
                            "price_unit": 1000.0,
                            "account_id": revenue_account.id,
                            "tax_ids": [(6, 0, tax.ids)],
                        },
                    )
                ],
            }
        )
        move.action_post()
        self.assertEqual(move.state, "posted")
        # The tax repartition line should post 120.0 (12% of 1000) to account 701090.
        compensation_lines = move.line_ids.filtered(
            lambda line: line.account_id == compensation_account
        )
        self.assertTrue(
            compensation_lines,
            "A posted move line for the compensation account (701090) must exist",
        )
        compensation_amount = abs(sum(compensation_lines.mapped("balance")))
        self.assertAlmostEqual(
            compensation_amount,
            120.0,
            places=2,
            msg="Compensation amount must be 12% of 1000 = 120.0",
        )

    def test_retention_is_withheld_on_base_plus_compensation(self):
        """A real olive receipt: the IRPF retention base includes the compensation.

            10 680 kg x 0,65        base           6 942,00
            + 12 % compensation                    +  833,04
            - 2 % IRPF retention                   -  155,50
                                                   ---------
            total to collect                       7 619,54

        The buyer withholds the 2 % on the base PLUS the flat-rate
        compensation (6 942,00 + 833,04 = 7 775,04), not on the base alone.
        That is what `include_base_amount` on the compensation tax encodes:
        it feeds its own amount into the base of the taxes that follow it
        (the retention has a higher sequence). Without it the retention would
        be computed on 6 942,00 and come out as 138,84 — 16,66 EUR short.
        """
        product = self.env["product.product"].create(
            {
                "name": "Aceituna Convencional",
                "taxes_id": [(6, 0, self.template.ref("tax_reagyp_s_ns").ids)],
            }
        )
        move = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                # the partner carries fp_reagyp_sale, which maps the product's
                # "no sujeto" tax to compensation 12 % + IRPF 2 %
                "partner_id": self.partner.id,
                "invoice_date": "2026-06-15",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "quantity": 10680.0,
                            "price_unit": 0.65,
                        },
                    )
                ],
            }
        )
        by_tax = {
            line.tax_line_id: -line.balance
            for line in move.line_ids.filtered("tax_line_id")
        }
        compensation = self.template.ref("tax_reagyp_s_12")
        retention = self.template.ref("tax_reagyp_s_irpf2")
        self.assertAlmostEqual(move.amount_untaxed, 6942.00, places=2)
        self.assertAlmostEqual(by_tax[compensation], 833.04, places=2)
        self.assertAlmostEqual(
            by_tax[retention],
            -155.50,
            places=2,
            msg="IRPF must be 2% of base + compensation (7 775,04), not of the base",
        )
        self.assertAlmostEqual(move.amount_total, 7619.54, places=2)
