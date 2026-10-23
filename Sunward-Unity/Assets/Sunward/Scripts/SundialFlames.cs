using UnityEngine;

namespace Sunward
{
    // A fixed pool of ribbons follows the disc's local plane and cannot leave
    // orphaned world-space trails when teleporting, resting or switching weapon.
    public sealed class SundialFlames : MonoBehaviour
    {
        const int Count = 10, Points = 24;
        readonly LineRenderer[] ribbons = new LineRenderer[Count];
        float clock;
        Material flameMaterial;
        public float Intensity { get; set; }
        public void Initialize(Material material)
        {
            // Retire flat flame cards only on the equipped instance. The
            // saved Sundial prefab and home display remain unchanged.
            foreach (var renderer in GetComponentsInChildren<MeshRenderer>())
                if (renderer.name == "Sundial-1108" || renderer.name == "Sundial-1109")
                    renderer.enabled = false;
            // Existing Calligraphic Energy is URP unlit, transparent and consumes
            // LineRenderer vertex colours/alpha. Give flames an untinted instance.
            flameMaterial = new Material(material);
            flameMaterial.name = "Sundial spectral light";
            flameMaterial.SetColor("_BaseColor", Color.white);
            if (flameMaterial.HasProperty("_Barrier")) flameMaterial.SetFloat("_Barrier", 0);
            for (int i = 0; i < Count; i++)
            {
                var go = new GameObject("Spectral flame ribbon " + i);
                go.transform.SetParent(transform, false);
                var line = go.AddComponent<LineRenderer>();
                line.sharedMaterial = flameMaterial;
                line.useWorldSpace = false;
                line.positionCount = Points;
                line.widthMultiplier = i % 2 == 0 ? .10f : .065f;
                line.widthCurve = new AnimationCurve(new Keyframe(0, .12f), new Keyframe(.25f, 1), new Keyframe(.7f, .5f), new Keyframe(1, 0));
                line.startColor = i % 3 == 0 ? new Color(.35f, .82f, 1, .8f) : new Color(1, .64f, .18f, .9f);
                line.endColor = i % 3 == 0 ? new Color(.1f, .5f, 1, 0) : new Color(.95f, .16f, .035f, 0);
                line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                line.receiveShadows = false;
                ribbons[i] = line;
            }
        }

        void OnDestroy()
        {
            if (flameMaterial) Destroy(flameMaterial);
        }

        void LateUpdate()
        {
            clock += Time.deltaTime;
            for (int i = 0; i < Count; i++)
            {
                if (!ribbons[i]) continue;
                for (int j = 0; j < Points; j++)
                {
                    float u = j / (float)(Points - 1);
                    float a = clock * (i % 2 == 0 ? 1.3f : -.95f) + i * Mathf.PI * 2 / Count + u * (.85f + Intensity * .9f);
                    float radius = .49f + u * (.31f + Intensity * .25f) + Mathf.Sin(u * 7 + clock * 3 + i) * .018f * u;
                    ribbons[i].SetPosition(j, new Vector3(Mathf.Cos(a) * radius, Mathf.Sin(a) * radius, -.18f - u * .10f + Mathf.Sin(u * 5 + clock * 2 + i) * .075f * u));
                }
            }
        }
    }
}
