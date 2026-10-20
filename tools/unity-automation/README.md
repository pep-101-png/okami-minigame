# Sunward local Unity validation and feedback

Integration branch: `sunward-minigame`; Unity **6000.6.6f1**, URP **17.6.0**.
Live project: `C:\Users\giuse\Documents\okami-minigame\Sunward-Unity`.
This change does not install/start/enable anything and does not merge its PR.
**Existing `SunwardGitSync` scripts, configuration, task and mutex are unchanged.**

## Architecture and safety

Codex PR → user merges to sunward-minigame → existing sync fetches/pulls → validation
runner observes a stable clean committed HEAD matching the cached origin ref →
immutable local snapshot → isolated Unity validation/rendering → local reports →
optional GitHub reporting-release assets → a later Codex task reads those assets.

The runner never uses Git add/commit/push/reset/stash/merge/checkout/fetch/pull or
LFS downloads against the live repository. Git archive and cached LFS reads are
read-only operations against a pinned commit, so they do not compete with sync for
index writes. The existing sync daemon holds its mutex throughout its life; trying
to take that mutex would starve this service. Instead, Unity opens a **different
project directory**, never the live checkout. Existing sync also already waits
while any Unity editor (including the owned batch editor) is running.

Before starting it checks: branch/origin identity, clean worktree, HEAD==cached
origin/sunward-minigame, no Git operation/lock, no Git process, no Unity process,
no live project lock, then a stable commit for at least 30 seconds. The final state
is checked again after snapshot creation. It does not independently contact GitHub
to prove the cached origin ref is current; that remains the existing sync's job.

- State lives in `%LOCALAPPDATA%\SunwardUnityAutomation`, outside all source files.
- A separate `Local\SunwardUnityAutomation` mutex allows one validator per user session.
- Snapshots contain only the committed `Sunward-Unity` tree, not the browser game.
- LFS pointers are replaced **only in snapshots** using already-cached objects;
  SHA-256 and size are verified. Missing objects fail clearly; no hidden fetch.
- A private process environment suppresses existing automatic scene/animation
  migrations and redirects SaveStore to a run-specific save directory. Normal Unity
  use without these variables is unchanged. No builders/repair commands are invoked.
- Scene/model/native-animation bytes and metas are hashed before/after successful
  validation/captures. Changes mark preservation failure; live project is untouched.
- No interactive user editor is closed. If another Unity opens while a job runs,
  only the owned batch process tree is cancelled. There is an unavoidable race
  between an OS process check and the user launching Unity; isolation protects the
  live project even in that interval. There is no system-wide editor launch lock.
- Disable requests cancel the owned process, not a live project or sync. Interrupted
  snapshot operations may be incomplete and remain for inspection.
- Each commit is attempted once, including failed validations. User/editor activity
  cancellations are deferred locally (not uploaded) and retried when safe. New commits trigger
  new runs. `-Retry` explicitly reruns the current commit. Failed uploads can be
  retried separately without rerunning Unity. Reporting never commits to any branch.
- The installed PowerShell runner is a reviewed copy, not remotely executed from
  an updating worktree. Update it explicitly after reviewing future automation PRs.
- Local working edits deliberately postpone testing. Once sync commits/uploads
  them, their resulting clean synced commit becomes eligible.

## What runs

`BatchValidation.Run` opens **Windflower**, checks loaded-scene and prefab missing
scripts/references, serialized asset GUIDs, dependencies, material/custom-shader
errors, 74 named rig bones and 47 imported/native clips. It reuses:

- `SunwardValidation.Validate`
- `WolfClipProcessor.ValidateScale` (including existing transition samples)
- `WindflowerDiagnostics.Connections` and `BoundsAudit`
- `VillageOverhaulValidation.Validate`

Compilation is considered reached only when Unity executes the reporting method.
A compiler/import/license/startup failure that prevents entry produces no success
report, and the outer runner records failure and preserves the editor log.

If the project already includes `com.unity.test-framework`, the runner executes
available **EditMode** tests and checks NUnit XML. No package is installed or added.
The current project does not declare that package: tests are explicitly reported
`skipped_framework_not_installed`, while the project validators still execute.
No arbitrary PlayMode test suite is enabled. A separate controlled Play Mode camera
capture exercises startup with isolated save data and input disabled.

`SceneCapture.Run` renders the actual Windflower scene, not a viewer/prototype:
front/side Amaterasu, four fixed-quarter clip samples (idle, walk, sprint, thrust),
architecture, vegetation/terrain, river/pond, a wide lighting/shadow view, and the
saved gameplay-camera view. Framing uses stable hierarchy ordering and bounds.
Heuristic target selection can miss or poorly frame an object; that is reported,
not converted into visual approval. Camera/pose metadata accompanies each image.

