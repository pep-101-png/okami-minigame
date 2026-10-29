using UnityEngine;

namespace Sunward
{
    public sealed class ValleyAudio : MonoBehaviour
    {
        public AudioClip bark, growl, hit, howl;
        AudioSource effects;
        void Awake()
        {
            effects = gameObject.AddComponent<AudioSource>();
            effects.volume = .40f;
            effects.spatialBlend = 0;
            // Original PL voices; cue assignments are a Sunward adaptation,
            // not a recovered original sound-event table.
            bark = Resources.Load<AudioClip>("Okami/Audio/Amaterasu-0");
            growl = Resources.Load<AudioClip>("Okami/Audio/Amaterasu-1");
            hit = Resources.Load<AudioClip>("Okami/Audio/Amaterasu-2");
            howl = null;
            // Missing authentic music, ambience and combat cues stay silent.
        }
        public void Cue(string id)
        {
            AudioClip clip = id == "bark" ? bark : id == "hurt" ? hit : id == "growl" ? growl : null;
            if (clip) effects.PlayOneShot(clip);
        }
    }
}
