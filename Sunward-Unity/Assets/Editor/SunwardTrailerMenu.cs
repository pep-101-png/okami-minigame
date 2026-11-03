#if UNITY_EDITOR
using UnityEditor;
using UnityEngine;
using Sunward.Editor.Automation;
namespace Sunward.Editor
{
    public static class SunwardTrailerMenu
    {
        [MenuItem("Sunward/Trailer/Preview 30 seconds")]
        public static void Preview(){Launch(false);}
        [MenuItem("Sunward/Trailer/Record 4K 60 fps")]
        public static void Record(){Launch(true);}
        static void Launch(bool record)
        {
            if(!EditorApplication.isPlaying){Debug.LogWarning("Enter Play Mode in Windflower, then choose Sunward > Trailer. The sequence protects your current save.");return;}
            var game=Object.FindFirstObjectByType<GameFlow>();if(!game)return;
            TrailerPlayback.Begin(game,record);
        }
    }
}
#endif
