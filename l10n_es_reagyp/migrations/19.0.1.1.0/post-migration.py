# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

from odoo import Command, api

_logger = logging.getLogger(__name__)

PURCHASE_POSITION = "fp_reagyp_purchase"
# Each wrapper and the core tax it replaces, added in 19.0.1.1.0.
WRAPPERS = {
    "tax_reagyp_p_iva21_nd": "account_tax_template_p_iva21_bc",
    "tax_reagyp_p_iva10_nd": "account_tax_template_p_iva10_bc",
    "tax_reagyp_p_iva4_nd": "account_tax_template_p_iva4_bc",
}
CORE_NON_DEDUCTIBLE = (
    "account_tax_template_p_iva0_nd",
    "account_tax_template_p_iva10_nd",
    "account_tax_template_p_iva4_nd",
)
POSITIONS = ("fp_reagyp_sale", PURCHASE_POSITION)


def _create_records(template, company):
    """Instantiate the purchase position and its three wrapper taxes.

    Chart-template records are created when the module is installed, never
    when it is upgraded. Only the new records are loaded: reloading the whole
    template would reset fields a deployment may have edited by hand.
    """
    created = 0
    data = {}
    if not template.ref(PURCHASE_POSITION, raise_if_not_found=False):
        values = template._get_reagyp_account_fiscal_position().get(PURCHASE_POSITION)
        if values:
            data["account.fiscal.position"] = {PURCHASE_POSITION: values}
            created += 1
    taxes = template._get_reagyp_account_tax()
    missing = {
        xmlid: taxes[xmlid]
        for xmlid in WRAPPERS
        if xmlid in taxes and not template.ref(xmlid, raise_if_not_found=False)
    }
    if missing:
        data["account.tax"] = missing
        created += len(missing)
    if data:
        template._load_data(data)
        # `_load_data` strips the `name@es` columns, and the step that turns
        # them into translations only runs from the full chart load, so these
        # records would otherwise keep their English name in every language.
        template._load_translations(companies=company, template_data=data)
    return created


def _release_core_non_deductible(template):
    """Take the core non-deductible taxes back out of our fiscal positions.

    A database coming from 18.0 arrives with the old mapping converted onto
    those core taxes: OpenUpgrade turns every `account.fiscal.position.tax`
    row into a membership plus a replacement, so `p_iva0_nd` ends up attached
    to one of our positions and claiming `p_iva21_bc` as an original.

    We cannot leave it that way. In 19.0 a destination tax carries the same
    substitution in *every* position it belongs to, and those core taxes also
    belong to the domestic position -- so the replacement would spread there
    and make ordinary domestic purchases non-deductible for the whole company.
    The wrapper taxes added in 19.0.1.1.0 exist precisely to keep the
    substitution inside our own position.
    """
    released = 0
    positions = [
        position
        for position in (
            template.ref(xmlid, raise_if_not_found=False) for xmlid in POSITIONS
        )
        if position
    ]
    for xmlid in CORE_NON_DEDUCTIBLE:
        destination = template.ref(xmlid, raise_if_not_found=False)
        if not destination:
            continue
        for position in positions:
            if destination in position.tax_ids:
                position.tax_ids = [Command.unlink(destination.id)]
                released += 1
        for source_xmlid in WRAPPERS.values():
            source = template.ref(source_xmlid, raise_if_not_found=False)
            if source and source in destination.original_tax_ids:
                destination.original_tax_ids = [Command.unlink(source.id)]
    return released


def migrate(cr, version):
    """Give the purchase half its own fiscal position, as 18.0.1.1.0 did.

    Nothing here touches accounting entries: the taxes a posted bill already
    carries still exist and keep their repartition. Only the mapping a *new*
    bill goes through changes.
    """
    env = api.Environment(cr, api.SUPERUSER_ID, {})
    created = released = 0
    for company in env["res.company"].search([]):
        template = env["account.chart.template"].with_company(company)
        if not template.ref("fp_reagyp_sale", raise_if_not_found=False):
            continue
        created += _create_records(template, company)
        released += _release_core_non_deductible(template)
    if created or released:
        _logger.info(
            "l10n_es_reagyp: created %s record(s) for the REAGYP purchase "
            "position and released %s core non-deductible tax(es) that the "
            "18.0 mapping had left attached to it",
            created,
            released,
        )
