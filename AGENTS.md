# Sunward Unity development workflow

Integration target: `sunward-minigame` in `pep-101-png/okami-minigame`.
Preserve the existing Unity game, wolf model/rig/animations and working Windows
Git syncing. Make focused changes and create PRs. The user's standing instruction
(22 October 2026) authorizes merging completed updates into sunward-minigame:
merge immediately when GitHub permits, or use supported GitHub auto-merge while
required checks finish. Do not leave ready PRs awaiting the user's manual merge.
Do not start/enable Windows tasks. Never rebuild/discard completed game work.

For each Unity game-development task:

1. Inspect the current branch/status and the latest matching GitHub release
   feedback on `sunward-unity-feedback`. Fetch it yourself with
   `tools/unity-automation/fetch_feedback.py`; if CLI metadata is forbidden, use
   the connected GitHub fetch tool to obtain the release's asset URL/SHA-256 and
   pass those to the helper. No user downloads/uploads/log copying are required.
2. Read `review-index.json`, Unity errors/validation and ALL 14 clip statuses.
   Inspect actual screenshots and MP4 sequences (extract frames with FFmpeg if
   needed). A file/technical success is not visual approval. Missing/unstarted
   clips are not passed clips. Match feedback to its exact source commit.
3. Implement the requested game change; check related code and visual/movement
   regressions. Fix capture/diagnostic failures that prevent meaningful inspection.
   Repeat available tests; compare fresh same-build recordings when available.
4. Use the existing Codex subscription workflow. Do not call paid OpenAI APIs,
   dispatch/enable the GitHub Actions Codex API receiver, add API keys or new paid
   services. Ordinary feedback release publishing may remain enabled.
5. Deliver through a PR and merge completed updates to the integration branch as
   authorized above. Existing PC sync can retrieve the merged source. Do not
   require the user to run PowerShell or the 14-video process; they will open Unity
   and play-test. Fetch already-published feedback yourself when available. Never
   claim new Unity rendering/motion was verified without actually retrieving and
   inspecting it. Report clearly what could not be verified on the user's PC.

This cloud workspace cannot run Windows Unity or control the user's PC unless
such access is explicitly available. Installed LocalAppData runner copies are not
updated by a source-code push. Do not pretend otherwise or ask the user to transfer
files that connector/network tools can retrieve. Report the exact remaining access
or post-merge validation limitation. This active subscription task can fetch and
review feedback; it cannot automatically wake a new chat while idle.
