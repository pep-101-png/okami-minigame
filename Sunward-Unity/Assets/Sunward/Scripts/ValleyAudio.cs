using UnityEngine;

namespace Sunward
{
    public sealed class ValleyAudio : MonoBehaviour
    {
        public AudioClip bark, growl, hit, howl;
        AudioSource effects, ambience;
        AudioClip jump, land, attack, impact, dash, collect, wind, heavy, heavyImpact, flame, flameImpact, bell;
        void Awake()
        {
            effects = gameObject.AddComponent<AudioSource>();
            effects.volume = .40f;
            effects.spatialBlend = 0;
            ambience = gameObject.AddComponent<AudioSource>();
            ambience.volume = .018f;
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
            bell = Tone(392, 1.2f, .04f);
            wind = SoftAir();
            ambience.clip = wind;
            ambience.Play();
        }

        // A quiet, filtered air bed. The previous loop contained a continuous
        // 160 Hz sine oscillator, heard as a hum everywhere in the village.
        static AudioClip SoftAir()
        {
            const int rate = 22050, count = rate * 12;
            var samples = new float[count];
            uint seed = 731;
            float low = 0;
            for (int i = 0; i < count; i++)
            {
                seed = 1664525 * seed + 1013904223;
                float noise = (seed >> 8) / 16777216f * 2 - 1;
                low += (noise - low) * .035f;
                samples[i] = low * .25f;
            }
            // Overlap the tail into the beginning so the repeating seam is quiet.
            const int fade = rate;
            for (int i = 0; i < fade; i++)
            {
                float u = i / (float)(fade - 1);
                samples[i] = Mathf.Lerp(samples[count - fade + i], samples[i], u);
            }
            var clip = AudioClip.Create("Quiet air · no tonal oscillator", count - fade, 1, rate, false);
            var loop = new float[count - fade];
            System.Array.Copy(samples, loop, loop.Length);
            clip.SetData(loop, 0);
            return clip;
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
            AudioClip clip = id == "bell" ? bell : id == "heavy" ? heavy : id == "heavy-impact" ? heavyImpact : id == "flame" ? flame : id == "flame-impact" ? flameImpact : id == "bark" ? bark : id == "hurt" ? hit : id == "growl" ? growl : id == "jump" ? jump : id == "land" ? land : id == "attack" ? attack : id == "impact" ? impact : id == "dash" ? dash : collect;
            if (clip)
                effects.PlayOneShot(clip);
        }
    }
}
