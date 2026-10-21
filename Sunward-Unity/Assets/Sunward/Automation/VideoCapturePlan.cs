#if UNITY_EDITOR
using System;
using System.Collections.Generic;
namespace Sunward.Editor.Automation
{
    // Shared with Windows PowerShell 5.1 Add-Type: keep this file compatible with C# 5.
    // Pure capture specification: testable without Unity. No animation/runtime overrides.
    [Serializable] public sealed class VideoClipSpec
    {
        public string name, category, angle;
        public int seconds;
        public string[] expectedStates;
    }
    public struct VideoCommand
    {
        public float worldX, worldZ;
        public bool walk, sprint, jump, dodge, light, heavy;
    }
    public static class VideoCapturePlan
    {
        public const int Version = 1;
        public static List<VideoClipSpec> Build()
        {
            var clips = new List<VideoClipSpec>();
            foreach (string gait in new[] { "walk", "jog", "sprint" })
                foreach (string angle in new[] { "side", "front", "rear-quarter" })
                    clips.Add(new VideoClipSpec { name = gait + "-" + angle, category = gait, angle = angle, seconds = 4,
                        expectedStates = new[] { gait == "walk" ? "Walk_" : gait == "jog" ? "Jog_" : "Sprint_" } });
            clips.Add(new VideoClipSpec { name = "jump-air-land-side", category = "jump", angle = "side", seconds = 5, expectedStates = new[] { "Jump_", "Air_Fall", "Land_" } });
            clips.Add(new VideoClipSpec { name = "gait-stop-turn-side", category = "transitions", angle = "side", seconds = 7, expectedStates = new[] { "Idle_Natural", "Walk_", "Jog_", "Sprint_", "_Turn_" } });
            clips.Add(new VideoClipSpec { name = "dodge-directions-rear-quarter", category = "dodge", angle = "rear-quarter", seconds = 5, expectedStates = new[] { "Dodge_" } });
            clips.Add(new VideoClipSpec { name = "combat-light-heavy-charge-side", category = "combat", angle = "side", seconds = 9, expectedStates = new[] { "Thrust", "Sweep", "Finish", "HeavyArc", "HeavyReturn", "ChargedHeavy" } });
            clips.Add(new VideoClipSpec { name = "windflower-gameplay-route", category = "gameplay", angle = "gameplay", seconds = 8, expectedStates = new[] { "Walk_", "Jog_" } });
            return clips;
        }
        static bool Pulse(int frame, float seconds, int fps, int width = 2)
        {
            return frame >= (int)Math.Round(seconds * fps) && frame < (int)Math.Round(seconds * fps) + width;
        }
        public static VideoCommand Command(VideoClipSpec clip, int frame, int fps)
        {
            float t = frame / (float)fps;
            var c = new VideoCommand();
            if (clip.category == "walk" || clip.category == "jog" || clip.category == "sprint") {
                if (t >= .5f && t < 3.5f) { c.worldZ = 1; c.walk = clip.category == "walk"; c.sprint = clip.category == "sprint"; }
            } else if (clip.category == "jump") {
                if (t < 2.4f) c.worldZ = 1;
                c.jump = Pulse(frame,1,fps) || Pulse(frame,3,fps);
            } else if (clip.category == "transitions") {
                if (t >= 1 && t < 5) c.worldZ = 1;
                c.walk = t >= 1 && t < 2.5f; c.sprint = t >= 4 && t < 5;
                if (t >= 5 && t < 6) c.worldX = 1;
            } else if (clip.category == "dodge") {
                if (t >= .5f && t < 1.8f) c.worldZ = 1;
                if (t >= 2.4f && t < 2.8f) c.worldX = -1;
                if (t >= 3.5f && t < 3.9f) c.worldZ = -1;
                c.dodge = Pulse(frame,1,fps) || Pulse(frame,2.4f,fps) || Pulse(frame,3.5f,fps);
            } else if (clip.category == "combat") {
                if (t < 2.5f) c.worldZ = 1;
                c.light = Pulse(frame,3,fps) || Pulse(frame,3.36f,fps) || Pulse(frame,3.86f,fps);
                c.heavy = Pulse(frame,5,fps) || Pulse(frame,5.56f,fps) || (t >= 7 && t < 7.5f);
            } else if (clip.category == "gameplay") {
                if (t < 5) c.worldZ = 1;
                if (t >= 5 && t < 7) c.worldX = 1;
                c.walk = t < 2; c.sprint = t >= 6 && t < 7;
            }
            return c;
        }
    }
}

#endif
