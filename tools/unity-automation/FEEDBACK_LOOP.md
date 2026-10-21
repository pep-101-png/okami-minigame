# Sunward visual feedback with the existing Codex subscription

No OpenAI API key, API billing or additional paid service is required. The legacy
API-based Actions repair job is hard-disabled; `DispatchRepair=true` in an old
local config is ignored by the updated publisher. The disabled workflow also
prevents an old installed publisher from triggering API work after this PR merges.
`Configure-Feedback.ps1 -EnablePublishing` configures ordinary release publishing
only; `-EnableRepairDispatch` now fails with an explanatory message.

## Normal development cycle

An active Codex game-development task reads the repository and the existing
`sunward-unity-feedback` release, downloads its matching ZIP itself, verifies its
SHA-256 and source commit, and inspects logs, screenshots and video frames.
`AGENTS.md` makes this workflow part of future Sunward tasks. The helper
`fetch_feedback.py` produces `review-index.json` listing every screenshot and all
14 expected recordings, including missing/not-started/partial cases. It supports
Windows ZIP separators safely and refuses traversal, symlinks and hash/identity
mismatches. It does not upload anything, start a task or call a model API.

Typical cloud retrieval:

```text
python tools/unity-automation/fetch_feedback.py --output /tmp/SunwardFeedback
```

If CLI GitHub API calls are forbidden in a cloud environment, Codex uses its
connected GitHub fetch tool on the existing release endpoint to obtain each
asset's `browser_download_url` and SHA-256 `digest`, then passes them directly:

```text
python tools/unity-automation/fetch_feedback.py --asset-url <browser_download_url> --sha256 <digest-without-sha256-prefix> --output /tmp/SunwardFeedback
```

This is a tool-to-tool transfer performed by Codex, not a request for the user to
download, upload or copy logs. The current repair retrieved and inspected the
existing Windows upload in exactly this way. No new authentication was needed for
the connected GitHub tool/direct release download. Existing Windows release
publishing still uses its already-configured GitHub CLI login.

Codex implements a focused fix and relevant tests, creates a PR to
`sunward-minigame`, and preserves completed game work and the existing sync system.
After review/merge, existing syncing retrieves the new source on the PC, and the
existing validator can publish the next real Unity test. Codex can then retrieve
those artifacts in an active task. Technical capture checks never certify correct
appearance, paw contact, movement, blending or combat animation.

## Recording fix and complete clip accounting

The real upload at commit `86ed0ccf75b188036f78911df56d30b1e180583b`, run
`20261021T082129301Z-f00f54`, contains zero `walk-side` frames and no other gameplay
clips. Its true error is `Gameplay scene/player disappeared`, before recording.
The synchronous scene reload was followed immediately by looking up the old
GameFlow; that reference was destroyed when the new scene activated.

The driver now waits for the asynchronous Windflower load to finish, verifies the
active scene path, waits another frame for Start, and binds only GameFlow objects
from that new scene. Every campaign declares all 14 clips before starting. A
clip-local error preserves its error/frames and proceeds to the next fresh scene;
timeouts and campaign storage limits still stop safely. Manifests are replaced
atomically. Missing clips never count as a successful campaign. Available partial
footage may be encoded/inspected but remains explicitly partial and unreviewed.

Static wolf screenshots now calculate bounds from baked posed geometry instead
of imported animation envelopes; this corrects the diagnostic framing code without
modifying the model, scene, controller or animation assets. Fresh real Unity
screenshots are still required to verify the resulting framing. The actual
roof/paw occlusion seen in the gameplay screenshot is recorded for a subsequent
gameplay-camera improvement, not silently changed in this capture repair.

## Tests and current limits

- `Test-Video.ps1`: C# 5-compatible scene readiness gate, identical 14-clip recipe
  names across Unity/PowerShell, the real zero-frame failure shape, full 14-name
  synthetic FFmpeg/ffprobe encoding, missing clip, partial clip and existing media
  safety cases. These synthetic clips are not Amaterasu footage.
- `Test-Feedback.ps1`: ordinary upload/retry/redaction and **zero** API dispatches,
  even with a legacy `DispatchRepair=true` config.
- `test_fetch_feedback.py`: Windows ZIP normalization, safe extraction, actual
  upload metadata shape and all-14 review accounting without model APIs.
- Existing runner cancellation/validation tests remain applicable.

This environment has no Unity editor and no remote-control channel to the user's
Windows PC. It cannot itself rerun Unity, inspect unrecorded movement, refresh
LocalAppData script copies or activate local tooling. The core driver/framing C#
fixes are inside the synced Unity project and do not require manually transferring
assets or replacing the installed runner to take effect after merge. Enhanced
PowerShell reporting/subscription guards require that installed copy to receive
the corresponding module changes; this cloud cannot perform that PC-side update.
No scheduled task has been enabled, started or changed here.

An active subscription task can retrieve available feedback, but this chat cannot
wake itself while idle or independently merge its PR to trigger another integrated
Windows build. Keep those exact limits distinct from completed code/tests and
from actual visual verification. Never substitute a static pose for motion review.
