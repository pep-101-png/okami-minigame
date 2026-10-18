using System.Collections;
using UnityEngine;

namespace Sunward
{
    public sealed class DivineGrowth : MonoBehaviour
    {
        public GameFlow game;
        public WolfMotor player;
        public Material ink;
        LineRenderer[] wind;
        Transform[] curls;
        float power;
        void Start()
        {
            wind = new LineRenderer[9];
            for (int i = 0; i < wind.Length; i++)
            {
                var go = new GameObject("Spectral wind " + i);
                go.transform.SetParent(transform, false);
                var l = go.AddComponent<LineRenderer>();
                l.sharedMaterial = ink;
                l.useWorldSpace = false;
                l.positionCount = 22;
                l.widthCurve = new AnimationCurve(new Keyframe(0, 0), new Keyframe(.15f, 1), new Keyframe(1, 0));
                l.widthMultiplier = .035f + (i % 3) * .015f;
                wind[i] = l;
            }

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
        }

        void Update()
        {
            if (!game)
                return;
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

            foreach (var curl in curls)
            {
                curl.gameObject.SetActive(power > 0);
                curl.localScale = Vector3.one * (.2f + power * .8f) / .34f;
                curl.localRotation = Quaternion.Euler(Mathf.Sin(Time.time * 2 - curl.GetSiblingIndex()) * 4, 0, 0);
            }
        }
    }
}
