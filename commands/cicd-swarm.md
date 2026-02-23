---
description: Multi-Agent CI/CD Swarm - Automated review, QA, merge, deploy, and verification pipeline replacing human gates
argument-hint: [agent name, pipeline stage, or question]
---

# Multi-Agent CI/CD Swarm

Automated pipeline of AI agents that replace human review gates. Triggered when a dev moves a Jira ticket to TO REVIEW and creates a PR.

**Runtime**: GitHub Actions
**Authority model**: Fully automated — no human reviewers in the loop
**Stack**: Stack-agnostic (mixed repos — Next.js, Python, Node.js, etc.)
**Auto-fix**: Claude Code auto-fixes issues found by Agents 1-3, commits to PR branch, and re-runs. Only fails back to dev after 2 failed auto-fix attempts.

---

## Auto-Fix Loop (applies to Agents 1, 2, and 3)

When any review/QA agent finds CRITICAL or HIGH issues:

```
Agent finds issues
       │
       ▼
Claude Code auto-fix attempt #1
  ├─ Fix committed to PR branch
  ├─ Agent re-runs on updated code
  │     ├─ PASS → pipeline proceeds
  │     └─ FAIL → auto-fix attempt #2
  │              ├─ Fix committed
  │              ├─ Agent re-runs
  │              │     ├─ PASS → pipeline proceeds
  │              │     └─ FAIL → escalate to dev
  │              └─ Can't fix → escalate to dev
  └─ Can't fix → escalate to dev
```

**Max auto-fix attempts**: 2 per agent
**What "escalate to dev" means**: PR is blocked, dev is notified via PR comment + Jira comment with exact issues and what auto-fix attempted. Dev must push a manual fix, which re-triggers the full pipeline.
**Auto-fix commit message**: `fix(ai): <agent name> — <brief description of fix>`

---

## Pipeline Overview

```
PR Created by Dev
       │
       ▼
┌─────────────────────────────────────┐
│  Agent 1: AI Code Review            │  ← Auto-review + auto-fix
├─────────────────────────────────────┤
│  Agent 2: AI Design & Architecture  │  ← Auto-review + auto-fix (conditional)
├─────────────────────────────────────┤
│  Agent 3: QA Validation             │  ← Auto-test + auto-fix
├─────────────────────────────────────┤
│  Agent 4: Merge to Main             │  ← Auto-merge
├─────────────────────────────────────┤
│  Agent 5: Build & Deploy            │  ← Auto-build + staging deploy
├─────────────────────────────────────┤
│  Agent 6: Production Rollout        │  ← Canary + auto-rollback
├─────────────────────────────────────┤
│  Agent 7: Verify & Close Loop       │  ← Health check + Jira → DONE
└─────────────────────────────────────┘

Zero human intervention in the happy path.
Dev only gets pulled back in if auto-fix fails after 2 attempts.
```

---

## Agent 1: AI Code Review Agent

**Trigger**: PR opened or updated (push to PR branch)
**Authority**: Fully automated — must PASS before any subsequent agent runs. Auto-fixes issues via Claude Code (up to 2 attempts) before escalating to dev.
**Runtime**: GitHub Actions workflow (`pull_request`, `pull_request_synchronize` events)
**GitHub integration**: Required status check, posts via PR review API (`APPROVE` or `REQUEST_CHANGES`)

### Review Checklist (stack-agnostic)

| Category | What it checks |
|----------|---------------|
| **Correctness** | Logic errors, off-by-one, null/undefined handling, race conditions |
| **Security** | OWASP top 10 (injection, XSS, auth bypass, secrets in code, insecure deps) |
| **Performance** | N+1 queries, unnecessary re-renders, missing indexes, unbounded loops, memory leaks |
| **Error handling** | Missing try/catch, swallowed errors, unhelpful error messages, missing fallbacks |
| **Code quality** | Dead code, code duplication, naming clarity, function complexity (cyclomatic), file size |
| **Tests** | Are new/changed paths covered? Do tests actually assert meaningful things? Mocks appropriate? |
| **API contracts** | Breaking changes to APIs, missing versioning, schema drift |
| **DB migrations** | Reversibility, data loss risk, locking concerns, index strategy |
| **Dependencies** | New deps justified? License compatible? Known vulnerabilities? |
| **Observability** | Logging for new code paths, metrics for business-critical flows, trace propagation |

