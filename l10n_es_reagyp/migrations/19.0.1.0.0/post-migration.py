# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

from odoo import Command, api

from odoo.addons.l10n_es_reagyp.hooks import _l10n_es_reagyp_post_init_hook

_logger = logging.getLogger(__name__)


def _drop_superseded_core_retention(env):
    """Unhook the core 2% retention from the REAGYP sale fiscal position.

    On 18.0 the fiscal position mapped `tax_reagyp_s_ns` to the *core*
    retention, `account_tax_template_s_irpf2`. OpenUpgrade converts that row
    into the 19.0 shape, so an upgraded database arrives here with the core
    retention attached to `fp_reagyp_sale`.

    We cannot keep borrowing it. In 19.0 a destination tax carries the same
    substitution in *every* fiscal position it belongs to, and the core
    retention lists every sale VAT tax among its `original_tax_ids`; joining
    our fiscal position would silently replace a 21% sale with a 2% retention.
    That is why 19.0.1.0.0 ships its own `tax_reagyp_s_irpf2`.

    Both mappings would apply at once, withholding 2% twice on the same
    invoice, so the old one has to go.
    """
    Template = env["account.chart.template"]
    unhooked = 0
    for company in env["res.company"].search([]):
        template = Template.with_company(company)
        position = template.ref("fp_reagyp_sale", raise_if_not_found=False)
        core_retention = template.ref(
            "account_tax_template_s_irpf2", raise_if_not_found=False
        )
        source = template.ref("tax_reagyp_s_ns", raise_if_not_found=False)
        if not (position and core_retention and source):
            continue
        if core_retention in position.tax_ids:
            position.tax_ids = [Command.unlink(core_retention.id)]
            unhooked += 1
        # `tax_reagyp_s_ns` only ever reached the core retention through our
        # own mapping, so dropping it does not affect fp_irpf2 or any other
        # position the core retention serves.
        if source in core_retention.original_tax_ids:
            core_retention.original_tax_ids = [Command.unlink(source.id)]
    if unhooked:
        _logger.info(
            "l10n_es_reagyp: detached the core 2%% retention from the REAGYP "
            "sale fiscal position on %s company(ies); the module now ships its "
            "own tax_reagyp_s_irpf2",
            unhooked,
        )


def migrate(cr, version):
    """Bring an upgraded database to the same shape as a fresh 19.0 install.

    Chart-template records are only instantiated when the module is installed,
    never when it is upgraded, so the retention tax added in 19.0.1.0.0 does
    not exist yet on an existing database. The post-init hook is the module's
    own idempotent backfill for exactly this situation — it creates whatever a
    company is missing and rewrites nothing — so reuse it rather than
    duplicating the template calls here.

    Order matters: create the new retention first, then detach the old one, so
    the fiscal position is never left without a retention in between.
    """
    env = api.Environment(cr, api.SUPERUSER_ID, {})
    _l10n_es_reagyp_post_init_hook(env)
    _drop_superseded_core_retention(env)
