/** Immutable historical assets. Inspection never writes a model or animation. */
export const recoveryCatalog={
 original:{label:'Original Sketchfab upload',file:'recovery/original/scene.gltf',note:'Untouched upload: painted skin plus an inverted black outline shell. Hide back faces reveals its original paint; disable it to reproduce the supplied double-sided rendering. No rig or clips.'},
 first:{label:'First colour & rig · 14 Oct',file:'models/recovery-first.glb',note:'First saved adaptation, before the later surface and facial rebuilds. Includes its original early eye/nose additions.'},
 art:{label:'Early art model · 14 Oct',file:'models/recovery-art.glb',note:'The rebuild retained the original black outline shell as skin, removed the painted head/body parts, closed the jaw and replaced fur. This is a major departure from the original.'},
 prehead:{label:'Before face narrowing · 16 Oct',file:'models/recovery-prehead.glb',note:'Smoothing and sculpted curls are present; the later narrowing/lengthening pass has not yet been applied.'},
 neck:{label:'Approved neck checkpoint',file:'models/neck-approved.glb',note:'Approved neck repair, with the earlier narrowed face. Preserved exactly.'},
 current:{label:'Current jaw & face review',file:'models/jaw-repair.glb',note:'The current review model, unchanged. Compare its forehead, eyes, muzzle and chin with the earlier foundations.'}
};
