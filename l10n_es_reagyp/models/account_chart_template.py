# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
from odoo import _, models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common_mainland", "account.account")
    def _get_reagyp_account_account(self):
        return self._parse_csv(
            "es_common_mainland", "account.account", module="l10n_es_reagyp"
        )

    @template("es_common_mainland", "account.tax.group")
    def _get_reagyp_account_tax_group(self):
        return self._parse_csv(
            "es_common_mainland", "account.tax.group", module="l10n_es_reagyp"
        )

    @template("es_common_mainland", "account.tax")
    def _get_reagyp_account_tax(self):
        return self._parse_csv(
            "es_common_mainland", "account.tax", module="l10n_es_reagyp"
        )

    @template("es_common_mainland", "account.fiscal.position")
    def _get_reagyp_account_fiscal_position(self):
        return self._parse_csv(
            "es_common_mainland",
            "account.fiscal.position",
            module="l10n_es_reagyp",
        )

    @template("es_common_mainland", "account.journal")
    def _get_reagyp_account_journal(self):
        return {
            "reagyp_sale": {
                "name": _("REAGYP receipts"),
                "type": "sale",
                "code": "REAG",
                "show_on_dashboard": True,
                "sequence": 20,
            },
        }
