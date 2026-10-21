# Sunward Unity development workflow

Integration target: `sunward-minigame` in `pep-101-png/okami-minigame`.
Preserve the existing Unity game, wolf model/rig/animations and working Windows
Git syncing. Make focused changes and create review PRs; do not auto-merge or
start/enable Windows tasks. Never rebuild/discard completed game work.

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
5. Deliver through a PR to the integration branch. Existing PC sync can retrieve
   the merged source and the existing validator can test it. Never claim new Unity
   rendering/motion was verified without actually retrieving and inspecting it.

This cloud workspace cannot run Windows Unity or control the user's PC unless
such access is explicitly available. Installed LocalAppData runner copies are not
updated by a source-code push. Do not pretend otherwise or ask the user to transfer
files that connector/network tools can retrieve. Report the exact remaining access
or post-merge validation limitation. This active subscription task can fetch and
review feedback; it cannot automatically wake a new chat while idle.
