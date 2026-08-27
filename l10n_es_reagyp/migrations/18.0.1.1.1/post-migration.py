# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def _reagyp_template_data(template):
    """The module's template records, in the shape _load_translations expects."""
    return {
        "account.account": template._get_reagyp_account_account(),
        "account.tax.group": template._get_reagyp_account_tax_group(),
        "account.tax": template._get_reagyp_account_tax(),
        "account.fiscal.position": template._get_reagyp_account_fiscal_position(),
        "account.journal": template._get_reagyp_account_journal(),
    }


def migrate(cr, version):
    """Translate the records earlier migrations created untranslated.

    `_load_data` strips the `name@es` columns off the values it is given, and
    the step that turns them into translations, `_load_translations`, only runs
    as part of a full chart load. A migration that instantiates a record on its
    own therefore leaves it with its English name in every language: on a
    database upgraded to 18.0.1.1.0, the REAGYP purchase position shows up as
    "REAGYP - purchase (farmer)" in a Spanish interface, while the sale one --
    created back when the module was installed -- reads correctly.

    Feeding the module's own template data back through `_load_translations`
    fills in what is missing. It saves with `overwrite=False`, so a name an
    accountant changed by hand stays changed.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    repaired = 0
    for company in env["res.company"].search([]):
        template = env["account.chart.template"].with_company(company)
        if not template.ref("fp_reagyp_sale", raise_if_not_found=False):
            continue
        template._load_translations(
            companies=company, template_data=_reagyp_template_data(template)
        )
        repaired += 1
    if repaired:
        _logger.info(
            "l10n_es_reagyp: reloaded the translations of the REAGYP template "
            "records on %s company(ies)",
            repaired,
        )
