# Solar ultimate and Eighth Wonder impact — 8 November 2026

The third-form U attack previously played a sleeping pose, grew a sun separately from the body, used a generic two-sound burst, and applied damage after returning control. Eighth Wonder's brush sword descended linearly over 0.6 seconds and used the generic heavy-impact cue. This update replaces that presentation while keeping the established third-form requirement, once-per-arena use, skip controls and Crimson Helm's separate phase transitions.

## Result

- Eighth Wonder accelerates down over **0.36 seconds**, then produces a brief 0.12 m camera shake, a dedicated louder original-audio impact mix, painted dust, twenty ballistic original rock fragments and an expanding shockwave. Its existing native wheel animation and model remain.
- The **6.8-second U cinematic** rises in a short spiral, turns and curls into the inspected compact portion of original player roll `pl00_017`. The original double-jump clips were inspected and rejected because they remain stretched. The actual native torso is pinned to the sun centre each frame; release unfolds back to the original idle, restores the exact player position/facing and returns the camera.
- Original sun artwork grows from warm orange to a bright gold-white core, with circling fire, rising spiral motes, an original ground seal and a charging point light. Camera direction favours the arena interior near its edge, obeys scene obstruction checks and pulls out toward the arena centre for the blast.
- At **4.65 seconds**, a large original-painted spiral burst combines with fire, three expanding shockwaves, varied smoke/dust and forty-eight flying rock fragments. Stronger camera shake decays without drift. Non-boss enemies take the hit during the flash, and their native falls continue using the cinematic clock. The camera holds on the result.
- Crimson Helm damage waits until this cinematic returns its camera, then advances only the current phase. This avoids two cinematic directors fighting for the camera and preserves all three phases. Cancellation does not fire the ultimate; skip fires it exactly once and restores control. Resetting a fight restores availability.
- Separate sword and ultimate WAVs layer **identified original recordings only**: native barrel-imp blast cue 203, the existing original heavy-impact recording and, for the sunburst, the original Solar Flare heavy fire recording. The finished mixes are peak-normalised to 0.90 without clipping. Original EVBC power-up voice remains, with a quiet original fire loop rising in pitch/gain during charging. All other existing cue bindings are conserved.

## Native art and adaptations

`provenance.json` records exact original DDS and source waveform hashes and every audio layer's gain, pitch and start time. The source paintings are `bafooon`, `sand_01`, `rcok_gray`, `kemuri_01`, `fire_02` and `circleLight`, plus previously recovered sun/fire/seal/ring sprites. Exported pixels are unchanged. Smoke/rock atlases use their actual 4x4 layouts. A soft carrier-edge shader fades the original sand/puff/burst boundaries; the original DDS images are not repainted. At most 185 painted quads are active in the captured blast, with reused meshes/materials disposed at the end.

These are Sunward cinematic/emission adapters using original art and audio. They do not claim to reconstruct the original exorcism-slip EST event interpreter, nor introduce external/generated artwork or recordings. The unused recovered `fire_02` export is retained with its source provenance; the active fire carriers use the already inspected whole original flame paintings.

## Review

`runtime.py` compiles the real NativeAmaterasu, ultimate, sword, enemy, camera, audio and painted-mesh drivers using explicit engine API doubles. It captures actual native bone poses, player positions, camera/lens output, effect vertices/UVs/colours, enemy health/defeat states and audio controls. `review.py` renders that output with original models/textures, matching alpha/additive blending and carrier fades. The separate **9.2-second, 1280x720, 30 fps MP4** shows the complete sword impact and ultimate, including scheduled impact/voice sounds and the changing charge loop. It stays outside Assets.

Inspected source roll/jump poses, charge/rise/release frames, encoded impact frames, all five enemies' falls, and isolated painted layers. Iterations tightened the curl, strengthened the hot core, varied plume radii/heights, faded rectangular sprite boundaries and used available audio headroom. Source fixtures cover 15/30/60/120 fps, exact sun centring, flash-time damage, once-per-fight use, skip/cancel, second-form rejection and faster sword contact. Existing awakening/combat/save and Crimson phase regressions also remain successful. `verify.py` checks original pixels/waveform identities, unchanged prior audio bindings, finite captures and single impact scheduling.

**Limits:** this is an offline render of actual C# driver output, not Unity Play Mode. It uses API doubles and a flat test floor, with approximate player/ground collisions. PC Unity scene obstructions, URP shader compilation, dynamic lighting/tendrils, rendering performance and subjective speaker/headphone mixing are not verified here. Latest published Unity feedback is still the 21 October source `aefd595771e933a3313ecb4170251764c94ab1e3`; all 14 clip statuses say `frames_captured_coverage_incomplete`. Its old combat video/report were inspected and do not validate this update. No Windows task or paid API was dispatched.

## Reproduce with existing caches

```
python tools/solar-ultimate/assets.py
python tools/spirit-charge-home/compile/check.py --dotnet /workspace/work/tundra-beads/dotnet/dotnet --dump-doubles /workspace/work/solar-ultimate/Doubles.cs
python tools/solar-ultimate/runtime.py
python tools/solar-ultimate/verify.py
PYTHONPATH=/workspace/work/trailer30/deps python tools/solar-ultimate/review.py
```
