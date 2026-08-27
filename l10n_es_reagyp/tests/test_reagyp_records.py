# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install", "l10n_es_reagyp")
class TestReagypRecords(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("es")
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env["account.chart.template"].with_company(cls.env.company)

    def _ref(self, xmlid):
        return self.template.ref(xmlid, raise_if_not_found=False)

    def test_income_account_exists(self):
        acc = self._ref("account_reagyp_compensation")
        self.assertTrue(acc, "Compensation income account not instantiated")
        self.assertEqual(acc.account_type, "income")
        self.assertTrue(acc.code.startswith("701090"))

    def test_tax_group_exists(self):
        grp = self._ref("tax_group_reagyp")
        self.assertTrue(grp, "tax_group_reagyp not instantiated")
        self.assertNotIn("iva", grp.name.lower())

    def test_tax_group_orders_before_retention(self):
        # The tax-group sequence orders the blocks in the invoice tax-totals
        # summary. The compensation must render BEFORE the IRPF retention
        # (base -> compensation -> retention), so its group needs a lower
        # sequence than the core retention group (which ships at 10).
        # Presentation only: tax *computation* order is set by the taxes' own
        # sequence (compensation 1, retention 1000), not by this.
        grp = self._ref("tax_group_reagyp")
        retention = self._ref("account_tax_template_s_irpf2")
        self.assertTrue(retention, "core retention tax s_irpf2 not found")
        self.assertLess(
            grp.sequence,
            retention.tax_group_id.sequence,
            "REAGYP compensation must sort before the IRPF retention",
        )

    def test_compensation_12_tax(self):
        tax = self._ref("tax_reagyp_s_12")
        self.assertTrue(tax, "tax_reagyp_s_12 not instantiated")
        self.assertEqual(tax.type_tax_use, "sale")
        self.assertEqual(tax.amount, 12.0)
        self.assertEqual(tax.l10n_es_type, "ignore")
        self.assertEqual(tax.tax_group_id, self._ref("tax_group_reagyp"))
        # Tax repartition routes to the dedicated income account
        tax_rep = tax.invoice_repartition_line_ids.filtered(
            lambda r: r.repartition_type == "tax"
        )
        self.assertEqual(tax_rep.account_id, self._ref("account_reagyp_compensation"))

    def test_compensation_105_tax(self):
        tax = self._ref("tax_reagyp_s_105")
        self.assertTrue(tax)
        self.assertEqual(tax.type_tax_use, "sale")
        self.assertEqual(tax.amount, 10.5)
        self.assertEqual(tax.l10n_es_type, "ignore")

    def test_no_sujeto_source_tax(self):
        tax = self._ref("tax_reagyp_s_ns")
        self.assertTrue(tax)
        self.assertEqual(tax.type_tax_use, "sale")
        self.assertEqual(tax.amount, 0.0)

    def test_sale_fiscal_position_maps_the_sale_half(self):
        fp = self._ref("fp_reagyp_sale")
        self.assertTrue(fp, "fp_reagyp_sale not instantiated")
        source = self._ref("tax_reagyp_s_ns")
        dests = fp.tax_ids.filtered(lambda m: m.tax_src_id == source).mapped(
            "tax_dest_id"
        )
        self.assertIn(self._ref("tax_reagyp_s_12"), dests)
        self.assertIn(self._ref("account_tax_template_s_irpf2"), dests)

    def test_sale_fiscal_position_no_longer_carries_purchase_mappings(self):
        # Which taxes a sale carries depends on the buyer's regime; whether
        # input VAT is deductible depends only on the farmer. Tying the second
        # to the first meant it reached the customers and missed the suppliers.
        fp = self._ref("fp_reagyp_sale")
        purchase_sources = fp.tax_ids.mapped("tax_src_id").filtered(
            lambda tax: tax.type_tax_use == "purchase"
        )
        self.assertFalse(
            purchase_sources,
            "The sale position must not map purchase taxes any more",
        )

    def test_purchase_fiscal_position_makes_input_vat_non_deductible(self):
        fp = self._ref("fp_reagyp_purchase")
        self.assertTrue(fp, "fp_reagyp_purchase not instantiated")
        for source_xmlid, dest_xmlid in (
            ("account_tax_template_p_iva21_bc", "account_tax_template_p_iva0_nd"),
            ("account_tax_template_p_iva10_bc", "account_tax_template_p_iva10_nd"),
            ("account_tax_template_p_iva4_bc", "account_tax_template_p_iva4_nd"),
        ):
            source = self._ref(source_xmlid)
            dests = fp.tax_ids.filtered(
                lambda m, source=source: m.tax_src_id == source
            ).mapped("tax_dest_id")
            self.assertIn(self._ref(dest_xmlid), dests, source_xmlid)

    def test_purchase_fiscal_position_is_assigned_by_hand(self):
        # Same as every regime position core ships (fp_reagyp_a, fp_irpf*):
        # no auto_apply, the bookkeeper decides which partners carry it.
        self.assertFalse(self._ref("fp_reagyp_purchase").auto_apply)
        self.assertFalse(self._ref("fp_reagyp_sale").auto_apply)

    def test_reagyp_journal_exists(self):
        journal = self._ref("reagyp_sale")
        self.assertTrue(journal, "reagyp_sale journal not instantiated")
        self.assertEqual(journal.type, "sale")
        self.assertEqual(journal.code, "REAG")
