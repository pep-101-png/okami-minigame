using UnityEngine;
namespace Sunward
{
    // Separate preferences; changing volume never touches the player's save.
    public static class GameAudioSettings
    {
        static bool loaded;static float master=1,music=1,effects=1;
        public static float Master{get{Load();return master;}}
        public static float Music{get{Load();return music;}}
        public static float Effects{get{Load();return effects;}}
        public static void Load(){if(loaded)return;loaded=true;master=Mathf.Clamp01(PlayerPrefs.GetFloat("Sunward.Audio.Master",1));music=Mathf.Clamp01(PlayerPrefs.GetFloat("Sunward.Audio.Music",1));effects=Mathf.Clamp01(PlayerPrefs.GetFloat("Sunward.Audio.Effects",1));AudioListener.volume=master;}
        public static void Set(int channel,float value){Load();value=Mathf.Clamp01(value);if(channel==0){master=value;AudioListener.volume=value;}else if(channel==1)music=value;else effects=value;PlayerPrefs.SetFloat(channel==0?"Sunward.Audio.Master":channel==1?"Sunward.Audio.Music":"Sunward.Audio.Effects",value);}
        public static void Save(){PlayerPrefs.Save();}
    }
}
