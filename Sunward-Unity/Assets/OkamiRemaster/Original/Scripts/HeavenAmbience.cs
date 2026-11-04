using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class HeavenAmbience:MonoBehaviour
    {
        void OnEnable(){var source=GetComponent<AudioSource>();if(source && source.clip)source.Play();}
        void OnDisable(){var source=GetComponent<AudioSource>();if(source)source.Stop();}
    }
}
