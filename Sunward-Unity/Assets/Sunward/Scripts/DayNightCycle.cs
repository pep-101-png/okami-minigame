using UnityEngine;

namespace Sunward
{
    // A full day takes twenty real minutes. Menus/rest pause ordinary progression.
    public sealed class DayNightCycle : MonoBehaviour
    {
        public GameFlow game;
        public Light sun;
        [Range(0, 24)] public float hour = 9;
        public float dayMinutes = 20;
        public Light[] lanterns = new Light[0];
        public Renderer[] lanternPaper = new Renderer[0];
        float[] intensities;
        public float Hour => hour;
        public bool IsNight => hour < 6 || hour >= 18;

        void Awake()
        {
            intensities = new float[lanterns.Length];
            for (int i = 0; i < lanterns.Length; i++)
                intensities[i] = lanterns[i] ? lanterns[i].intensity : 0;
        }

        public void RestUntilNextPhase()
        {
            hour = IsNight ? 7.5f : 20;
            Apply();
        }

        void Update()
        {
            if (game && !game.Blocked && !game.InTrial && !game.Home.Active && VillageRest.ActiveRest == null)
                hour = Mathf.Repeat(hour + Time.deltaTime * 24 / Mathf.Max(120, dayMinutes * 60), 24);
            Apply();
        }

        void Apply()
        {
            float daylight = Mathf.SmoothStep(0, 1, Mathf.Clamp01((Mathf.Sin((hour - 6) * Mathf.PI / 12) + .12f) / .42f));
            float night = 1 - daylight;
            Shader.SetGlobalFloat("_SunwardNight", night);
            if (sun)
            {
                // Moonlight remains directional/readable, rather than pitching the village black.
                sun.transform.rotation = Quaternion.Euler(Mathf.Lerp(28, 66, daylight), hour * 15 - 100, 0);
                sun.color = Color.Lerp(new Color(.42f, .53f, .86f), new Color(1, .91f, .72f), daylight);
                sun.intensity = Mathf.Lerp(.28f, 1.5f, daylight);
            }
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = Color.Lerp(new Color(.095f, .12f, .25f), new Color(.52f, .61f, .67f), daylight);
            RenderSettings.ambientEquatorColor = Color.Lerp(new Color(.095f, .10f, .18f), new Color(.46f, .43f, .32f), daylight);
            RenderSettings.ambientGroundColor = Color.Lerp(new Color(.035f, .045f, .075f), new Color(.25f, .25f, .19f), daylight);
            RenderSettings.fogColor = Color.Lerp(new Color(.09f, .12f, .22f), new Color(.65f, .67f, .54f), daylight);
            for (int i = 0; i < lanterns.Length; i++)
                if (lanterns[i]) lanterns[i].intensity = intensities[i] * Mathf.Lerp(.12f, 1, night) * (1 + Mathf.Sin(Time.time * 1.7f + i * 2.1f) * .025f);
            // The shader's global night amount is also consumed by the painted sky.
        }

        void OnDisable() { Shader.SetGlobalFloat("_SunwardNight", 0); }
    }
}
