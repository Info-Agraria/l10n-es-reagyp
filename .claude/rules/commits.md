# Commits
- Conventional Commits: `type(scope): subject`. Subject imperative, lowercase,
  no trailing period, at most 72 characters.
- Types: feat, fix, docs, chore, ci, refactor, build, test.
- Any commit that touches a `.md` file is `docs`, even when it also changes
  code. Its body has two sections:
  - `Inventory:` one bullet per document touched, with the concrete change.
  - `Why:` what prompted the change.
- Split a commit when code and docs have different reasons to change.
- Both hooks run at the commit-msg stage. Install them with
  `pre-commit install --hook-type pre-commit --hook-type commit-msg`.
