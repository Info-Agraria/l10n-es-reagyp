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
