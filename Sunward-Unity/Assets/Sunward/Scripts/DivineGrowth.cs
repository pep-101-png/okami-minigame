using System.Collections;
using UnityEngine;

namespace Sunward
{
    public sealed class DivineGrowth : MonoBehaviour
    {
        public GameFlow game;
        public WolfMotor player;
        public Material ink;
        public Mesh shiranuiMane;
        public Material shiranuiMaterial;
        public bool TestShiranui { get; private set; }
        GameObject testForm;
        LineRenderer[] testWisps;

        LineRenderer[] wind;
        Transform[] curls;
        float power;
        void Start()
        {
            // No persistent movement aura/indicator around Amaterasu. Keep the
            // earned power curls and short, event-driven combat effects.
            wind = new LineRenderer[0];

            var list = new System.Collections.Generic.List<Transform>();
            foreach (var bone in player.animationView.animator.GetComponentsInChildren<Transform>())
            {
                string n = bone.name.Replace(".", "");
                if (n == "DEF_shoulderL" || n == "DEF_shoulderR" || n == "DEF_front_pawL" || n == "DEF_front_pawR" || n == "DEF_rear_hockL" || n == "DEF_rear_hockR")
                {
                    for (int j = 0; j < 2; j++)
                    {
                        var go = new GameObject("Power curl");
                        go.transform.SetParent(bone, false);
                        go.transform.localScale = Vector3.one / .34f;
                        var l = go.AddComponent<LineRenderer>();
                        l.sharedMaterial = ink;
                        l.useWorldSpace = false;
                        l.widthMultiplier = .075f - j * .02f;
                        l.positionCount = 28;
                        l.widthCurve = new AnimationCurve(new Keyframe(0, 1), new Keyframe(1, 0));
                        for (int i = 0; i < 28; i++)
                        {
                            float t = i / 27f, a = t * 7;
                            l.SetPosition(i, new Vector3(Mathf.Sin(a) * .16f * (1 - t), .13f + t * .55f, Mathf.Cos(a) * .14f * (1 - t) + t * .20f));
                        }

                        list.Add(go.transform);
                    }
                }
            }

            curls = list.ToArray();
            testForm = new GameObject("Shiranui · temporary P-key appearance preview");
            testForm.transform.SetParent(player.transform, false);
            if (shiranuiMane && shiranuiMaterial)
            {
                testForm.AddComponent<MeshFilter>().sharedMesh = shiranuiMane;
                var body = testForm.AddComponent<MeshRenderer>();
                body.sharedMaterial = shiranuiMaterial;
                body.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                body.receiveShadows = false;
            }
            testWisps = new LineRenderer[8];
            for (int i = 0; i < testWisps.Length; i++)
            {
                var go = new GameObject("White-gold Shiranui streamer " + i);
                go.transform.SetParent(testForm.transform, false);
                var line = go.AddComponent<LineRenderer>();
                line.sharedMaterial = ink;
                line.useWorldSpace = false;
                line.positionCount = 22;
                line.widthMultiplier = .065f;
                line.widthCurve = new AnimationCurve(new Keyframe(0, .5f), new Keyframe(.2f, 1), new Keyframe(1, 0));
                line.startColor = new Color(1, .91f, .66f, .8f);
                line.endColor = new Color(1, .45f, .2f, 0);
                line.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                line.receiveShadows = false;
                testWisps[i] = line;
            }
            testForm.SetActive(false);
        }

        void Update()
        {
            if (!game)
                return;
            if (player && player.input && player.input.ShiranuiTest.WasPressedThisFrame() && !game.Blocked)
            {
                TestShiranui = !TestShiranui;
                if (testForm) testForm.SetActive(TestShiranui);
                game.Notify(TestShiranui ? "Shiranui appearance test ON · P to return · progress unchanged" : "Shiranui appearance test OFF");
            }
            if (TestShiranui && testForm)
            {
                testForm.transform.localPosition = Vector3.up * (Mathf.Sin(Time.time * 1.7f) * .012f);
                for (int i = 0; i < testWisps.Length; i++)
                    for (int j = 0; j < 22; j++)
                    {
                        float u = j / 21f;
                        float side = i % 2 == 0 ? -1 : 1;
                        float z = .35f - i / 2 * .22f;
                        testWisps[i].SetPosition(j, new Vector3(side * (.22f + Mathf.Sin(u * 5 + Time.time * 1.5f + i) * .09f * u), 1.32f + u * .45f + Mathf.Sin(u * 6 - Time.time * 2 + i) * .04f * u, z - u * .70f));
                    }
            }
            power = Mathf.Clamp01((ProgressionRules.Power(game.Profile) - 5) / 45);
            float speed = Mathf.Clamp01((player.Speed - 2) / 3);
            for (int i = 0; i < wind.Length; i++)
            {
                var l = wind[i];
                l.enabled = power > 0 || speed > .01f;
                var c = i % 3 == 0 ? new Color(.57f, .72f, .64f) : new Color(.94f, .91f, .82f);
                c.a = (.15f * speed + .45f * power);
                l.startColor = l.endColor = c;
                for (int j = 0; j < 22; j++)
                {
                    float t = j / 21f;
                    l.SetPosition(j, new Vector3(Mathf.Sin(t * 7 + Time.time * 2 - i) * (.08f + t * .14f), 1.0f + Mathf.Cos(i * 1.4f) * .5f + Mathf.Sin(t * 6 + Time.time * 3 - i) * .08f, -t * (.6f + speed * 1.8f + power * .8f)));
                }
            }

            if (curls == null) return;
            foreach (var curl in curls)
            {
                curl.gameObject.SetActive(power > 0);
                curl.localScale = Vector3.one * (.2f + power * .8f) / .34f;
                curl.localRotation = Quaternion.Euler(Mathf.Sin(Time.time * 2 - curl.GetSiblingIndex()) * 4, 0, 0);
            }
        }
    }
}
