using System;
using System.Collections;
using UnityEngine;

namespace Sunward
{
    public sealed class PaintedEffects : MonoBehaviour
    {
        public Material ink;
        [Serializable] sealed class Appearance { public string resource; public Vector3 offset, scale; }
        [Serializable] sealed class OriginalFeedback { public Appearance ring, warning, projectile; }
        OriginalFeedback originals;
        void Load()
        {
            if (originals != null) return;
            var data = Resources.Load<TextAsset>("Okami/Feedback");
            if (!data) throw new InvalidOperationException("Original Okami feedback assets are missing.");
            originals = JsonUtility.FromJson<OriginalFeedback>(data.text);
        }
        public LineRenderer Ring(Vector3 center, Color color, float radius, float life = .65f)
        {
            if (!MeshSafety.Finite(center) || !float.IsFinite(radius) || radius <= 0)
                throw new InvalidOperationException("Invalid original feedback placement.");
            Load();
            var source = color.r > color.g * 1.2f ? originals.warning : originals.ring;
            var go = new GameObject("Original Okami feedback · " + source.resource);
            go.transform.position = center + Vector3.up * .035f;
            go.transform.localScale = new Vector3(radius, 1, radius);
            go.AddComponent<Sunward.Remaster.OriginalVisual>().Load(source.resource, source.offset, source.scale);
            // Existing combat owns a LineRenderer handle. Keep that lifetime
            // handle without drawing invented line or ring geometry.
            var handle = go.AddComponent<LineRenderer>();
            handle.enabled = false; handle.positionCount = 0;
            StartCoroutine(Lifetime(handle, life));
            return handle;
        }
        IEnumerator Lifetime(LineRenderer handle, float life)
        {
            float elapsed = 0;
            var renderers = handle.GetComponentsInChildren<Renderer>();
            while (handle && elapsed < life)
            {
                elapsed += Time.deltaTime;
                float alpha = float.IsPositiveInfinity(life) ? 1 : Mathf.Clamp01(1 - elapsed / life);
                foreach (var renderer in renderers)
                    if (renderer && renderer != handle && renderer.sharedMaterial && renderer.sharedMaterial.HasProperty("_Color"))
                        renderer.sharedMaterial.SetColor("_Color", new Color(1, 1, 1, alpha));
                yield return null;
            }
            if (handle) Destroy(handle.gameObject);
        }
        public GameObject Boundary(Vector3 center, float radius) => Ring(center, Color.red, radius, float.PositiveInfinity).gameObject;
        public void AttachProjectile(GameObject owner)
        {
            Load();
            owner.AddComponent<Sunward.Remaster.OriginalVisual>().Load(originals.projectile.resource, originals.projectile.offset, originals.projectile.scale);
        }
        public void SundialOrbit(Vector3 center, bool heavy)
        {
            // wp24's native skeletal appearance remains active. The original
            // EST/SEQ dispatcher is unfinished; do not substitute a custom orbit.
        }
        public void Impact(Vector3 point, Color color) { Ring(point, color, .7f, .22f); }
    }
}
