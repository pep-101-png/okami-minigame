# Sunward Windows Git sync (disabled until reviewed)

Target repository root: `C:\Users\giuse\Documents\okami-minigame`
Unity project: `Sunward-Unity`; remote: `pep-101-png/okami-minigame`; branch: `sunward-minigame`.

Nothing in this change installs, enables, starts, commits, or pushes this service.
The development checkout is on `work`, not `main`; do not run the Windows service
against that branch. Scripts refuse every branch except `sunward-minigame`.

## Policy and limits

- Default Sync.ps1 is a preview: it fetches remote refs and reports the planned
  direction but does not stage, commit, push, download LFS contents, or check out files.
  Fetch updates Git metadata. Preview writes a local log and may create a pause marker.
- `-Apply` explicitly authorizes staging all nonignored repository changes,
  committing them, downloading fast-forward updates, and pushing to the named branch.
  Saved deletions, .meta files, scripts, and configuration are included. Unsaved editor
  buffers are not. Review secrets before enabling; .gitignore is not a secret scanner.
- Every cycle requires Unity to be closed (any Unity.exe blocks it), no Unity lockfile,
  and 120 seconds of stable file sizes and modification times. It polls every 30 seconds
  and limits auto commits to one per ten minutes. No changes means no new commit.
  These are conservative process/file checks, not an OS lock: keep Unity and other Git
  clients closed during a sync. A process can start between checks. Stop before editing
  with another Git client. A copied stale Temp/UnityLockfile also blocks syncing;
  remove a stale lock only after confirming Unity is closed.
- Clean remote-ahead state: fast-forward only, followed by `git lfs pull`.
  Local-ahead state: ordinary push, with explicit `git lfs push` first. Remote races
  produce a rejected push and pause. No force, reset, stash, rebase, history rewriting,
  merge-conflict resolution, or automatic conflict commits.
- Remote-ahead plus local edits, divergence, existing staging, interrupted Git
  operations, missing credentials, failed hooks/LFS, or any other error creates
  `%LOCALAPPDATA%\SunwardGitSync\PAUSED.txt` and exits. No automatic retry until reviewed.
  If staging/commit succeeds but a later step fails, those staged files or local
  commits remain for inspection. No rollback overwrites them.
- Binary Unity formats use LFS according to the root .gitattributes. The existing
  Idle_Natural.anim rule remains. .meta files and ordinary text scenes/scripts do not
  use LFS. A file >=50 MiB without an LFS rule pauses before staging; add a specific
  LFS rule manually after review. No size-dependent history migration occurs.
  New binary rules can cause previously ordinary Git assets to appear modified once
  LFS is configured: their stored representation becomes a pointer on the next add,
  while working-file bytes stay the same. Review that first staged set carefully;
  LFS bandwidth/storage charges may apply to your account.
- .gitignore excludes Library, Temp, Logs, Obj, UserSettings, builds, IDE caches and
  generated project files. Already tracked generated Unity directories cause a pause;
  ignores do not untrack existing files. Assets, Packages, ProjectSettings and .meta
  files remain eligible. Back up the repository independently; sync propagates deletions.
- A named mutex prevents concurrent service instances in the same Windows session.
  One Windows account and one checkout are supported. There is no cross-machine lock.
- Logs rotate at 5 MiB. The scheduled service executes an installed copy of Sync.ps1,
  not the remote-updated repository script. Reinstall explicitly to adopt script changes.

## Review and prerequisites

1. Review all files under tools/windows-sync plus .gitignore/.gitattributes.
   Install Git for Windows with Git LFS. Use Windows PowerShell 5.1 or newer.
   Configure your Git author name/email and authenticate to GitHub as an account
   with repository write access (Git Credential Manager or an existing SSH key).
   No credentials are stored by these scripts; scheduled execution cannot prompt.
