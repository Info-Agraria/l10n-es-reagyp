============================
Spain - REAGYP (seller side)
============================

This module adds the **seller-side** fiscal layer for the Spanish
**REAGYP** regime (*Régimen Especial de la Agricultura, Ganadería y
Pesca*) on top of the mainland Spanish chart of accounts (``l10n_es``).

Farmers, stockbreeders and fishers under this special VAT regime do not
charge VAT on their sales; instead, the buyer pays them a flat-rate
**compensation** (12% for agricultural and forestry products, 10.5% for
livestock and fishing products). This module provides everything the
seller needs to invoice that compensation correctly:

- **Compensation taxes** for the applicable rates, plugged into the
  ``es_common_mainland`` chart template.
- A dedicated **fiscal position** that maps standard sale taxes to the
  REAGYP compensation taxes automatically.
- A dedicated **REAGYP receipts journal** (the buyer issues a receipt,
  *recibo*, rather than the seller issuing a VAT invoice).
- The required **accounts** and **tax group** for the compensation.

A ``post_init_hook`` backfills this data into companies that already had
a mainland Spanish chart loaded before the module was installed. Canary
Islands charts are intentionally out of scope: there is no REAGYP under
the Canary regime.

Configuration
=============

No manual configuration is required.

On installation, the module injects its accounts, tax group,
compensation taxes, fiscal position and the REAGYP receipts journal into
the mainland Spanish chart template (``es_common_mainland``). If a
company already had a mainland Spanish chart installed beforehand, a
``post_init_hook`` backfills the same data for that company
automatically.

Usage
=====

1.  Make sure the company uses a **mainland** Spanish chart of accounts
    (``l10n_es``, ``es_common_mainland``-based).
2.  On the customer to be invoiced under REAGYP, set the **REAGYP fiscal
    position**.
3.  Create the customer document (sale order / invoice / receipt). The
    sale taxes are automatically replaced by the REAGYP compensation
    taxes, and the move is posted against the dedicated REAGYP receipts
    journal.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/Info-Agraria/l10n-es-reagyp/issues>`_.

Credits
=======

Authors
~~~~~~~

* Pablo Renero Balgañón

Maintainer
~~~~~~~~~~

This module is maintained by **Info Agraria**.

Contact: info@infoagraria.es
