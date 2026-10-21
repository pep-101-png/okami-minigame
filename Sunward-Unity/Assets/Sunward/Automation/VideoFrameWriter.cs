#if UNITY_EDITOR
using UnityEngine;
namespace Sunward.Editor.Automation
{
    // Runs after the existing motor, Animator, root correction, OrbitCamera and camera brain.
    [DefaultExecutionOrder(32000)]
    public sealed class VideoFrameWriter : MonoBehaviour
    {
        public VideoCaptureDriver driver;
        void LateUpdate() { if (driver) driver.CaptureFrame(); }
    }
}

#endif
