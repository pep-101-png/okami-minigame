# Standalone wolf viewer on GitHub Pages

The existing `wolf-viewer/` project is the only source for this site. The
`wolf-viewer-pages` branch contains hosting configuration based on the accepted
`2ba1f2b` viewer. It does not include the unapproved neck study. No game project
is built or deployed.

Expected site: https://pep-101-png.github.io/okami-minigame/

Animation comparison: https://pep-101-png.github.io/okami-minigame/compare.html

These are destination addresses, not a claim that Pages has been enabled.

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

Do not merge this branch into the game to deploy it. Do not promote an
unapproved model merely to update the website. Keep the uncommitted neck repair
and other authoring drafts separate until their visual approval.

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
