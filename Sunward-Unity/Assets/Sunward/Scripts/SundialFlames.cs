using UnityEngine;

namespace Sunward
{
    // A fixed pool of ribbons follows the disc's local plane and cannot leave
    // orphaned world-space trails when teleporting, resting or switching weapon.
    public sealed class SundialFlames : MonoBehaviour
    {
        const int Count = 7, Points = 24;
        readonly LineRenderer[] ribbons = new LineRenderer[Count];
        float clock;
        TrailRenderer sweepTrail;
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
                line.widthMultiplier = i % 2 == 0 ? .11f : .075f;
                line.widthCurve = new AnimationCurve(new Keyframe(0, .12f), new Keyframe(.25f, 1), new Keyframe(.7f, .5f), new Keyframe(1, 0));
                line.startColor = i % 3 == 0 ? new Color(1, .94f, .75f, .75f) : new Color(1, .50f, .16f, .80f);
                line.endColor = new Color(.95f, .25f, .10f, 0);
                line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                line.receiveShadows = false;
                ribbons[i] = line;
            }
            var trailObject = new GameObject("Sundial painted sweep");
            trailObject.transform.SetParent(transform, false);
            trailObject.transform.localPosition = Vector3.right * .48f;
            sweepTrail = trailObject.AddComponent<TrailRenderer>();
            sweepTrail.sharedMaterial = flameMaterial;
            sweepTrail.time = .16f;
            sweepTrail.minVertexDistance = .06f;
            sweepTrail.widthMultiplier = .13f;
            sweepTrail.startColor = new Color(1, .75f, .35f, .5f);
            sweepTrail.endColor = new Color(1, .35f, .1f, 0);
            sweepTrail.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            sweepTrail.receiveShadows = false;
            sweepTrail.emitting = false;
        }

        void OnEnable() { if (sweepTrail) sweepTrail.Clear(); }

        void OnDestroy()
        {
            if (flameMaterial) Destroy(flameMaterial);
        }

        void LateUpdate()
        {
            clock += Time.deltaTime;
            if (sweepTrail) sweepTrail.emitting = Intensity > .20f;
            for (int i = 0; i < Count; i++)
            {
                if (!ribbons[i]) continue;
                for (int j = 0; j < Points; j++)
                {
                    float u = j / (float)(Points - 1);
                    float a = clock * (i % 2 == 0 ? .30f : -.22f) + i * Mathf.PI * 2 / Count + u * (.45f + Intensity * .6f);
                    float radius = .46f + Mathf.Sin(u * Mathf.PI) * (.10f + Intensity * .15f) + Mathf.Sin(u * 7 + clock * 3 + i) * .018f * u;
                    ribbons[i].SetPosition(j, new Vector3(Mathf.Cos(a) * radius, Mathf.Sin(a) * radius, -.095f - u * (.42f + Intensity * .25f) + Mathf.Sin(u * 5 + clock * 2 + i) * .035f * u));
                }
            }
        }
    }
}
