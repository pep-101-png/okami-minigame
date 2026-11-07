# Standalone 30-second Sunward cinematic

This exports a **separate MP4**. Nothing is installed into Unity and no trailer
playback, input shortcut or automation is added to the game.

The first delivered cinematic used original scene geometry, native animation
banks and original sounds rendered outside Unity. This follows that same native
asset approach, with an OpenGL rasterizer to render all 1,800 frames directly at
1920×1080 / 60 fps. No video motion interpolation is used.

The current saved Windflower scene, original farm props, native festival lantern
layout, CelestialGarden placement data, original PL00/PL0D wolves, WP2E/WP29
weapons, EM00 imps and EM11/WP19 Crimson Helm assembly supply the picture.
Camera movement, hit timing, staging and particle timing are cinematic direction.
It is **not a recording of Unity gameplay**, proof of live collision/AI, or a
recreation of the game's render pipeline. No generated or outside art/music is
used. Titles use the original logo and message-glyph atlas.

The edit includes a village introduction, walking, the farm and digging, night
lanterns and a spirit run, native rosary combat, a weapon showcase, the heavens,
Shiranui's transformation, Crimson Helm armour/skeletal forms, a charged native
lightning impact, victory, a moonlit howl and an ending title.

`native_renderer.py` imports the actual saved scene and native weighted rigs.
`director.py` supplies the shot choreography. `titles.py` draws native lettering.
`render.py` exports silent picture and a render receipt. `compose.py` mixes only
existing original-source project audio into a separate MP4, with level limiting
and music ducking for the howls. Source audio choices arriving during the task
remain a **separate pending game-update list**, held until the user says done.

Dependencies: Python with NumPy, Pillow, ModernGL and glcontext, EGL/llvmpipe,
and FFmpeg/ffprobe. The small extra modules were installed in the task workspace.
Run the renderer with `--preview` for every shot midpoint before a full export.
The final movie must be fully decoded and checked for 1,800 frames, 30 seconds,
60 fps, stereo audio and inspected using frames from the actual encoded output.
