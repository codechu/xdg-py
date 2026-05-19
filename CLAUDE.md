# CLAUDE.md — codechu-xdg

Bootstrap per `codechu-org/ai/AGENTS.md` §0 before any work. Prefer
the local clone at `$org_home/codechu-org/ai/AGENTS.md` (if
`~/.config/codechu/config.toml` has `org_home` set); otherwise
WebFetch the public raw URL
<https://raw.githubusercontent.com/codechu/codechu-org/main/ai/AGENTS.md>.
This file lists only product-local overrides.

## Product-local notes

- Mirrors the XDG Base Directory Specification with Codechu's
  `vendor/product` namespacing convention. Do not invent new path
  conventions — if the spec doesn't define a category, ask before
  adding one.
- Public API: `App(vendor, product)` + `settings_file`, `cache_file`,
  `data_file`, `log_file`, `runtime_file`, `remove_cache`,
  `remove_runtime`.
- Cleanup helpers (`remove_*`) must never traverse outside the
  vendor/product subtree they were constructed for. Tests cover this
  invariant; do not relax them.
- Coverage target: ≥90 %. Current 97 %.

## Discipline reminders (org rules apply)

- Conventional Commits, no AI signature.
- No `--no-verify`, no force push, no unapproved publish.
- See `codechu-org/ai/AGENTS.md` for the full list.