### Severity Levels & Gate Logic

| Severity | Blocks PR? | Examples |
|----------|-----------|----------|
| **CRITICAL** | Yes — hard block | Security vulnerability, data loss risk, secrets exposed, breaking production API |
| **HIGH** | Yes — hard block | Logic bug in core path, missing error handling on external calls, no tests for new feature |
| **MEDIUM** | No — warning | Suboptimal performance, missing edge case test, code style issues |
| **LOW** | No — suggestion | Naming improvements, refactoring opportunities, documentation gaps |

**Gate rule**: PR is blocked if ANY critical or high severity finding exists. Medium/low are posted as comments but don't block.

### Output Format (PR comment)

```markdown
## AI Code Review — [PASS/FAIL]

### Summary
<1-2 sentence overview of the change and overall assessment>

### Findings

#### CRITICAL (0)
#### HIGH (0)
#### MEDIUM (2)
- **[file:line]** <description> — <suggestion>
- **[file:line]** <description> — <suggestion>

#### LOW (1)
- **[file:line]** <description> — <suggestion>

### What looks good
- <positive observations about the PR>

### Verdict: PASS / FAIL
<If FAIL: list the blocking findings that must be resolved>
```

### Override Mechanism
- Dev can push a fix and re-trigger
- For false positives: label `ai-review-override` can be applied by a **code owner** (not the PR author) to bypass

---

## Agent 2: AI Design & Architecture Review Agent

**Trigger**: Conditional — only when PR touches architecture-sensitive areas
**Authority**: Fully automated — auto-fixes architectural issues via Claude Code (up to 2 attempts) before escalating to dev. Same severity model as Agent 1.
**Runs after**: Agent 1 passes
**Can be skipped**: Yes — if trigger conditions not met, pipeline moves straight to Agent 3

### Trigger Conditions (any one = agent runs)

| Condition | Detection method |
|-----------|-----------------|
| New files or modules created | Diff contains new file paths |
| API routes added/modified | Files matching `*/api/*`, `*/routes/*`, `*/controllers/*`, `*/endpoints/*` |
| DB schema / migration changes | Files matching `*/migrations/*`, `*.sql`, schema files, ORM model changes |
| Config or infra changes | `docker*`, `*.yml`/`*.yaml` CI files, `terraform/*`, env config files |
| Large diff | >300 lines changed across the PR |
| Dependency changes | `package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, lock files |
| New service or module boundary | New top-level directories, new microservice folders |

If **none** of these conditions match → Agent 2 is **skipped** with status `SKIPPED — no architectural changes detected` and pipeline proceeds to Agent 3.

### Review Checklist

| Category | What it evaluates |
|----------|-------------------|
| **Pattern consistency** | Does the change follow existing repo patterns? (folder structure, naming conventions, module organization) |
| **Separation of concerns** | Is business logic mixed into API handlers? Are DB queries leaking into UI components? |
| **API design** | RESTful conventions, consistent error responses, proper HTTP status codes, pagination, versioning |
| **Data modeling** | Normalization, relationship design, index strategy, migration safety (can it rollback?) |
| **Scalability** | Will this approach hold at 10x load? Synchronous bottlenecks? Missing caching layer? |
| **Coupling & cohesion** | Does the change create tight coupling between modules? Hidden dependencies? Circular imports? |
| **Config & secrets management** | Hardcoded values that should be env vars? Secrets in wrong places? |
| **Error boundaries** | Are failure domains isolated? Can one component's failure cascade? |
| **Backward compatibility** | Breaking changes to existing consumers? Migration path for downstream? |
| **Over-engineering** | Is the change too complex for what it solves? Premature abstractions? |

### Severity Levels & Gate Logic

| Severity | Blocks PR? | Examples |
|----------|-----------|----------|
| **CRITICAL** | Yes | New public API with no auth, migration that drops column with no rollback, circular dependency creating deadlock risk |
| **HIGH** | Yes | Breaking API contract with no versioning, business logic in wrong layer with no separation, new service with no health check |
| **MEDIUM** | No — warning | Inconsistent naming vs existing patterns, missing caching for heavy query, could use existing util instead of new one |
| **LOW** | No — suggestion | Folder structure could be cleaner, consider extracting interface, documentation of architecture decision |

### Output Format (PR comment)

```markdown
## AI Architecture Review — [PASS/FAIL/SKIPPED]

