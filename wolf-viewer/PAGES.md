# Standalone wolf viewer on GitHub Pages

The existing `wolf-viewer/` project is the only source for this site. The
`wolf-viewer-pages` branch contains the existing viewer and its hosting configuration.
The neck repair is approved and saved as an immutable checkpoint; the current
head reconstruction is an explicitly requested browser review study. It is not
yet an accepted head. No game project is built or deployed.

Expected site: https://pep-101-png.github.io/okami-minigame/

Head comparison: https://pep-101-png.github.io/okami-minigame/compare.html?study=head

Approved neck: https://pep-101-png.github.io/okami-minigame/?version=neck-approved

Original baseline: https://pep-101-png.github.io/okami-minigame/?version=baseline-2ba1f2b

The initial hosted viewer was verified in a real browser after deployment attempt 3.
Verify each subsequent deployed revision before reporting it live.

## One-time repository setting

1. Open https://github.com/pep-101-png/okami-minigame/settings/pages.
2. Under **Build and deployment**, set **Source** to **GitHub Actions**.
3. Open the **Deploy wolf viewer** run for the `wolf-viewer-pages` branch in
   **Actions**. If its initial run failed because Pages was disabled, use
   **Re-run all jobs** after enabling Pages.
4. Wait for both the build and deploy jobs to succeed, then open the site above.

If Actions is disabled for the repository, enable GitHub Actions under
**Settings → Actions → General**. Repository admin access is needed for settings.

## Updating the same hosted viewer

Push approved changes to `wolf-viewer/` on `wolf-viewer-pages`. The workflow
installs the locked viewer dependencies, runs its existing Vite production build,
and deploys only `wolf-viewer/dist`. The public URL stays the same; no ZIP
download or Windows setup is required for visitors. Source changes can be
reviewed separately from model/animation commits before they reach this branch.

Do not merge this branch into the game to deploy it. Keep review models clearly labelled until their visual approval. Preserve the
approved neck checkpoint and original baseline when publishing a new head study.

## Paths and preserved behaviour

Vite emits relative asset URLs (`base: './'`). The model and metadata loaders
already use `import.meta.env.BASE_URL`. The comparison iframes use relative
viewer URLs, so both pages work below `/okami-minigame/` and in local previews.
The GLB contains its existing textures and clips; runtime watercolor shaders,
tail/fur/face motion, orbit/zoom controls, animation selection, play/pause,
restart, playback rate and scrubbing are the existing viewer implementation.

Local production check (no game build):

```sh
npm ci --prefix wolf-viewer
npm run build --prefix wolf-viewer
```

The workflow does not run Blender, regenerate models, or alter animation data.
Keep the model attribution and licence included in the existing public files.
