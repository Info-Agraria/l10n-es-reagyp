# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

from odoo import Command, api

_logger = logging.getLogger(__name__)

BUNDLE_XMLID = "tax_reagyp_s_12_irpf2"

# The 18.0 fiscal position mapped the no-sujeto sale tax onto two destinations.
# 19.0 routes it through a single group tax instead, so both of the old
# destinations have to let go of the source.
SUPERSEDED_DESTINATIONS = ("tax_reagyp_s_12", "account_tax_template_s_irpf2")


def _create_bundle_tax(env):
    """Instantiate the 19.0 group tax on companies that already load the chart.

    Chart-template records are only created when the module is installed, never
    when it is upgraded, so the group tax does not exist yet here.

    Only the group is loaded, deliberately. The module ships an idempotent
    backfill hook that would create it too, but it reloads every template
    record, and `_load_data` resets fields a deployment may well have edited by
    hand -- the fiscal position name among them. A migration has no business
    renaming things an accountant renamed on purpose.
    """
    created = 0
    for company in env["res.company"].search([]):
        template = env["account.chart.template"].with_company(company)
        if template.ref(BUNDLE_XMLID, raise_if_not_found=False):
            continue
        # Only companies that already carry the rest of our data: the ones that
        # never loaded a mainland Spanish chart have nothing to migrate.
        if not template.ref("fp_reagyp_sale", raise_if_not_found=False):
            continue
        bundle = template._get_reagyp_account_tax().get(BUNDLE_XMLID)
        if not bundle:
            continue
        data = {"account.tax": {BUNDLE_XMLID: bundle}}
        template._load_data(data)
        # `_load_data` strips the `name@es` columns, and the step that turns
        # them into translations only runs from the full chart load, so the
        # record would otherwise keep its English name in every language.
        template._load_translations(companies=company, template_data=data)
        created += 1
    if created:
        _logger.info(
            "l10n_es_reagyp: created the %s group tax on %s company(ies)",
            BUNDLE_XMLID,
            created,
        )


def _drop_superseded_mappings(env):
    """Leave the group tax as the only destination of the no-sujeto sale tax.

    OpenUpgrade converts the whole `account_fiscal_position_tax` table into the
    19.0 shape, so an upgraded database arrives with the two 18.0 destinations
    -- our compensation and the *core* 2% retention -- both hooked onto
    `fp_reagyp_sale` and both claiming `tax_reagyp_s_ns` as an original.

    19.0 maps the source to `tax_reagyp_s_12_irpf2`, a group tax that has those
    same two as children. Left alone, the position would resolve the source to
    the group *and* to its children, and the core retention would additionally
    drag its own originals -- every sale VAT tax -- into this position, so an
    ordinary 21% sale to a REAGYP customer would come out as a 2% withholding
    with no VAT at all.
    """
    Template = env["account.chart.template"]
    cleaned = 0
    for company in env["res.company"].search([]):
        template = Template.with_company(company)
        position = template.ref("fp_reagyp_sale", raise_if_not_found=False)
        source = template.ref("tax_reagyp_s_ns", raise_if_not_found=False)
        if not (position and source):
            continue
        for xmlid in SUPERSEDED_DESTINATIONS:
            destination = template.ref(xmlid, raise_if_not_found=False)
            if not destination:
                continue
            if destination in position.tax_ids:
                position.tax_ids = [Command.unlink(destination.id)]
                cleaned += 1
            # The source only ever reached these taxes through our own 18.0
            # mapping, so dropping it leaves fp_irpf2 and every other position
            # the core retention serves untouched.
            if source in destination.original_tax_ids:
                destination.original_tax_ids = [Command.unlink(source.id)]
    if cleaned:
        _logger.info(
            "l10n_es_reagyp: replaced %s pre-19.0 mapping(s) on the REAGYP sale "
            "fiscal position with the tax_reagyp_s_12_irpf2 group tax",
            cleaned,
        )


def migrate(cr, version):
    """Bring an upgraded database to the same shape as a fresh 19.0 install.

    Nothing here touches accounting entries: both taxes the 18.0 fiscal
    position mapped to still exist, so posted invoices, their tax lines and the
    tax reports built on them are left exactly as they were. Only the mapping
    a *new* invoice goes through changes.

    Order matters: create the group first, then drop what it replaces, so the
    fiscal position is never left without a mapping in between.
    """
    env = api.Environment(cr, api.SUPERUSER_ID, {})
    _create_bundle_tax(env)
    _drop_superseded_mappings(env)