### Trigger reason
<Why this agent was activated — e.g., "New API routes detected", "DB migration added", ">300 lines changed">

### Architectural Assessment
<2-3 sentence overview: does this change fit the system's architecture?>

### Findings

#### CRITICAL (0)
#### HIGH (0)
#### MEDIUM (1)
- **[area]** <description> — <recommendation>

#### LOW (0)

### Design Observations
- <observations about good design decisions in the PR>

### Verdict: PASS / FAIL / SKIPPED
```

### Override Mechanism
- Same as Agent 1: label `ai-arch-override` by a code owner
- Can also be force-triggered on any PR with label `needs-arch-review`

---

## Agent 3: QA Validation Agent

**Trigger**: Agents 1 (and 2 if applicable) pass
**Authority**: Fully automated — must PASS before merge. Auto-fixes test failures and coverage gaps via Claude Code (up to 2 attempts) before escalating to dev.
**Capabilities**: Full auto — runs existing tests, generates new tests, runs E2E, validates test quality
**Team context**: Designed for intern + junior team — enforces discipline while educating

### What It Does (4 phases)

#### Phase 1: Run Existing Test Suites
- Auto-detects test framework from repo (`jest`, `pytest`, `vitest`, `mocha`, `playwright`, `cypress`, etc.)
- Runs full test suite (or affected tests only if repo supports `--changedSince`)
- Captures results: pass/fail count, duration, failures with stack traces
- **Gate**: If existing tests fail → immediate FAIL, no further phases run

#### Phase 2: Coverage Analysis on Changed Files
- Runs tests with coverage enabled (`--coverage`)
- Extracts coverage for **only the files changed in the PR**
- **Coverage threshold**: Configurable per repo via `.swarm-config.yml`, default **80% line coverage on changed files**
- Reports uncovered lines with file:line references
- **Gate**: If changed files are below threshold → FAIL (with specific uncovered lines listed)

```yaml
# .swarm-config.yml (per repo)
qa:
  coverage_threshold: 80        # default 80%
  coverage_target: changed      # "changed" (only PR files) or "all" (whole repo)
  skip_coverage_for:
    - "*.config.*"
    - "migrations/*"
    - "scripts/*"
```

#### Phase 3: AI Test Generation for Uncovered Paths
- Identifies uncovered code paths in changed files
- Generates test cases targeting those paths
- Runs the generated tests to validate they pass
- Opens a **follow-up commit** on the PR branch with the new tests (dev can review)
- Comment on PR: "Added X tests covering Y previously uncovered paths"
- **Not a gate** — generated tests are additive, don't block if they fail (flagged for dev review)

#### Phase 4: Test Quality Audit
- Checks generated and existing tests for:
  - **Meaningful assertions**: Not just `expect(true).toBe(true)`
  - **Mock hygiene**: Over-mocking that makes tests useless, mocking the thing being tested
  - **Flakiness signals**: Time-dependent, order-dependent, network-dependent without mocks
  - **Edge cases**: Boundary conditions tested? Empty inputs? Error paths?
- Posts quality findings as PR comments (non-blocking, educational for interns)

### Severity Levels & Gate Logic

| Severity | Blocks PR? | Examples |
|----------|-----------|----------|
| **CRITICAL** | Yes | Existing tests fail, security test fails |
| **HIGH** | Yes | Changed files below coverage threshold, test run detects regression |
| **MEDIUM** | No — warning | Generated tests reveal uncovered error paths, flaky test detected |
| **LOW** | No — educational | Test quality suggestions, mock hygiene tips, edge case recommendations |

### Output Format (PR comment)

```markdown
## QA Validation — [PASS/FAIL]

### Test Suite Results
- **Framework**: jest v29.7
- **Total**: 142 tests | **Passed**: 142 | **Failed**: 0 | **Skipped**: 3
- **Duration**: 23.4s

