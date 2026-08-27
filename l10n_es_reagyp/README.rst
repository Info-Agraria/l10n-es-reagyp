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
- Two dedicated **fiscal positions**: a sale one that maps the standard
  sale tax to the REAGYP compensation and the IRPF withholding, and a
  purchase one that makes input VAT non-deductible.
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
compensation taxes, fiscal positions and the REAGYP receipts journal into
the mainland Spanish chart template (``es_common_mainland``). If a
company already had a mainland Spanish chart installed beforehand, a
``post_init_hook`` backfills the same data for that company
automatically.

Usage
=====

1.  Make sure the company uses a **mainland** Spanish chart of accounts
    (``l10n_es``, ``es_common_mainland``-based).
2.  On the customer to be invoiced under REAGYP, set the **REAGYP -
    sale (farmer)** fiscal position.
3.  Create the customer document (sale order / invoice / receipt). The
    sale taxes are automatically replaced by the REAGYP compensation
    taxes, and the move is posted against the dedicated REAGYP receipts
    journal.
4.  On your suppliers, set the **REAGYP - purchase (farmer)** fiscal
    position, so that input VAT is booked as non-deductible.

Sale and purchase are two separate positions on purpose. Which taxes a
sale carries depends on whether the buyer is himself under REAGYP, so it
is decided per customer. Whether input VAT is deductible does not depend
on the supplier at all: under this regime the farmer deducts none of it,
and the flat-rate compensation is what makes up for that.

Neither position is applied automatically. Like every regime position
``l10n_es`` ships (``fp_reagyp_a``, ``fp_irpf*``), they are assigned by
hand, because whether they fit is a bookkeeping judgement rather than
something a module can decide. A deployment whose activity is entirely
within REAGYP may well want to tick **Detect Automatically** on the
purchase position so that it covers every supplier without maintenance;
that is a decision for whoever keeps the books, and it is one checkbox
on the position itself. It is deliberately left off here because the
module's data is created in every company holding a mainland Spanish
chart, and a company outside the regime must keep deducting its input
VAT. The same caveat applies to a farmer running a separate activity
outside REAGYP, whose purchases for that activity remain deductible.

A partner that is both customer and supplier -- a cooperative you sell
produce to and buy supplies from -- can only carry one fiscal position,
since Odoo resolves it per partner and not per document type. The usual
way out is a child contact for the other role, each with its own
position.

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
