# Shiranui ribbon geometry and material correction

Addresses the supplied in-game screenshot of six overbright angular strips
crossing the head/shoulders. This update changes the effect itself, not the photo.

- Original ES4A/ES4B are preserved. Derived copies keep their original texture,
  skeleton, UVs and winding, with edge subdivision, slimmer cross sections and
  smooth native-chain skin weights. The coarse five-segment bends are smoothed.
- Original negative-Z blunt roots and extreme tips fade away. Six mounts follow
  the actual torso bone along the flanks/rear ribs, not the dorsal weapon socket.
- Right-hand motion is mirrored so both sides stream outward and backward rather
  than piling into one fan. The original seamless wind loops still animate them.
- A dedicated ribbon shader uses bounded pigment and ordinary transparency rather
  than stacking six HDR additive whites. Native RGB fade intensity is transferred
  to alpha, preventing dark vertices from becoming opaque black strips. The older
  shared spirit material is unchanged, preserving other game effects.
- The effect remains exclusive to the third/full-power ES3A form. Second-form
  visibility and all audio, weapon, garden and progression behavior are preserved.

Validation: actual C# compiles with explicit engine doubles, zero errors. Existing
form/skip/visibility/motion tests passed. Native derived-geometry checks test valid
streams/weights, subdivision, source preservation, root fade and visible-vertex
head clearance across idle, locomotion, charge and howl poses with both mirrored
wind sides. Twenty offline native-asset views cover close overhead, overhead, top,
front and rear at four motion times, using the new alpha and blend rules and the
actual player motion bank. These are offline diagnostics, not Unity screenshots.

No current Unity import, shader compilation or Play Mode validation is claimed.
Available automated PC feedback predates this update; the user's screenshot is
the direct evidence of the problem being corrected. No outside media are used.
