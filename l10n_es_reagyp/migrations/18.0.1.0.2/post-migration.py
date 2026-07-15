# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
import logging

_logger = logging.getLogger(__name__)


def migrate(env, version):
    """Lower the REAGYP compensation tax group's sequence on existing installs.

    The sequence orders the blocks in the invoice's tax-totals summary. All
    core tax groups ship at sequence 10, so the compensation group (created
    last) tied and rendered AFTER the IRPF retention — an odd reading order
    (retention before compensation). New chart loads pick up sequence 5 from
    the CSV; existing per-company groups were already instantiated at 10, and
    the post_init hook never rewrites existing rows, so update them in place.

    This is presentation only: the tax *computation* order is governed by the
    taxes' own sequence (compensation 1, retention 1000), untouched here.
    """
    Template = env["account.chart.template"]
    fixed = 0
    for company in env["res.company"].search([]):
        group = Template.with_company(company).ref(
            "tax_group_reagyp", raise_if_not_found=False
        )
        if group and group.sequence != 5:
            group.sequence = 5
            fixed += 1
    if fixed:
        _logger.info(
            "l10n_es_reagyp: set REAGYP tax group sequence on %s company(ies) "
            "so compensation renders before the IRPF retention",
            fixed,
        )