### Coverage (changed files only)
| File | Lines | Branches | Threshold | Status |
|------|-------|----------|-----------|--------|
| src/api/orders.ts | 92% | 85% | 80% | PASS |
| src/utils/calc.ts | 67% | 50% | 80% | FAIL |

**Uncovered lines in failing files:**
- `src/utils/calc.ts:45-52` — error handling branch for negative values
- `src/utils/calc.ts:78` — edge case when input is empty array

### AI-Generated Tests
- Generated **3 tests** for uncovered paths → committed to PR branch
- Tests cover: negative value handling, empty array edge case, overflow boundary

### Test Quality Audit
- No major quality issues found
- Suggestion: `orders.test.ts:23` — consider testing with malformed input

### Verdict: PASS / FAIL
```

### Why This Matters for Intern + Junior Team
- **Phase 1** catches "I didn't run the tests before pushing" (very common with interns)
- **Phase 2** catches "I wrote the feature but zero tests" (extremely common)
- **Phase 3** teaches by example — interns see how AI writes tests for their code
- **Phase 4** educates without blocking — builds good testing habits over time

### Override Mechanism
- Label `qa-override` by a code owner to bypass
- Coverage threshold can be lowered per-repo in `.swarm-config.yml`

---

## Agent 4: Merge to Main Agent

**Trigger**: Agents 1, 2 (if applicable), and 3 all pass
**Authority**: Auto-merge — performs the merge without human intervention
**Runs after**: All review/QA gates pass

### Pre-Merge Checklist (all must be true)

| Check | What it verifies |
|-------|-----------------|
| **All required status checks pass** | Agent 1 (code review), Agent 2 (arch review, or skipped), Agent 3 (QA) all PASS |
| **No unresolved review threads** | All PR conversation threads resolved |
| **Branch is up-to-date with main** | No new commits on main since PR branch was created/rebased |
| **No merge conflicts** | Clean merge possible without manual resolution |
| **PR description complete** | Summary, testing done, risk notes all present (template compliance) |
| **No `do-not-merge` label** | Escape hatch — anyone can add this label to halt the merge |

### If Branch is Behind Main

```
Auto-rebase sequence:
1. Attempt rebase onto latest main
2. If clean rebase → re-run Agent 3 (QA) on rebased code
3. If conflicts → FAIL with conflict report, assign back to dev
```

### Merge Strategy

| Scenario | Strategy | Reason |
|----------|----------|--------|
| Default | **Squash merge** | Clean history — intern commits are often "fix", "wip", "asdf" |
| Configurable | Per-repo in `.swarm-config.yml` | For repos that prefer rebase or merge-commit |

```yaml
# .swarm-config.yml (per repo)
merge:
  strategy: squash              # "squash" (default) | "rebase" | "merge-commit"
  delete_branch_after: true     # clean up feature branch after merge
  require_linear_history: true  # enforce no merge commits on main