2. Ensure these reviewed files are available in the Windows repository. They are
   uncommitted in the implementation workspace; no GitHub publication is implied.
   Close Unity. In a normal, non-administrator Windows PowerShell window:

   ```powershell
   Set-Location C:\Users\giuse\Documents\okami-minigame
   git branch --show-current
   git status --short --branch
   git remote -v
   ```

   Expected branch: sunward-minigame. If it differs, preserve/review local work,
   then switch manually. Neither installer nor service switches branches.
   Confirm origin names the exact intended GitHub repository. Resolve outstanding
   staging/conflicts and review all local changes before proceeding.
3. Install **disabled**, as your ordinary Windows user:

   ```powershell
   .\tools\windows-sync\Install.ps1
   Get-ScheduledTask -TaskName SunwardGitSync | Select-Object TaskName,State
   ```

   Expected State: Disabled. Installer configures Git LFS locally (including its
   pre-push hook), copies the runner to `%LOCALAPPDATA%\SunwardGitSync`, and registers
   a disabled per-user Task Scheduler task. No sync starts. It does not override
   existing hooks with --force. If execution policy blocks reviewed scripts, use
   your organization's permitted signing/unblocking process; no policy bypass is used.
   Registration permissions may depend on Windows policy; a failure is not success.

## Verify the first sync, before enabling the task

Keep Unity closed throughout. Start with preview:

```powershell
.\tools\windows-sync\Sync.ps1
.\tools\windows-sync\Status.ps1
```

Wait for the two-minute observation. The preview fetches the branch and reports
local/remote commit counts and whether changes exist. It exits without applying.
If it pauses, read PAUSED.txt. Manually reconcile dirty/remote-ahead or divergent
states before continuing; never erase work just to make the service run.

Before the first applied run, manually stage and inspect the intended baseline
(including these scripts/configuration and any binary normalization), then commit
it yourself. The service refuses an existing staged set. For example:

```powershell
git add --all
git diff --cached --stat
git diff --cached --name-status
# Inspect this set; remove unintended files from staging before committing.
git commit -m "Prepare reviewed Sunward Windows sync"
git lfs ls-files
```

Do not run add/commit blindly if you have unrelated work. An LFS listing alone is
not proof of full object availability. With a clean checkout and no divergence,
explicitly run one applied cycle (this can publish your reviewed local commits):

```powershell
.\tools\windows-sync\Sync.ps1 -Apply
git fetch origin sunward-minigame
git rev-parse HEAD origin/sunward-minigame
git status --short
git lfs fsck --objects HEAD
(Get-Item .\Sunward-Unity\Assets\Sunward\Generated\Animations\Idle_Natural.anim).Length
(Get-FileHash .\Sunward-Unity\Assets\Sunward\Generated\Animations\Idle_Natural.anim -Algorithm SHA256).Hash
```

Expected: identical HEAD/remote hashes, clean status, successful LFS verification,
Idle_Natural.anim length **159951318**, SHA-256
`ec366136a5252c2354ae11403097d4d43fb2e18d6ef0bc477c79e9fc36ca8375`.
If this previously existing animation is still a pointer on Windows, with a clean
checkout explicitly run `git lfs pull origin` and repeat the size/hash verification.
Do not create an animation edit to trigger retrieval.

Optional round-trip check before continuous operation: while Unity stays closed,
create a small `sync-smoke-test.txt` at repository root and run Sync.ps1 -Apply.
Check its commit/file on GitHub. Edit that test file on GitHub, run -Apply again,
and confirm the edit appears locally as a fast-forward. Delete the test file and
apply again after the ten-minute commit interval (or commit the deletion manually).
A fresh independent LFS-enabled clone is the strongest check that GitHub can serve
uploaded assets. No gameplay or Unity asset edits are needed for this test.

## Enable only after review and successful one-shot verification

```powershell
Enable-ScheduledTask -TaskName SunwardGitSync
Start-ScheduledTask -TaskName SunwardGitSync
.\tools\windows-sync\Status.ps1
```

