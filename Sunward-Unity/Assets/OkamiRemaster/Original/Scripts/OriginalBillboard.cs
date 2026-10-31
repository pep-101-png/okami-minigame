using UnityEngine;
using UnityEngine.Rendering;

namespace Sunward.Remaster
{
    // Rendering adapter for the original thin tree/bamboo paintings. The
    // preserved world/collision root never rotates with this visual anchor.
    public sealed class OriginalBillboard : MonoBehaviour
    {
        Camera view;
        void OnEnable() { RenderPipelineManager.beginCameraRendering += BeforeCamera; }
        void OnDisable() { RenderPipelineManager.beginCameraRendering -= BeforeCamera; }
        void BeforeCamera(ScriptableRenderContext context, Camera camera) { Face(camera); }
        void LateUpdate()
        {
            if (!view) view = Camera.main;
            if (!view) return;
            Face(view);
        }
        void Face(Camera camera)
        {
            if (!camera) return;
            Vector3 direction = camera.transform.position - transform.position;
            direction.y = 0;
            if (direction.sqrMagnitude > .001f) transform.rotation = Quaternion.LookRotation(direction);
        }
    }
}
