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

    def test_fiscal_position_maps_no_sujeto_to_the_group_tax(self):
        # 19.0 removed account.fiscal.position.tax: the mapping now lives on
        # the destination tax, which declares the positions it applies in and
        # the taxes it replaces. The position derives its tax_map from that.
        fp = self._ref("fp_reagyp_sale")
        self.assertTrue(fp, "fp_reagyp_sale not instantiated")
        source = self._ref("tax_reagyp_s_ns")
        bundle = self._ref("tax_reagyp_s_12_irpf2")
        self.assertTrue(bundle, "tax_reagyp_s_12_irpf2 not instantiated")
        self.assertEqual(bundle.amount_type, "group")
        self.assertEqual(bundle.fiscal_position_ids, fp)
        self.assertEqual(bundle.original_tax_ids, source)
        self.assertEqual(
            fp.map_tax(source),
            bundle,
            "The no-sujeto sale tax must resolve to the REAGYP group tax",
        )

    def test_group_tax_bundles_compensation_and_the_core_retention(self):
        # The group exists so that the retention can be the core tax instead of
        # a copy of it: a destination tax carries the same substitution in
        # every position it belongs to, so hooking the core retention directly
        # onto our position would drag its own originals in with it.
        bundle = self._ref("tax_reagyp_s_12_irpf2")
        compensation = self._ref("tax_reagyp_s_12")
        core_retention = self._ref("account_tax_template_s_irpf2")
        self.assertEqual(bundle.children_tax_ids, compensation + core_retention)
        self.assertTrue(
            compensation.include_base_amount,
            "The compensation must feed the base of the retention that follows",
        )
        self.assertFalse(
            core_retention.fiscal_position_ids & bundle.fiscal_position_ids,
            "The core retention must stay out of the REAGYP fiscal position",
        )

    def test_fiscal_position_leaves_core_vat_sales_alone(self):
        # The reason the module ships its own retention instead of reusing the
        # core one: a destination tax carries the same substitution in every
        # position it belongs to, and the core 2% retention lists every sale
        # VAT tax among its original_tax_ids. Borrowing it would strip the VAT
        # off any ordinary sale made to a partner carrying this position.
        fp = self._ref("fp_reagyp_sale")
        iva21 = self._ref("account_tax_template_s_iva21b")
        self.assertTrue(iva21, "core sale VAT 21% not found")
        self.assertEqual(
            fp.map_tax(iva21),
            iva21,
            "An ordinary 21% sale must pass through the REAGYP position untouched",
        )

    def test_reagyp_journal_exists(self):
        journal = self._ref("reagyp_sale")
        self.assertTrue(journal, "reagyp_sale journal not instantiated")
        self.assertEqual(journal.type, "sale")
        self.assertEqual(journal.code, "REAG")