`GameplayCapture.Run` enters the real scene in Play Mode, uses a fresh isolated
save, disables input **inside that Unity process only**, advances 30 fixed-time
frames and requests a render from the actual gameplay camera. This is a startup/
camera smoke check, not movement/combat/UI validation. Neither camera-render method
captures screen-space UI. Capture JSON labels static versus live-camera images.

Captures request a graphics-capable URP renderer (no `-nographics` for render stages).
Null devices, unsupported SRP render requests, almost-uniform images, missing
subjects or failed stages are reported as unavailable/incomplete. Pixel-identical
results across GPUs, shader-time effects and Unity drivers are **not guaranteed**.
PNG existence/nonuniformity only establishes output; it does not establish that
materials, shadows, anatomy or animation look correct. Codex/user image inspection
and a Windows playtest are still required.

If batch rendering fails, optional `AllowVisibleCapture=true` permits a separate
non-batch editor launch on the isolated snapshot for the static capture stage.
It defaults **false** to avoid unexpected desktop windows. That fallback also
requires graphics hardware/an interactive Windows session and can still fail.

Optional `BuildWindowsPlayer=true` builds the Windflower scene to a run-specific
output directory and writes `build-summary.json`. Default is false: no accidental
hourly player builds. Windows Build Support must already be installed. It never
invokes the existing build command that could rebuild a missing scene. Build
binaries and save files stay local; they are not in the report upload.

## Deadlines, storage and recovery

Each native Git operation has a 120-second deadline; uploads 300 seconds; each Unity
stage defaults to 3600 seconds (`UnityTimeoutSeconds`). Both output pipes are drained
asynchronously and a heartbeat is logged every ten seconds. A timed-out/cancelled
child is stopped with its own process tree; other editors/processes are untouched.
Editor logs stream to individual files while stages run. Import/extraction/hash
work on local disks is logged by stage; a kernel-level stalled filesystem call
cannot be interrupted safely by PowerShell itself.

A first isolated import can be slow: it uses local Unity package caches/network for
existing manifest dependencies, an activated editor license, several GB of disk
and substantial RAM. It does not download new external asset packs. Snapshots do
not reuse the live Library or lock files. Allow tens of GB of free disk for imports.
Completed successful snapshots are removed by default; reports remain. Failed
snapshots remain for diagnosis. Cleanup checks the exact owned path/marker and
refuses recursive deletion when links/junctions or another editor need review.
`KeepSuccessfulSnapshots=true` retains successful snapshots too.

If validation fails, inspect `last-run.json`, the run's `report.json`,
`validation.json`, and `*-editor.log`. Fix source in a separate reviewed commit,
never edit the live project through the validator. A new synced commit retries
automatically. For an infrastructure repair on the same commit, use `-Retry`.
No source rollback, conflict resolution or Git lock cleanup is automatic.

If Unity is open, Git is busy, local changes exist, or refs differ, the runner waits.
A copied stale UnityLockfile also blocks it; confirm no editor owns the live project
before addressing that lock manually. Never remove locks to force parallel access.

## Windows installation (explicit user actions only)

1. Review and merge the automation PR into **sunward-minigame**. Let existing sync
   deliver it. Close Unity for the smoke test. Keep Git for Windows/LFS and the exact
   Unity editor/license already installed/activated. Run an ordinary non-admin
   Windows PowerShell 5.1 session. Do not bypass organization execution policies.

2. Test scripts, then install a **disabled** validation task (sync is unaffected):

   ```powershell
   cd C:\Users\giuse\Documents\okami-minigame
   .\tools\unity-automation\tests\Test-Automation.ps1
   .\tools\unity-automation\Install.ps1
   $state = "$env:LOCALAPPDATA\SunwardUnityAutomation"
   notepad "$state\config.json"
   ```

   Default editor discovery checks standard Unity Hub and standalone install paths
   and PATH. For a custom Hub location set `UnityEditor` to its exact `Unity.exe`
   path. Version metadata and project version must match 6000.6.6f1. Keep
   `PublishReports=false` for the first local run, visible fallback false, builds
   false. Other defaults include screenshots and controlled Play Mode camera capture.

3. Run one manual validation **while the task remains disabled**:

   ```powershell
   Remove-Item "$state\DISABLED"
   & "$state\Run.ps1" -Retry
   .\tools\unity-automation\Status.ps1
   ```

   This can take a full import plus several editor launches. Inspect local JSON,
   logs and screenshots. Confirm editor version, validation statuses, explicit test
   skips, preservation result, and actual image contents. Confirm your real source
   checkout/save has not changed. Graphics or Unity API problems here are Windows
   integration failures to report; this PR was not Unity-compiled/rendered in cloud.

