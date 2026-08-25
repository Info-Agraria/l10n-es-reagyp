# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
from odoo import Command, _, models

from odoo.addons.account.models.chart_template import TAX_TAG_DELIMITER, template


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
        tax_data = self._parse_csv(
            "es_common_mainland", "account.tax", module="l10n_es_reagyp"
        )
        self._deref_reagyp_tax_tags(tax_data)
        return tax_data

    def _deref_reagyp_tax_tags(self, tax_data):
        """Turn the tax report tag codes of our CSV into tag ids.

        Core does this in `_deref_account_tags`, but that helper finds the
        country by looking the chart template code up in the template mapping,
        and `es_common_mainland` is not in it: only the selectable charts built
        on top of it are. Our template functions are registered against the
        parent and are called without the code of the chart actually being
        loaded, so resolve against Spain directly instead.
        """
        mapper = self._get_tag_mapper(self.env.ref("base.es").id)
        for tax_values in tax_data.values():
            for element in tax_values.get("repartition_line_ids", []):
                values = element[2] if len(element) == 3 else None
                if isinstance(values, dict) and isinstance(values.get("tag_ids"), str):
                    values["tag_ids"] = [
                        Command.set(mapper(*values["tag_ids"].split(TAX_TAG_DELIMITER)))
                    ]

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
