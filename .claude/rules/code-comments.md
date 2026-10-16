# Shipped code carries no internal information
Code inside a module directory ships to customers. In comments, docstrings,
XML comments, help strings and migrations:
- No issue or PR numbers (`#119`). Put the link in the commit or PR.
- No links to private repos, no org or repo names.
- No customer, farm or person names.
Explain the why in plain words instead: "Bridges add their buttons after this
anchor", not "Extension anchor (#121)".
