# References
Facts and architecture claims cite their source. Cite what does not move,
and date every source, because what it says can change.

In the text, cite with a number: "Recintos are versioned per campaign [2]."
At the end of the doc, list the sources:

    ## References
    1. `docs/ARCHITECTURE.md`, section "Module layout". Read 2026-10-16.
    2. FEGA, "Servicios SIGPAC", https://example.org/sigpac. Read 2026-10-16.
    3. `Info-Agraria/l10n-es-reagyp#5`. State as of 2026-10-16.

| Cite | Like this | Not like this |
|---|---|---|
| A doc | path + section heading | a line number or a section number |
| Code | module `agriculture_sigpac`, model `agriculture.plot`, field, XML id | a file path with line numbers |
| Work | `Info-Agraria/l10n-es-reagyp#5` (always with owner/repo) | a bare `#5` |
| A pin | a commit SHA, only where the pin is the point | a SHA as a general link |
| Outside the org | URL + date read | a bare URL |

If a cited name is renamed, the rename PR updates the docs that cite it.
Shipped code never cites anything internal: see `code-comments.md`.
