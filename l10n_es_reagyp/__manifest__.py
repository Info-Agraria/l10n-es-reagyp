# Copyright 2026 Pablo Renero Balgañón <info@infoagraria.es>
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Spain - REAGYP (seller side)",
    "version": "18.0.1.0.2",
    "category": "Localization/Account Charts",
    "summary": "Seller-side REAGYP fiscal layer: sale compensation taxes, "
    "fiscal position, dedicated receipts journal. Complements the "
    "core buyer-side REAGYP.",
    "author": "Pablo Renero Balgañón",
    "website": "https://github.com/Info-Agraria/l10n-es-reagyp",
    "support": "info@infoagraria.es",
    "license": "LGPL-3",
    # Store cover image (thumbnail): first entry is used as the cover.
    "images": ["static/description/banner.png"],
    "depends": [
        "l10n_es",
    ],
    # data/template/*.csv files are auto-discovered by the chart-template loader
    # via account_chart_template.py; they are NOT listed in "data".
    "data": [],
    "post_init_hook": "_l10n_es_reagyp_post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
    "development_status": "Beta",
}
