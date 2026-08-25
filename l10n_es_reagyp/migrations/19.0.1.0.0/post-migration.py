# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

from odoo import Command, api

from odoo.addons.l10n_es_reagyp.hooks import _l10n_es_reagyp_post_init_hook

_logger = logging.getLogger(__name__)

# The 18.0 fiscal position mapped the no-sujeto sale tax onto two destinations.
# 19.0 routes it through a single group tax instead, so both of the old
# destinations have to let go of the source.
SUPERSEDED_DESTINATIONS = ("tax_reagyp_s_12", "account_tax_template_s_irpf2")


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

    Chart-template records are only instantiated when the module is installed,
    never when it is upgraded, so the group tax added in 19.0.1.0.0 does not
    exist yet on an existing database. The post-init hook is the module's own
    idempotent backfill for exactly this situation -- it creates whatever a
    company is missing and rewrites nothing -- so reuse it rather than
    duplicating the template calls here.

    Order matters: create the group first, then drop what it replaces, so the
    fiscal position is never left without a mapping in between.
    """
    env = api.Environment(cr, api.SUPERUSER_ID, {})
    _l10n_es_reagyp_post_init_hook(env)
    _drop_superseded_mappings(env)
