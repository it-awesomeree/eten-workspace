# CI/CD Pipeline Notes — Eten

Overview of the 7-agent CI/CD swarm pipeline used for web app deployments.

---

## Pipeline Overview

The CI/CD pipeline is a 7-agent sequential pipeline triggered on PR merge to `test` or `main`.

```
PR Merge → Agent 1 (Code Review) → Agent 2 (Architecture Review)
  → Agent 3 (QA) → Agent 4 (Merge) → Agent 5 (Build + Staging Deploy)
  → Agent 6 (Canary Rollout) → Agent 7 (Verification + Jira Close)
```

---

## Agent Responsibilities

| Agent | Role | Key Actions |
|-------|------|-------------|
| **1 — Code Reviewer** | Review code quality | 10-category checklist: correctness, security, performance, types, duplication, etc. |
| **2 — Architect** | Review architecture | Conditional — triggered if Agent 1 flags concerns. Checks scalability, patterns, dependencies |
| **3 — QA** | Run tests | 4 phases: unit → integration → E2E → coverage analysis. AI-generated test suggestions |
| **4 — Merger** | Merge PR | Squash merge strategy with clean commit messages |
| **5 — Builder** | Build + deploy staging | Production build, deploy to staging environment |
| **6 — Canary** | Gradual rollout | 5% → 25% → 50% → 100% with auto-rollback on error spike |
| **7 — Verifier** | Post-deploy verification | Smoke tests, Jira ticket closure |

---

## Key Points for Developers

1. **All checks must pass** before merge — no bypassing
2. **Security review** is part of Agent 1's checklist (OWASP top 10)
3. **Auto-rollback** kicks in if error rates spike during canary deployment
4. **Jira tickets** are automatically closed by Agent 7 on successful deploy
5. **Branch protection** — `test` and `main` require PR reviews

---

## What This Means for My Workflow

- Write clean code that passes Agent 1's review → less rework
- Include tests with PRs → Agent 3 will run them
- PR to `test` first → pipeline runs on `test` branch
- After `test` validation → PR from `test` to `main` triggers production pipeline
- If canary fails → auto-rollback, investigate and fix

---

## Reference

Full pipeline specification: `/cicd-swarm` command (844 lines of detail including `.swarm-config.yml` reference).
