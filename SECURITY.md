# Security policy

`codechu-xdg` returns filesystem paths and offers two cleanup helpers
(`remove_cache`, `remove_runtime`) that **delete** files under a
vendor/product subtree. Anything that lets those helpers escape that
subtree — or that lets a path land somewhere it shouldn't — is
security-relevant.

## Supported versions

| Version | Supported |
|---|:---:|
| `main` branch | ✅ |
| Latest minor release (0.x) | ✅ |
| Older releases | ❌ |

Pre-1.0.0 period — only the latest minor receives security fixes.

## Reporting a vulnerability

### Preferred path — GitHub Security Advisory (private)

Open a **private** advisory at
[github.com/codechu/codechu-xdg-py/security/advisories/new](https://github.com/codechu/codechu-xdg-py/security/advisories/new).
The disclosure stays non-public until a fix lands, and a CVE can be
requested automatically.

### Alternative — Email

Write to `security@codechu.com`.

## Scope — what to report

**In scope:**

- **Path escape from `remove_cache` / `remove_runtime`** — any way to
  make them touch a file outside the `<vendor>/<product>/` subtree
  they were constructed for.
- **Symlink traversal** during cleanup that follows a link out of the
  subtree.
- **Vendor / product name injection** — characters in `vendor` or
  `product` that resolve a path outside the intended XDG base
  (`..`, absolute paths, NUL).
- **Spec deviation** that places user data in a base directory the
  XDG spec does not authorize (e.g. cache content written under
  `$XDG_CONFIG_HOME`).
- **Honoring a relative `XDG_*` value** — the spec says relative
  values must be ignored; doing otherwise is a bug.

**Out of scope:**

- Users passing a vendor / product they shouldn't have control over
  (that's an upstream caller bug, not ours — though we still happily
  harden the input check if you propose one).
- Filesystem-level race conditions outside our control (another
  process racing the same path).
- Platform support for macOS / Windows — this library targets
  Linux / Unix only.

## Process

Reports are reviewed on a best-effort basis — no fixed SLA. We aim
for coordinated disclosure within **90 days** of the report,
extendable by mutual agreement if a fix is non-trivial.

Public disclosure is coordinated after the fix is released
(together with the reporter).

## Public disclosure

Once a confirmed fix is released:

- A summary is added to the CHANGELOG under the `### Security`
  category (with the reporter's name if they want credit).
- A GitHub Security Advisory is published.
- If a CVE was assigned, its number is referenced.
