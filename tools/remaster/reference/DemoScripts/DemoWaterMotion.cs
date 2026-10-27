using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace SunwardVillageDemo
{
    public sealed class DemoWaterMotion : MonoBehaviour
    {
        public static DemoWaterMotion Active { get; private set; }
        public bool Animated = true;
        readonly List<Renderer> surfaces = new List<Renderer>();
        readonly List<GameObject> pairedFoam = new List<GameObject>();
        MaterialPropertyBlock properties;
        float phase;
        static readonly int FlowTime = Shader.PropertyToID("_FlowTime");
        static readonly int PhaseOffset = Shader.PropertyToID("_FoamPhaseOffset");
        void Awake() { Active = this; properties = new MaterialPropertyBlock(); }
        void Start() { CollectSurfaces(); }
        void CollectSurfaces()
        {
            surfaces.Clear();
            foreach (Renderer renderer in FindObjectsByType<Renderer>(FindObjectsSortMode.None))
            {
                Material material = renderer.sharedMaterial;
                if (material == null || !material.HasProperty("_WaterMode") || material.GetFloat("_WaterMode") < .5f) continue;
                surfaces.Add(renderer); renderer.shadowCastingMode = ShadowCastingMode.Off;
                if (!material.HasProperty("_FoamMode") || material.GetFloat("_FoamMode") < .5f) continue;
                MeshFilter original = renderer.GetComponent<MeshFilter>();
                if (original == null || original.sharedMesh == null) continue;
                // Share geometry and artwork: two cross-fading phases, not another stored mesh.
                Bounds bounds = original.sharedMesh.bounds; bounds.Expand(new Vector3(1.4f, .12f, 1.4f)); original.sharedMesh.bounds = bounds;
                GameObject copy = new GameObject(renderer.name + " paired travelling foam");
                copy.transform.SetParent(renderer.transform.parent, false);
                copy.transform.localPosition = renderer.transform.localPosition;
                copy.transform.localRotation = renderer.transform.localRotation;
                copy.transform.localScale = renderer.transform.localScale;
                copy.AddComponent<MeshFilter>().sharedMesh = original.sharedMesh;
                MeshRenderer other = copy.AddComponent<MeshRenderer>(); other.sharedMaterial = material; other.shadowCastingMode = ShadowCastingMode.Off;
                properties.Clear(); properties.SetFloat(PhaseOffset, .5f); other.SetPropertyBlock(properties);
                surfaces.Add(other); pairedFoam.Add(copy);
            }
            Debug.Log("Continuous painted water ready: " + surfaces.Count + " layers, " + pairedFoam.Count + " paired foam batches. Pause affects every layer.");
        }
        void Update()
        {
            if (Animated) phase += Time.deltaTime;
            foreach (Renderer renderer in surfaces)
            {
                if (renderer == null) continue;
                renderer.GetPropertyBlock(properties); properties.SetFloat(FlowTime, phase); renderer.SetPropertyBlock(properties);
            }
        }
        void OnDestroy()
        {
            foreach (GameObject copy in pairedFoam) if (copy != null) Destroy(copy);
            pairedFoam.Clear(); if (Active == this) Active = null;
        }
    }
}