```

### Merge Commit Message Format

```
<PR title> (#<PR number>)

<PR body summary — first 3 lines>

Reviewed-by: ai-code-review-agent
Reviewed-by: ai-arch-review-agent (if applicable)
Tested-by: ai-qa-agent
Coverage: <X%> on changed files
Jira: <ticket ID extracted from branch name or PR body>
```

### Post-Merge Actions
1. **Delete feature branch** (configurable, default: on)
2. **Post merge confirmation** as final PR comment
3. **Trigger Agent 5** (Build & Deploy) via workflow dispatch
4. **Update Jira ticket** status comment: "PR merged to main — awaiting deployment"

### Failure Modes

| Failure | What happens |
|---------|-------------|
| Merge conflict | FAIL — posts conflict details, re-assigns to dev, adds `merge-conflict` label |
| Rebase breaks tests | FAIL — posts test failures after rebase, dev must resolve |
| Status check missing | WAIT — retries every 30s for up to 10 min, then FAIL with timeout |
| `do-not-merge` label present | HALT — posts "Merge blocked by do-not-merge label" and waits |
| Branch protection violation | FAIL — logs the specific rule that blocked |

### Output Format (PR comment)

```markdown
## Merge Agent — [MERGED/FAILED/WAITING]

### Pre-Merge Checks
- [x] All status checks passed
- [x] No unresolved threads
- [x] Branch up-to-date with main
- [x] No merge conflicts
- [x] PR description complete
- [x] No `do-not-merge` label

### Merge Details
- **Strategy**: Squash merge
- **Commit**: `abc1234` on main
- **Branch cleanup**: `feature/AW-288-compliance` deleted

### Next: Build & Deploy pipeline triggered
```

---

## Agent 5: Build & Deploy Agent

**Trigger**: Agent 4 successfully merges to main
**Authority**: Autonomous — builds and deploys to non-production environments automatically
**Event**: `push` to `main` branch (or `workflow_dispatch` from Agent 4)

### What It Does (3 phases)

#### Phase 1: Build Artifact
- Auto-detects build system (`npm run build`, `docker build`, `python setup`, etc.)
- Creates versioned, immutable build artifact
- Tags with: git SHA, timestamp, Jira ticket ID, PR number
- Stores artifact (container registry, GCS bucket, or GitHub artifact depending on repo)
- **Gate**: If build fails → pipeline stops, posts failure to PR and notification channel

```yaml
# .swarm-config.yml (per repo)
build:
  command: "npm run build"          # or "docker build", auto-detected if not set
  artifact_store: "gcr"             # "gcr" | "gar" | "gcs" | "github"
  dockerfile: "Dockerfile"          # if using Docker
  env_file: ".env.production"       # env template for build-time vars
```

#### Phase 2: Deploy to Staging
- Deploys built artifact to **staging environment** first
- Staging mirrors production config (same env vars, same infra, scaled down)
- Waits for deployment to be healthy (readiness/liveness checks)
- **Gate**: If staging deploy fails or health check fails → pipeline stops

| Deployment target | Method |
|-------------------|--------|
| **Google Cloud App Engine** | `gcloud app deploy` with `--version` flag |
| **Cloud Run** | `gcloud run deploy` with traffic tag `staging` |
| **Kubernetes** | `kubectl apply` to staging namespace |
| **Docker Compose** | SSH + `docker compose up` on staging VM |

Auto-detected from repo config or `.swarm-config.yml`.

#### Phase 3: Run Smoke Tests on Staging
- Hits critical endpoints/pages on staging to verify deployment works
- Tests defined in repo: `smoke-tests/` directory or `.swarm-config.yml`
- Checks: HTTP 200 on health endpoint, key pages load, API responds, no console errors
- **Gate**: If smoke tests fail → pipeline stops, does NOT proceed to production

```yaml
# .swarm-config.yml (per repo)
deploy:
  staging:
    url: "https://staging.employee.awesomeree.com.my"
    health_endpoint: "/api/health"
    smoke_tests:
      - endpoint: "/"
        expect_status: 200
      - endpoint: "/api/health"
        expect_status: 200
        expect_body_contains: "ok"
      - endpoint: "/inventory"
        expect_status: 200
  production:
    url: "https://employee.awesomeree.com.my"
    health_endpoint: "/api/health"
```

### Failure Modes

| Failure | What happens |
|---------|-------------|
| Build fails | STOP — posts build logs, notifies dev, Jira ticket stays in current state |
| Staging deploy fails | STOP — posts deploy logs, attempts rollback on staging |
| Smoke tests fail on staging | STOP — posts failure details, staging left in failed state for debugging |
| Artifact store unreachable | RETRY 3x with backoff, then FAIL |

### Output Format (posted to PR + Jira ticket)

```markdown
## Build & Deploy — [SUCCESS/FAILED]

### Build
- **Artifact**: `awesomeree-web:abc1234-20260210`
- **Size**: 142MB
- **Duration**: 2m 34s
- **Stored**: gcr.io/awesomeree/web-app:abc1234

### Staging Deployment
- **URL**: https://staging.employee.awesomeree.com.my
- **Status**: Healthy
- **Deploy time**: 1m 12s

### Smoke Tests (staging)
- [x] GET / → 200 (340ms)
- [x] GET /api/health → 200, body contains "ok" (45ms)
- [x] GET /inventory → 200 (520ms)

### Next: Production rollout ready — triggering Agent 6
```

---

## Agent 6: Production Rollout Agent

**Trigger**: Agent 5 staging deploy + smoke tests pass
**Authority**: Autonomous with automatic rollback capability
**Goal**: Zero-downtime production deployment with instant rollback if anything goes wrong

### Deployment Strategy: Canary Rollout

Traffic shifts gradually — not a big-bang deploy:

```
Step 1:  5% traffic → new version (canary)     ← watch for 2 min
Step 2: 25% traffic → new version              ← watch for 3 min
Step 3: 50% traffic → new version              ← watch for 3 min
Step 4: 100% traffic → new version             ← stable
```

At **each step**, the agent checks health signals. If any signal is bad → **automatic rollback to 0% new version**.

```yaml
# .swarm-config.yml (per repo)
rollout:
  strategy: canary              # "canary" (default) | "blue-green" | "rolling" | "instant"
  canary_steps: [5, 25, 50, 100]
  canary_watch_minutes: [2, 3, 3, 0]
  auto_rollback: true
  rollback_on:
    - error_rate_increase: 5%   # if error rate rises 5% above baseline
    - latency_p99_increase: 50% # if p99 latency rises 50% above baseline
    - health_check_fail: true   # if health endpoint returns non-200
    - crash_loop: true          # if container restarts >2 times in watch window
```

### Health Signals Monitored at Each Step

| Signal | Source | Rollback threshold |
|--------|--------|--------------------|
| **Error rate** | Application logs / monitoring | >5% increase over baseline |
| **Latency (p99)** | Request duration metrics | >50% increase over baseline |
| **Health endpoint** | HTTP GET to `/api/health` | Any non-200 response |
| **Container restarts** | Orchestrator metrics | >2 restarts in watch window |
| **Memory/CPU** | Infrastructure metrics | >90% sustained for 1 min |
| **Console errors** (if web app) | Client-side error tracking | Spike in new error types |

### Rollback Procedure

If any signal trips during canary:
1. Immediately shift 100% traffic back to previous version
2. New version kept running at 0% traffic (for debugging)
3. Post rollback report to PR, Jira, and notification channel
4. Mark pipeline as FAILED — dev must investigate and re-submit
5. Jira ticket moved back to IN PROGRESS with rollback comment

### Platform-Specific Rollout Methods

| Platform | How canary works |
|----------|-----------------|
| **App Engine** | Deploy new version → `gcloud app services set-traffic` to split by percentage |
| **Cloud Run** | Deploy with `--tag canary` → `gcloud run services update-traffic` to shift |
| **Kubernetes** | Canary deployment object + Istio/Nginx traffic splitting |

### Feature Flag Integration (if applicable)

If the PR includes a feature flag (noted in PR description):
- Deploy with flag **OFF** by default
- Full rollout at 100% traffic
- Flag can be turned ON separately after deployment verified
- Decouples deploy from release

```yaml
# .swarm-config.yml (per repo)
rollout:
  feature_flags:
    provider: "launchdarkly"    # or "custom" | "env-var" | "db-flag"
    default_state: "off"
```

### Output Format

```markdown
## Production Rollout — [COMPLETE/ROLLED-BACK/IN-PROGRESS]

### Rollout Progress
- [x] 5% canary — healthy (2m watch, error rate: 0.1%, p99: 120ms)
- [x] 25% — healthy (3m watch, error rate: 0.1%, p99: 125ms)
- [x] 50% — healthy (3m watch, error rate: 0.2%, p99: 118ms)
- [x] 100% — stable

### Health Baseline vs Current
| Metric | Baseline | Current | Status |
|--------|----------|---------|--------|
| Error rate | 0.1% | 0.2% | OK (within 5% threshold) |
| p99 latency | 120ms | 125ms | OK (within 50% threshold) |
| Health check | 200 | 200 | OK |

### Deployment
- **Version**: `abc1234-20260210`
- **Platform**: App Engine
- **Previous version**: `def5678-20260208` (retained for rollback)
- **Total rollout time**: 10m 45s

### Next: Triggering Agent 7 for verification
```

---

## Agent 7: Verify & Close Loop Agent

**Trigger**: Agent 6 production rollout completes at 100%
**Authority**: Autonomous — verification + Jira/notification updates
**Goal**: Confirm production health, close Jira ticket, notify stakeholders

### What It Does (3 phases)

#### Phase 1: Production Verification (immediate + delayed)

**Immediate checks** (right after 100% rollout):
- Hit all smoke test endpoints on production URL
- Verify health endpoint returns 200 with expected body
- Check key user flows still work (same checks from staging, now on prod)

**Delayed checks** (15 min and 60 min after rollout):
- Re-run the same health/smoke checks
- Compare error rate and latency vs pre-deployment baseline
- Check for any new error types in logs that didn't exist before
- If delayed check fails → trigger Agent 6 rollback, mark pipeline as FAILED

```yaml
# .swarm-config.yml (per repo)
verify:
  immediate_checks: true
  delayed_checks:
    - after_minutes: 15
    - after_minutes: 60
  baseline_comparison: true
  error_log_scan: true
```

#### Phase 2: Jira Ticket Update
- Move Jira ticket from TO REVIEW → **DONE** (move to TOP of Done column)
- Add final comment to Jira ticket with deployment summary:
  - What was deployed (version, commit SHA)
  - When deployed
  - Link to PR
  - Link to deployment logs
  - Link to monitoring dashboard
  - All agent verdicts summary (Agent 1-7 results)

#### Phase 3: Notifications & Reporting
- Post deployment summary to notification channel (Slack/email/webhook)
- Update PR with final "deployed to production" comment and lock the PR
- If the change had a feature flag → remind team to enable with a follow-up task
- Record deployment metrics for swarm dashboard:
  - Total pipeline duration (PR created → production verified)
  - Time per agent
  - Number of retries/failures
  - Coverage achieved

### Output Format (final PR comment + Jira comment)

```markdown
## Deployment Complete — VERIFIED

### Production Health
| Check | Immediate | +15 min | +60 min |
|-------|-----------|---------|---------|
| Health endpoint | 200 OK | 200 OK | 200 OK |
| Error rate | 0.2% (baseline: 0.1%) | 0.15% | 0.12% |
| p99 latency | 125ms (baseline: 120ms) | 118ms | 115ms |
| Homepage | 200 (320ms) | 200 (310ms) | 200 (305ms) |

### Pipeline Summary
| Agent | Verdict | Duration |
|-------|---------|----------|
| 1. Code Review | PASS | 1m 20s |
| 2. Architecture | SKIPPED | — |
| 3. QA Validation | PASS | 3m 45s |
| 4. Merge | MERGED | 12s |
| 5. Build & Deploy | SUCCESS | 3m 46s |
| 6. Prod Rollout | COMPLETE | 10m 45s |
| 7. Verify & Close | VERIFIED | 60m (delayed checks) |

### Total pipeline: PR → Production in 19m 48s (+ 60m verification tail)

### Jira: AW-288 moved to DONE
### Version: abc1234-20260210 live on employee.awesomeree.com.my
```

### Failure at Verification Stage
If production verification fails (even after rollout succeeded):
1. Trigger Agent 6 rollback immediately
2. Move Jira ticket back to IN PROGRESS
3. Add comment: "Deployed but verification failed — rolled back. See logs."
4. Notify team with urgency flag

---

## Swarm Configuration Reference

All agent behavior is configurable per repo via `.swarm-config.yml` in the repo root.

```yaml
# .swarm-config.yml — Full reference

# Agent 1 & 2: Review settings
review:
  override_label_code: "ai-review-override"
  override_label_arch: "ai-arch-override"
  arch_review_threshold_lines: 300

# Agent 3: QA settings
qa:
  coverage_threshold: 80
  coverage_target: changed        # "changed" | "all"
  skip_coverage_for:
    - "*.config.*"
    - "migrations/*"
    - "scripts/*"
  generate_tests: true
  test_quality_audit: true

# Agent 4: Merge settings
merge:
  strategy: squash                # "squash" | "rebase" | "merge-commit"
  delete_branch_after: true
  require_linear_history: true

# Agent 5: Build & Deploy settings
build:
  command: "npm run build"
  artifact_store: "gcr"
  dockerfile: "Dockerfile"

deploy:
  staging:
    url: "https://staging.employee.awesomeree.com.my"
    health_endpoint: "/api/health"
    smoke_tests:
      - endpoint: "/"
        expect_status: 200
      - endpoint: "/api/health"
        expect_status: 200
        expect_body_contains: "ok"
  production:
    url: "https://employee.awesomeree.com.my"
    health_endpoint: "/api/health"

# Agent 6: Rollout settings
rollout:
  strategy: canary
  canary_steps: [5, 25, 50, 100]
  canary_watch_minutes: [2, 3, 3, 0]
  auto_rollback: true
  rollback_on:
    - error_rate_increase: 5%
    - latency_p99_increase: 50%
    - health_check_fail: true
    - crash_loop: true
  feature_flags:
    provider: "env-var"
    default_state: "off"

# Agent 7: Verification settings
verify:
  immediate_checks: true
  delayed_checks:
    - after_minutes: 15
    - after_minutes: 60
  baseline_comparison: true
  error_log_scan: true

# Notifications
notifications:
  channel: "slack"                # "slack" | "email" | "webhook"
  webhook_url: ""
  notify_on: ["failure", "rollback", "success"]
```

---

## Implementation Details (Live as of 2026-02-10)

### Repository
- **Repo**: `it-awesomeree/AWESOMEREE-WEB-APP`
- **PR**: #219 (`feat/cicd-swarm-pipeline`)
- **Branch**: `feat/cicd-swarm-pipeline`

### Workflow Files

| File | Agent |
|------|-------|
| `.github/workflows/swarm-agent-1-code-review.yml` | Agent 1: AI Code Review |
| `.github/workflows/swarm-agent-2-arch-review.yml` | Agent 2: Architecture Review |
| `.github/workflows/swarm-agent-3-qa.yml` | Agent 3: QA & Test Coverage + Auto-Merge |
| `.github/workflows/swarm-agent-4-merge.yml` | Agent 4: Merge Report |
| `.github/workflows/swarm-agent-5-build-deploy.yml` | Agent 5: Build & Deploy Staging |
| `.github/workflows/swarm-agent-6-prod-rollout.yml` | Agent 6: Production Canary Rollout |
| `.github/workflows/swarm-agent-7-verify.yml` | Agent 7: Post-Deploy Verification + Jira |
| `.github/workflows/swarm-verify-cron.yml` | Periodic health check (every 15 min) |

### Foundation Files

| File | Purpose |
|------|---------|
| `app/api/health/route.ts` | Health endpoint with DB connectivity check |
| `jest.config.ts` | Jest config with `next/jest`, 60% threshold |
| `jest.setup.ts` | `@testing-library/jest-dom` setup |
| `__tests__/health.test.ts` | Seed test for health endpoint |
| `.swarm-config.yml` | Swarm configuration (coverage: 60%) |
| `CLAUDE.md` | Repo context for Claude Code Action instances |

### GitHub Settings

- **Branch protection on `main`**: requires "AI Code Review" and "QA & Test Coverage" status checks
- **Auto-merge**: enabled (was already on)
- **Old workflows**: `deploy-prod.yml` and `claude-code-review.yml` still active — disable after swarm validation

### Secrets (GitHub Actions)

| Secret | Value | Set |
|--------|-------|-----|
| `JIRA_BASE_URL` | `https://awesomeree.atlassian.net` | Yes |
| `JIRA_EMAIL` | `agnes@awesomeree.com.my` | Yes |
| `JIRA_API_TOKEN` | Atlassian API token (agnes) | Yes |
| `CLAUDE_CODE_OAUTH_TOKEN` | Pre-existing | Yes |
| `GCP_SERVICE_ACCOUNT_KEY_PROD` | Pre-existing | Yes |
| `GCP_PROJECT_ID_PROD` | Pre-existing | Yes |
| All other deploy secrets | Pre-existing (DB, auth, Shopee, etc.) | Yes |

### Infrastructure

- **GCP Project**: `deeptest-449907`
- **Production**: `employee.awesomeree.com.my` (App Engine default service)
- **Staging**: `test-dot-deeptest-449907.appspot.com` (App Engine `test` service)
- **Canary steps**: 5% (2min) → 25% (3min) → 50% (3min) → 100%
- **Coverage threshold**: 60% (starting low, ratchet up over time)
