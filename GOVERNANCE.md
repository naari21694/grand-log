# Governance

Grand Log is young, with a clear ambition: grow a real, self-propelling crew. We borrow the mechanics that actually scale — Kubernetes-style `OWNERS`, Node.js-style no-objection promotion windows, Apache-style "merit doesn't expire" — at thresholds a small project can realistically hit.

## Principles
- Anyone contributes via fork → PR. **Nobody pushes to `main` directly.**
- We don't quantify *merit* (subjective) — we quantify the **gate**: named sponsors + time-in-grade + a no-objection window.
- **Every promotion is a reviewable PR** against `MAINTAINERS.md` / `OWNERS`.

## The ladder

| Rung | Can do | Promotion rule (measurable) | Approved by | Recorded as |
|---|---|---|---|---|
| **User** | Open issues, join Discussions | — | — | — |
| **Contributor** | Credited in the README | **≥1 merged PR** (code, docs, tests, or triage) | Automatic | contributors list |
| **Triager** | Label/triage issues, apply `good first issue`, close dupes | Active **≥1 month** + triaged/commented on **≥10** issues/PRs | **1 Maintainer**; no objection in **7 days** | `TRIAGERS` in MAINTAINERS.md (a PR) |
| **Reviewer** | Review + approve PRs (auto-requested via CODEOWNERS) | Contributor **≥3 months** + primary reviewer on **≥5 PRs** + **≥15** merged PRs/reviews | **1 Maintainer sponsors**; no objection from any Maintainer in **7 days** | `reviewers:` in OWNERS (a PR) |
| **Maintainer** | Merge + release rights, governance vote | Reviewer **≥3 months** + primary reviewer on **≥10 PRs** + **≥25** merged PRs/reviews | **2 Maintainers** (1 nominates + 1 sponsors); no objection in **14 days** | `approvers:` in OWNERS (a PR) |

Thresholds are scaled-down Kubernetes numbers — we keep the **ratios + time-in-grade** and raise the counts as the crew grows.

> **How it works on GitHub today:** a promotion is simply a PR adding you to `MAINTAINERS.md` / [`OWNERS`](OWNERS) / `.github/CODEOWNERS`, approved per the rule above; branch protection then auto-requests your review on matching paths. The Kubernetes-style `/lgtm` bot automation is a later scaling step — the ladder works fine on plain GitHub without it.

## Decisions
- Small changes: a Maintainer reviews + merges.
- Direction / larger changes: open an issue or Discussion first (a **10-day** comment window for proposals).
- **Lazy consensus**: silence = assent. A Maintainer `-1` *with a stated reason* blocks until resolved (Apache-style veto).

## Merit doesn't expire
No contributions in **12 months** → moved to `EMERITUS` in MAINTAINERS.md (not removed). Re-activation is easy — just come back.

## Recognition (automated)
contrib.rocks avatars in the README · `@`-credit in every release · GitHub achievements · a `FUNDING.yml` Sponsor button. We may add the **all-contributors** bot for non-code recognition as we grow.

## Why a CLA + dual license
So Grand Log stays free and open forever for the community while a commercial license funds the work — see [LICENSING.md](LICENSING.md).
