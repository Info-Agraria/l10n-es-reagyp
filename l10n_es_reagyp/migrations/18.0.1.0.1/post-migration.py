# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

COMPENSATION_TEMPLATES = ("tax_reagyp_s_12", "tax_reagyp_s_105")


def migrate(cr, version):
    """Backfill `include_base_amount` on already-instantiated compensation taxes.

    The IRPF retention is withheld on base + compensation, which is what
    `include_base_amount` on the compensation tax encodes. Fixing the CSV only
    helps companies that load the chart *after* this release: chart-template
    records are instantiated per company, and `_l10n_es_reagyp_post_init_hook`
    only creates the ones a company is missing — it never rewrites existing
    rows. So companies that already loaded a Spanish chart keep the old tax and
    would go on under-withholding (2 % of the base instead of 2 % of base +
    compensation). Update those taxes in place.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    Template = env["account.chart.template"]
    fixed = 0
    for company in env["res.company"].search([]):
        template = Template.with_company(company)
        for xmlid in COMPENSATION_TEMPLATES:
            tax = template.ref(xmlid, raise_if_not_found=False)
            if tax and not tax.include_base_amount:
                tax.include_base_amount = True
                fixed += 1
    if fixed:
        _logger.info(
            "l10n_es_reagyp: set include_base_amount on %s REAGYP compensation "
            "tax(es) so the IRPF retention is withheld on base + compensation",
            fixed,
        )
