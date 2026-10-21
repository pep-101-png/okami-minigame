# Real Windows feedback inspected — 21 October 2026 (Sydney)

Source: `86ed0ccf75b188036f78911df56d30b1e180583b`,
run `20261021T082129301Z-f00f54`.
[Release bundle](https://github.com/pep-101-png/okami-minigame/releases/download/sunward-unity-feedback/86ed0ccf75b188036f78911df56d30b1e180583b-20261021T082129301Z-f00f54.zip)
SHA-256: `0542d71d822e02fc5ebdd41ca3c49458c8c154cc49fd32e628400ce3e5d09199`.

Validation/preservation passed; screenshots and gameplay video remain incomplete.
The driver bound a GameFlow before the requested scene activated. It then failed
with `Gameplay scene/player disappeared` during the first warmup. `walk-side`
contains **0/120 frames**. Walk-front/rear-quarter, all three jogs, all three
sprints, jumping, transitions/turning, dodging, combat and gameplay-route clips
never started. No MP4 or numbered gameplay frame was in this upload.

Inspected all 11 actual screenshots in a contact sheet, with full-size inspection
of `gameplay-live-camera.png` and `amaterasu-side.png`:

- Wolf front/side and all four pose views show distant scenery, not a useful wolf
  close-up. Metadata camera distances are hundreds of metres. Fix diagnostic
  bounds/framing; do not infer anything about pose quality from these images.
- The live gameplay screenshot shows the existing white/red wolf by a building.
  A foreground roof obscures the legs/paws. This is a real gameplay-camera
  occlusion finding, requiring a future scoped camera improvement and fresh test.
- Architecture is visible in its dedicated view. The wide lighting view is
  obstructed by a large foreground rock. Vegetation was not captured according to
  the manifest; improve hierarchy-based target matching in capture diagnostics.
- River view is distant. No movement, foot sliding, animation blend, jump landing
  or combat quality can be assessed from this upload.

Implemented capture lifecycle/framing/reporting fixes; their new visual output
has **not** been rendered here. Fourteen synthetic clip encodes test the pipeline
only. The existing game assets, animations and gameplay systems are preserved.

## All 14 recordings audited

| Recording | Evidence in uploaded run |
|---|---|
| `walk-side` | 0/120 frames; failed during warmup |
| `walk-front` | Not started; no video or frame evidence |
| `walk-rear-quarter` | Not started; no video or frame evidence |
| `jog-side` | Not started; no video or frame evidence |
| `jog-front` | Not started; no video or frame evidence |
| `jog-rear-quarter` | Not started; no video or frame evidence |
| `sprint-side` | Not started; no video or frame evidence |
| `sprint-front` | Not started; no video or frame evidence |
| `sprint-rear-quarter` | Not started; no video or frame evidence |
| `jump-air-land-side` | Not started; no video or frame evidence |
| `gait-stop-turn-side` | Not started; no video or frame evidence |
| `dodge-directions-rear-quarter` | Not started; no video or frame evidence |
| `combat-light-heavy-charge-side` | Not started; no video or frame evidence |
| `windflower-gameplay-route` | Not started; no video or frame evidence |