4. Optional automatic GitHub feedback requires GitHub CLI installed and authenticated
   **as the same Windows account that runs the task**. No token is stored in config:

   ```powershell
   gh auth login
   gh auth status
   gh release create sunward-unity-feedback --repo pep-101-png/okami-minigame --target sunward-minigame --prerelease --latest=false --title "Sunward local Unity feedback" --notes "Generated local validation reports only. Not a game release."
   ```

   Create this dedicated reporting release only once. It creates one reporting tag,
   not a source-branch commit. Review that logs/screenshots may include local paths
   before setting `PublishReports=true` in local config. Existing release assets
   use unique commit/run IDs; retries skip existing names, never clobber assets.
   No release, upload or authentication is performed by this PR/cloud session.

   Test delivery for an existing run without rerunning Unity:

   ```powershell
   .\tools\unity-automation\Publish.ps1 -RunDirectory "<runDirectory from last-run.json>"
   ```

5. **Only after the smoke test and review**, enable explicitly:

   ```powershell
   .\tools\unity-automation\Enable.ps1 -StartNow
   .\tools\unity-automation\Status.ps1
   ```

   The per-user `SunwardUnityValidation` task starts at Windows sign-in (not before
   login or while the PC is off). No administrator/system service or stored Windows
   password is required. It must not use a second self-hosted Actions runner.

## Disable, update, uninstall

```powershell
.\tools\unity-automation\Disable.ps1
.\tools\unity-automation\Status.ps1
```

Disable writes the stop marker and disables only this new task. The owned child
cancels at its watchdog check; inspect logs/task state before manual investigation.
It never invokes Stop-ScheduledTask on SunwardGitSync or kills an interactive editor.

To update installed PowerShell code: disable, wait for exit, explicitly unregister
`SunwardUnityValidation`, rerun Install.ps1, review preserved local config, smoke
test again. It is installed disabled again. Never use automatic self-updating task
scripts. To uninstall, disable/wait/unregister; remove this service's LocalAppData
folder only after saving needed reports. Do not uninstall Git LFS or sync.

No automatic remote retention/deletion policy is enabled. Periodically remove old
feedback assets deliberately if repository storage needs it. Failed local snapshots
may be deleted manually after diagnosis and after confirming no editor uses them.

## How Codex uses feedback

Report location: GitHub → Releases → **Sunward local Unity feedback**
(`sunward-unity-feedback`, a prerelease), assets `<commit>-<runId>.zip` and
`<commit>-<runId>-report.json`. The ZIP includes editor logs, validator JSON,
EditMode XML if available, capture metadata, screenshots, and optional build summary.
It excludes project source, Library, caches, executable builds and save data.

A subsequent Codex task can use authenticated GitHub tools/CLI to list/download:

```text
gh release view sunward-unity-feedback --repo pep-101-png/okami-minigame --json assets
gh release download sunward-unity-feedback --repo pep-101-png/okami-minigame --pattern "<commit>-<runId>*" --dir <scratch directory>
```

Codex must match the report's exact commit, inspect failures and actual PNGs, then
propose a separate fix/review PR. PNGs are not automatically judged beautiful or
correct. Uploads do not start a new Codex task, approve artwork, merge PRs, resolve
conflicts or self-authorize new development. The user must start/continue a Codex
task to consume feedback; this chat cannot run indefinitely or react while idle.

Actions artifacts were not chosen because a cloud workflow cannot read local
Windows files without another installed runner/service. A dedicated release uses
the requested reporting mechanism without adding a privileged Actions listener to
your PC. If publication fails, reports remain local; use Publish.ps1 after fixing
auth/network/release setup. That does not retrigger a Unity validation loop.

## Verification performed here

PowerShell 7.4.6 on Linux: parsing all scripts; isolated local Git/LFS snapshots;
clean/dirty/ref guards; exact LFS hash materialization with no live-file writes;
missing object rejection; protected hash failures; mocked Unity report success,
startup failure and unsupported graphics; explicit skipped test status; repeated
commit checks; native quoting, dual-pipe pressure, timeouts, cancellation; mocked
idempotent report publication. New C# files were Roslyn syntax-parsed only.

Not verified here: Unity compilation/API compatibility, licensing/import behavior,
existing validator outcomes, Play Mode behavior, actual PNG rendering/quality,
Windows PowerShell 5.1, Task Scheduler, Windows taskkill, gh authentication/upload
from your PC, and player builds. These require your existing Windows Unity setup.
No rendered screenshot or successful Unity validation is claimed by this PR.
