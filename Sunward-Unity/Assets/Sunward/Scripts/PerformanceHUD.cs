using UnityEngine;
using UnityEngine.InputSystem;
using Unity.Profiling;

namespace Sunward
{
    public sealed class PerformanceHUD : MonoBehaviour
    {
        ProfilerRecorder mainThread, drawCalls;
        float elapsed, fps;
        int frames;
        bool visible;
        void OnEnable()
        {
            mainThread = ProfilerRecorder.StartNew(ProfilerCategory.Internal, "Main Thread", 15);
            drawCalls = ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count", 15);
        }

        void OnDisable()
        {
            mainThread.Dispose();
            drawCalls.Dispose();
        }

        void Update()
        {
            if (Keyboard.current != null && Keyboard.current.f3Key.wasPressedThisFrame)
                visible = !visible;
            elapsed += Time.unscaledDeltaTime;
            frames++;
            if (elapsed >= .5f)
            {
                fps = frames / elapsed;
                frames = 0;
                elapsed = 0;
            }
        }

        void OnGUI()
        {
            if (!visible)
                return;
            GUI.Box(new Rect(20, 165, 320, 80), "Runtime profiler · F3\n" + fps.ToString("0.0") + " FPS · CPU " + (mainThread.Valid ? (mainThread.LastValue / 1000000f).ToString("0.0") + " ms" : "n/a") + "\nDraw calls " + (drawCalls.Valid ? drawCalls.LastValue.ToString() : "n/a"));
        }
    }
}
