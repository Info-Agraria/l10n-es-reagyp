# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

_logger = logging.getLogger(__name__)


def _l10n_es_reagyp_post_init_hook(env):
    # Companies that already had a MAINLAND Spanish chart loaded before this
    # module was installed don't get our @template data automatically; create
    # it for them. Canary charts are out of scope (no REAGYP there).
    # Canary charts are excluded: no REAGYP in the Canary Islands regime.
    companies = env["res.company"].search(
        [
            ("chart_template", "=like", "es_%"),
            ("chart_template", "not like", "es_canary%"),
            ("parent_id", "=", False),
        ]
    )
    for company in companies:
        _logger.info(
            "l10n_es_reagyp: backfilling REAGYP data for company %s", company.name
        )
        Template = env["account.chart.template"].with_company(company)
        data = {
            "account.account": Template._get_reagyp_account_account(),
            "account.tax.group": Template._get_reagyp_account_tax_group(),
            "account.tax": Template._get_reagyp_account_tax(),
            "account.fiscal.position": Template._get_reagyp_account_fiscal_position(),
            "account.journal": Template._get_reagyp_account_journal(),
        }
        Template._pre_reload_data(company, {}, data)
        Template._load_data(data)
