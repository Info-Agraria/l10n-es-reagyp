# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

PURCHASE_XMLID = "fp_reagyp_purchase"
# The purchase half that moves out of fp_reagyp_sale, by source tax.
MOVED_SOURCES = (
    "account_tax_template_p_iva21_bc",
    "account_tax_template_p_iva10_bc",
    "account_tax_template_p_iva4_bc",
)


def _create_purchase_position(template, company):
    """Instantiate fp_reagyp_purchase, which only exists from 18.0.1.1.0 on.

    Chart-template records are created when the module is installed, never
    when it is upgraded, so an existing database has no such position yet.
    Only this record is loaded: reloading the whole template would reset
    fields a deployment may have edited by hand, the position names included.

    Translations need loading by hand as well. `_load_data` strips the `name@es`
    columns off the values, and the step that turns them into translations only
    runs from the full chart load, so a record created here would keep its
    English name in every language.
    """
    if template.ref(PURCHASE_XMLID, raise_if_not_found=False):
        return False
    values = template._get_reagyp_account_fiscal_position().get(PURCHASE_XMLID)
    if not values:
        return False
    data = {"account.fiscal.position": {PURCHASE_XMLID: values}}
    template._load_data(data)
    template._load_translations(companies=company, template_data=data)
    return True


def _strip_purchase_half(template):
    """Drop the purchase mappings from the sale position.

    They were only ever reachable through a partner carrying the sale
    position, which is a customer. Non-deductible input VAT is a property of
    the farmer, not of who they sell to, so it now lives in its own position.
    """
    position = template.ref("fp_reagyp_sale", raise_if_not_found=False)
    if not position:
        return 0
    sources = [template.ref(xmlid, raise_if_not_found=False) for xmlid in MOVED_SOURCES]
    sources = [tax.id for tax in sources if tax]
    stale = position.tax_ids.filtered(lambda line: line.tax_src_id.id in sources)
    count = len(stale)
    stale.unlink()
    return count


def migrate(cr, version):
    """Split fp_reagyp_sale into a sale position and a purchase position.

    The two halves answer different questions. Which taxes a *sale* carries
    depends on whether the buyer is himself under REAGYP; whether input VAT is
    deductible depends only on the farmer. Keeping both on one position meant
    the non-deductible mapping reached exactly the partners it had no business
    being tied to -- the customers -- and missed every other supplier.

    Nothing is reassigned automatically: which partners should carry the new
    position is a bookkeeping decision, so the partners currently holding the
    sale position are logged for review instead.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    created = moved = 0
    for company in env["res.company"].search([]):
        template = env["account.chart.template"].with_company(company)
        if _create_purchase_position(template, company):
            created += 1
        moved += _strip_purchase_half(template)

        position = template.ref("fp_reagyp_sale", raise_if_not_found=False)
        if not position:
            continue
        partners = (
            env["res.partner"]
            .with_company(company)
            .search([("property_account_position_id", "=", position.id)])
        )
        if partners:
            _logger.warning(
                "l10n_es_reagyp: %s carries the REAGYP sale position on %s "
                "partner(s): %s. Input VAT is no longer made non-deductible "
                "through it -- assign '%s' to the suppliers that need it.",
                company.name,
                len(partners),
                ", ".join(partners.mapped("display_name")[:10]),
                PURCHASE_XMLID,
            )
    _logger.info(
        "l10n_es_reagyp: created the purchase fiscal position on %s company(ies) "
        "and moved %s mapping(s) out of the sale one",
        created,
        moved,
    )
