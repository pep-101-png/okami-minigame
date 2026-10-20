using UnityEngine;

namespace Sunward
{
    public sealed class ValleyAudio : MonoBehaviour
    {
        public AudioClip bark, growl, hit, howl;
        AudioSource effects, ambience;
        AudioClip jump, land, attack, impact, dash, collect, wind, heavy, heavyImpact, flame, flameImpact;
        void Awake()
        {
            effects = gameObject.AddComponent<AudioSource>();
            effects.volume = .40f;
            effects.spatialBlend = 0;
            ambience = gameObject.AddComponent<AudioSource>();
            ambience.volume = .065f;
            ambience.loop = true;
            jump = Tone(520, .18f, .4f);
            land = Tone(90, .16f, 2);
            attack = Tone(240, .15f, 1.5f);
            impact = Tone(120, .18f, 3);
            heavy = Tone(135, .30f, 1.6f);
            heavyImpact = Tone(65, .30f, 3.2f);
            flame = Tone(360, .25f, 1.8f);
            flameImpact = Tone(190, .25f, 2.8f);
            dash = Tone(600, .14f, 1);
            collect = Tone(880, .26f, .2f);
            wind = Tone(160, 8, 1);
            ambience.clip = wind;
            ambience.Play();
        }

        static AudioClip Tone(float f, float duration, float noise)
        {
            const int rate = 22050;
            int n = (int)(duration * rate);
            var samples = new float[n];
            uint seed = 13;
            for (int i = 0; i < n; i++)
            {
                seed = 1664525 * seed + 1013904223;
                float t = i / (float)rate, envelope = Mathf.Sin(Mathf.PI * i / n);
                samples[i] = (Mathf.Sin(2 * Mathf.PI * f * t) * .20f + ((seed >> 8) / 16777216f - .5f) * noise * .3f) * envelope;
            }

            var c = AudioClip.Create("Legal generated placeholder", n, 1, rate, false);
            c.SetData(samples, 0);
            return c;
        }

        public void Cue(string id)
        {
            AudioClip clip = id == "heavy" ? heavy : id == "heavy-impact" ? heavyImpact : id == "flame" ? flame : id == "flame-impact" ? flameImpact : id == "bark" ? bark : id == "hurt" ? hit : id == "growl" ? growl : id == "jump" ? jump : id == "land" ? land : id == "attack" ? attack : id == "impact" ? impact : id == "dash" ? dash : collect;
            if (clip)
                effects.PlayOneShot(clip);
        }
    }
}
