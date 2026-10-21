# Issue #9: Windows feedback → GitHub → Codex repair PR

This implementation is **not end-to-end verified**. No Windows task, GitHub
receiver variable or API secret was enabled by this PR. Gameplay and sync are
unchanged. The current conversation does not receive background events: the
receiver starts a separate, supported [OpenAI Codex Action](https://github.com/openai/codex-action)
run using the OpenAI API, with its own billing/authentication.

## Capture cancellation

The report in Issue #9 proves validation succeeded and capture cancelled on an
additional PID; it does not identify that PID's parent/birth time. The code fixes
two reproducible false-positive cases: a process exits between `Get-Process` and
the CIM snapshot, and a previously verified owned worker loses its parent record.
Ownership now survives parent exit only when the exact PID **and creation time**
were already proven to belong to this runner. PID reuse invalidates that proof.
A worker hint, matching executable or batch flag alone never grants ownership.
Unknown live ancestry, query failures and genuinely separate editors still stop
capture. Historical records are memory-only and reset for each validation job.

The bounded `process-diagnostics.json` history records sanitized process/parent
IDs, creation times, executable names/paths, batch/worker hints and the precise
ancestry decision. It includes known-worker observations before cancellation.
Raw command lines are never included. Marker cancellation includes the exact
marker path in `runner-stage.log`. These are published even for a deferred job.
The exact cause of Windows PID 6572 remains unverified until its real diagnostics
are captured; neither tests nor the existing log establish that it was owned.

## One-time owner setup (requires authentication/permission)

1. Review/merge this PR into `sunward-minigame`. Do not enable a task yet.
2. Install GitHub CLI and run `gh auth login` **as the Windows user that runs the
   validation task**. The credential must read this repository and write release
   contents; repair dispatch also needs permission to create repository dispatch
   events (fine-grained PAT: repository Contents read/write). For private repos,
   classic CLI authentication generally uses `repo`. Do not paste/store credentials
   in config, source, issues or reports. Scheduled tasks with another user do not
   inherit this login. Revocation/SSO expiry will leave a retryable local outbox.
3. GitHub `repository_dispatch` workflows must exist on the repository's **default
   branch**. The default branch was verified as `sunward-minigame` for this PR,
   so merging this PR installs the receiver in the required location. No `main`
   change or separate bootstrap PR is currently needed. If the owner later changes
   the default branch, copy only the reviewed workflow there through normal review.
   The workflow always checks out `sunward-minigame`.
4. In repository Settings → Secrets and variables → Actions, add the secret
   `OPENAI_API_KEY` and, only after review, variable
   `SUNWARD_CODEX_REPAIR_ENABLED=true`. This authorizes paid API use. Also allow
   GitHub Actions to create pull requests. The workflow requests Contents and
   Pull requests write permissions for its post-agent publication step. No secret
   is put in the dispatch payload. The pinned official Codex Action checks the
   triggering user's repository write access and uses its Linux sandbox with
   `drop-sudo`. Do not weaken this to `unsafe` or permit all triggering users.
5. After the installed-code update below, explicitly opt into delivery:

   ```powershell
   .\tools\unity-automation\Configure-Feedback.ps1 -EnablePublishing -EnableRepairDispatch
   ```

   This verifies CLI authentication, creates the dedicated prerelease if absent,
   and sets `PublishReports=true` and `DispatchRepair=true` in the existing local
   config. It does **not** start/enable any task or change the DISABLED marker.
   Omit `-EnableRepairDispatch` for unattended publication without API repair runs.
   Config defaults remain false. Review the destination repository's visibility:
   release artifacts inherit its access. Redaction is defense in depth; don't log
   credentials in Unity. Never use a token that cannot safely upload diagnostics.

## Update the installed Windows runner (user action; no automatic activation)

The scheduled task executes LocalAppData copies, not repository scripts. While
validation is disabled and all its owned processes have exited:

```powershell
# Explicit user action; this does not touch SunwardGitSync.
.\tools\unity-automation\Disable.ps1
$state = Join-Path $env:LOCALAPPDATA 'SunwardUnityAutomation'
# Verify Status.ps1 and process state; wait for the owned runner to exit first.
.\tools\unity-automation\Status.ps1
# After it has stopped, update just the runner modules; retain config/reports.
'Run.ps1','Common.ps1','Video.ps1','Feedback.ps1' | ForEach-Object {
    Copy-Item (Join-Path '.\tools\unity-automation' $_) (Join-Path $state $_)
}
Get-FileHash .\tools\unity-automation\Common.ps1
Get-FileHash (Join-Path $state 'Common.ps1')
```

No task re-registration is necessary for this module update. First installation
still uses `Install.ps1`, which registers only a **disabled** validation task.
Do not update while the runner is active. Review local config before deliberately
removing DISABLED for a one-shot manual test. Leave the task itself disabled.
`Configure-Feedback.ps1` is run from the repository and need not be installed.

## Delivery and repair behavior

- Every completed attempt, including failed/deferred capture, writes a report and
  per-run stage log, and automatically publishes when configured. Explicitly
  allowlisted text is redacted for common GitHub/OpenAI token, authorization and
  secret-assignment patterns. Configs, save data, environments, licensing files,
  source, Library and raw process command lines are excluded. Redaction cannot
  prove arbitrary application logs contain no secrets; inspect the first bundle.
- Named logs/JSON/XML, up to 20 MiB screenshots and existing bounded gameplay
  media go into an immutable `<commit>-<runId>.zip` and summary on prerelease
  `sunward-unity-feedback`. Total uncompressed bundle limit is 140 MiB; text
  logs above 4 MiB are explicitly marked and bounded to their head/tail (full logs
  remain local); structured text above 16 MiB fails delivery explicitly. Existing MP4/frame
  fallback budgets still apply. No media is committed to Git. No remote retention
  deletion is automatic; the owner controls release retention.
- `delivery.json` tracks partial upload/dispatch completion. Watch mode retries
  delivery without rerunning Unity, with 1–60 minute backoff, at most ten attempts,
  three deliveries per poll and the newest 100 run directories. Explicit
  `Publish.ps1 -RunDirectory ...` retries older/exhausted entries. Deferred Unity
  attempts themselves have a five-minute backoff and a three-attempt-per-commit
  cap; `-Retry`/a new commit explicitly permits another attempt.
- After upload, a `repository_dispatch` contains only commit/run identity, asset
  name and SHA-256. HTTP success means **submitted**, not proof of receiver/API
  success. Check the Actions run. The workflow is inert until the owner opt-in.
- The receiver downloads the matching release asset, verifies SHA/identity and
  extraction budgets/path safety, and checks the integration HEAD still matches.
  Stale reports skip repair. MP4s, screenshots, logs, contact sheets and telemetry
  are present locally for Codex; up to 16 contact sheets are attached as images.
  The prompt requires real frame inspection before judging motion and treats all
  logs/artifacts as untrusted data. An existing `video-reuse.json` reference is
  reported as requiring its earlier bundle, never substituted silently.
- One deterministic repair branch per source commit prevents duplicate repair PRs.
  Code changes are gated to automation directories (20 files / 300 KB patch caps).
  The receiver gate executes the committed version after Codex, checks the target
  hasn't advanced, then pushes a new branch and creates a **draft** PR. The agent
  does not receive GH_TOKEN. Out-of-scope changes fail publication. No changes
  means diagnosis in Actions logs, not an invented fix or empty PR.
- Workflow checkout/feedback is ephemeral; source media/LFS need not be downloaded
  to propose an automation repair. The default workflow timeout bounds API work.
  If a branch was pushed but PR creation failed, create/recover that draft PR from
  the branch; deduplication intentionally prevents an automatic second API spend.

## End-to-end acceptance test still required

1. Run `tests/Test-Cancellation.ps1`, `tests/Test-Feedback.ps1`,
   `tests/Test-Automation.ps1`, and `tests/Test-Video.ps1` in fresh Windows
   PowerShell 5.1 processes. Python receiver tests run with
   `python -m unittest discover -s tools/unity-automation/tests -p test_feedback_receiver.py`.
2. With the task still disabled, perform one deliberate manual `Run.ps1 -Retry`
   using the installed modules/config and existing Unity 6000.6.6f1 setup. Confirm
   owned workers don't cancel; if a live unknown process stops the run, inspect
   its published ancestry decisions rather than assuming it is safe to ignore.

   ```powershell
   $state = Join-Path $env:LOCALAPPDATA 'SunwardUnityAutomation'
   # Deliberate manual smoke test only; scheduled task stays disabled.
   Remove-Item (Join-Path $state 'DISABLED') -ErrorAction SilentlyContinue
   try {
       & (Join-Path $state 'Run.ps1') `
           -Repository 'C:\Users\giuse\Documents\okami-minigame' `
           -ConfigPath (Join-Path $state 'config.json') -Retry
   } finally {
       'Reviewing manual feedback test; task remains disabled.' |
           Set-Content (Join-Path $state 'DISABLED')
   }
   ```

3. Verify the real release ZIP has report/logs, sanitized process diagnostics,
   screenshots and short MP4s (or explicit capture/encoding failures). Verify the
   receipt hash and ensure no credentials or configs are in the actual ZIP.
4. Verify the `Sunward feedback repair` Actions run received that exact commit,
   actually invoked Codex, inspected available media and produced either a gated
   draft repair PR or an honest diagnosis. Check API/workflow failures directly.
5. Review/merge a safe repair yourself. With your existing sync and an explicitly
   user-enabled validation task, the new integrated commit can then be validated
   and publish the next feedback iteration. No component auto-merges PRs or
   starts a task. Human review is intentionally the integration gate.

Local tests exercise mocked Windows process tables, real native watchdogs, real
ZIP packaging, mocked GitHub requests and a real temporary Git remote with a
synthetic agent patch. They do not exercise Windows Unity, actual credentials,
GitHub event routing, the Codex API or visual quality. The full loop must not be
called working until the real acceptance test passes.