The task starts at **your Windows sign-in**, including after reboot; it does not
run before login or while the machine is off. This preserves access to your normal
Git credentials without storing a Windows password. A true pre-login system
service is deliberately outside this setup. On resume from sleep, it continues its
checks; offline fetches pause for review instead of generating commits endlessly.

## Stop, resolve a pause, resume, uninstall

```powershell
.\tools\windows-sync\Stop.ps1
.\tools\windows-sync\Status.ps1
```

Stop disables future launches and creates a pause marker. A running cycle finishes
its current operation and exits at the next boundary; Stop does not kill an active
Git write/transfer. A foreground one-shot runner observes the same marker at its
next boundary. Inspect task state/logs before reopening Unity or running manual Git.

For a pause: read `%LOCALAPPDATA%\SunwardGitSync\PAUSED.txt`, inspect `git status`
and the log, fix the cause manually, finish/unstage prepared work, and ensure the
worker has exited. Only then remove that file:

```powershell
Remove-Item "$env:LOCALAPPDATA\SunwardGitSync\PAUSED.txt"
.\tools\windows-sync\Sync.ps1
# After review, repeat a one-shot -Apply or enable/start the task as above.
```

For reinstall/update, stop and wait for exit, then:

```powershell
Unregister-ScheduledTask -TaskName SunwardGitSync -Confirm:$false
.\tools\windows-sync\Install.ps1
```

It is disabled again. For uninstall, stop/wait/unregister; optionally remove the
SunwardGitSync local state directory after saving logs. Keep the repository's LFS
configuration and hooks: existing assets need them even without autosync.

## Recovering from the Git helper recursion bug

The original helper was named `Git` and invoked `& git`. PowerShell resolves command
names without regard to case and chooses functions before native applications, so
that call invoked the helper again until call depth overflowed. The helper is now
`Invoke-SunwardGit` and executes the absolute native application path resolved by
`Get-Command -Name git -CommandType Application`. Installer and status invocations
use application-only resolution too, bypassing aliases/functions named Git.

If only preview was run and no task was installed, no installation is needed to
retest this fix. After reviewing and applying the fix to your `sunward-minigame`
checkout, close Unity, inspect `git status` and the existing pause/log, then remove
only the old recursion pause and run preview again:

```powershell
Get-Content "$env:LOCALAPPDATA\SunwardGitSync\PAUSED.txt"
git status --short --branch
# Only after confirming the pause is the old call-depth error and local state is safe:
Remove-Item "$env:LOCALAPPDATA\SunwardGitSync\PAUSED.txt"
.\tools\windows-sync\Sync.ps1
```

Do not pass `-Apply`, install a task, or enable one for this retest. If preview now
reports missing LFS configuration, review `git lfs install --local` separately;
that configures Git LFS and its hook without registering/enabling a scheduled task.
Any new pause should be inspected rather than repeatedly clearing the marker.
If a task was previously installed, its copied runner must also be updated through
reviewed reinstall steps; changing the repository copy alone does not update it.

## Validation

Run the dependency-free regression test on Windows PowerShell 5.1 or PowerShell 7:

```powershell
.\tools\windows-sync\tests\Test-NativeGit.ps1
```

It parses all PowerShell scripts and loads only the actual helper and executable
resolution AST fragments. It never starts sync, installs a task, or accesses GitHub.
It uses an empty temporary directory (including spaces in its path), shadows Git
with functions/alias, checks native execution and argument boundaries, and checks
that native failures still throw and preserve the error preference.

The test passed on PowerShell 7.4.6 on Linux. Ignore/LFS attribute matching was
checked during initial implementation. Windows PowerShell 5.1, Task Scheduler and
Unity integration remain untested in this environment; the Windows first-run and
round-trip procedure above is required before enabling. The recursion fix leaves
branch checks, preview default, LFS, quiet-time/editor checks, mutex, fast-forward
only downloads, staged/conflict guards, pause handling, commit intervals, and
ordinary non-force pushes in place. This setup does not provide an atomic editor
lock; always keep Unity closed during applied cycles.
