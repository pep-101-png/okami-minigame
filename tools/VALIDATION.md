The smoke suite runs against an already running server. It does not change game files or saved game data. Gameplay state is manipulated only inside its isolated browser tab to reach otherwise slow regression scenarios.

For a production run, first run `npm run build` and start `npm run preview -- --port 4173`. In another terminal:

```sh
npm run test:smoke
```

Playwright is a pinned development dependency. On machines without system Chromium, run `npx playwright install chromium` once. `PLAYWRIGHT_MODULE` can point at an existing external Playwright installation; `CHROMIUM_PATH` can select a browser executable. Set `SMOKE_BASE_URL` to test another address (the default is `http://127.0.0.1:4173`). Chromium is launched with software WebGL for cloud hosts without a hardware GPU.

The suite writes a unique timestamped directory under the ignored `.test-artifacts` directory. `SMOKE_OUT_DIR` changes that parent directory; cloud validation uses `/workspace/validation-artifacts`. Each directory contains `report.json` and actual browser screenshots. The report includes UTC start and finish times, the Sydney finish time, durations, measured bone/clip data, attack timings, and failures. No screenshot is a substitute for subjective art review.

Coverage includes local skinned-model loading, useful scene pixels, finite articulated animation samples, real keyboard movement and action events, a live-frame animation check, collisions, NPC dialogue, village enemy leashing, buffered three-hit combat, directional hit geometry, enemy attack damage, defeat/restart, victory/continued exploration, flower collection/shrine offering, sound mute, resizing, useful startup errors when WebGL is blocked, and absence of JavaScript errors or external asset requests.

The harness pauses requestAnimationFrame only while applying reproducible fixed steps through the actual Game.update loop. It resumes real rendering for visual evidence and live-frame checks. The only intentional browser error occurs in a separate tab where WebGL is deliberately disabled.

## Wolf feature suite

Run `npm run test:wolf` against the same production preview. It tests physical left/right mouse holds and releases, charged damage, heavy arcs, moving while charging, dodge cancellation, bark direction/cover/cooldown, finite nonzero vocal PCM buffers, running foliage lifetime, jump rise/fall and aerial recovery, face meshes, silk geometry and the new authored clips. Reports are saved with a `wolf-` prefix.
