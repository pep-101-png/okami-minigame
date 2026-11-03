# Desktop village play-test repair

Baseline: b451c8bcf7750befbf1bfdf0b323f24931222765, including removal of the unintended in-game trailer. The update changes the existing Windflower gameplay scene, not a demo scene.

- Selected PL00-41 bark is unchanged; playback gain .24 -> .75. The user's clarification was weak playback in-game, not a wrong source sound. No other audio levels changed.
- Thirteen festival pickups remain; the race returns to 55 seconds. Reward prices remain 9/12/15.
- Native atlas measurement and GUI clipping share glyph metrics. Controls wrap within the scroll interior; stat descriptions are short per-rank explanations. Reflector portraits use the native idle visible groups and a face-on projection instead of including giant attack-effect meshes.
- Disabled ten obsolete broad exterior colliders around Ammy's house. A static MeshCollider uses the visible exterior mesh itself. Door and detached room systems remain unchanged.
- Farm shelter roofs now use real r107 __LY32__3F_Yane geometry with separate original timber posts. Previous sentakuba geometry was a washing platform, not a roof. Pen layout and crop soil are preserved.
- Spa guest keeps the original seated pose and receives a stronger native hm05_027 arm gesture with a short rest and blend envelope. Eight disconnected held-prop pieces are omitted; hands and body remain. This is a seated adaptation using recovered original motions, not an identified original bathing clip.
- Final wave waits three unpaused seconds before the existing shaft-collapse cinematic. Cancels safely on leaving, a new trial or death.
- Boss root settles to the actual lower-floor triangles after scaling and movement. No arbitrary visual-only offset or damage rule changes.
- Waterfall direction is derived from the source's top/bottom geometry. The lip moves to Z36 and entry starts at Z35.25, within the existing Z37.5 movement clamp. The existing automatic fall, portal transfer and garden return remain. Water layers have per-layer native UV direction, and the portal lamp is at the portal instead of world origin.
- No in-game trailer code is restored. The standalone video is a separate unfinished deliverable.

Validation: selected whole runtime scripts compile with .NET engine doubles (0 errors); 13 festival, 23 village, 36 garden/collapse/boss-grounding, 336 actual native-glyph layout, and 915 boss/director checks pass. Additional 71 focused source/resource checks, 2862 scene/resource/metadata, 250 native garden checks, 120 door checks, 371 farm/audio/source checks and 131 C# syntax trees pass. Asset metadata and download ZIP integrity are checked separately when packaged.

Limit: there is no Unity Editor here. These checks do not verify actual Unity physics, animation rendering, shader compilation or audible mix. Offline portrait/source previews are not screenshots of the running game. User play-testing remains necessary, especially doorway collision, waterfall descent, moving spa arms and third-phase grounding.

The patch ZIP contains only changed Assets and .meta files. Review tools and this document are excluded. This Desktop lineage remains a stacked draft PR; merging its entire history into the obsolete integration project would risk overwriting the user's working game.
