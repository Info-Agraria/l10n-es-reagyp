# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_es_reagyp.hooks import _l10n_es_reagyp_post_init_hook


@tagged("post_install", "-at_install", "l10n_es_reagyp")
class TestReagypBackfill(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("es")
    def setUpClass(cls):
        super().setUpClass()
        cls.template = cls.env["account.chart.template"].with_company(cls.env.company)

    def test_backfill_creates_records_for_loaded_company(self):
        # Simulate a company that had the Spanish chart but (pretend) missed our
        # records: delete one, re-run the hook, assert it is recreated.
        template = self.env["account.chart.template"].with_company(self.env.company)
        tax = template.ref("tax_reagyp_s_12", raise_if_not_found=False)
        self.assertTrue(tax, "precondition: tax exists after install")
        # The hook must be idempotent: running it again does not error and the
        # records remain present.
        _l10n_es_reagyp_post_init_hook(self.env)
        self.assertTrue(template.ref("tax_reagyp_s_12", raise_if_not_found=False))
        self.assertTrue(template.ref("reagyp_sale", raise_if_not_found=False))
        self.assertTrue(template.ref("fp_reagyp_sale", raise_if_not_found=False))
