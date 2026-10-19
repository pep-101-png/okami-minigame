using System.Collections;
using UnityEngine;

namespace Sunward
{
    public sealed class PaintedEffects : MonoBehaviour
    {
        public Material ink;
        public LineRenderer Ring(Vector3 center, Color color, float radius, float life = .65f)
        {
            if (!MeshSafety.Finite(center) || !float.IsFinite(radius))
                throw new System.InvalidOperationException("Invalid painted-ring input: " + center + ", radius " + radius);
            var go = new GameObject("Painted impact ring");
            go.transform.position = center + Vector3.up * .035f;
            var line = go.AddComponent<LineRenderer>();
            line.sharedMaterial = ink;
            line.useWorldSpace = false;
            line.positionCount = 49;
            line.loop = false;
            line.widthCurve = new AnimationCurve(new Keyframe(0, .7f), new Keyframe(.5f, 1), new Keyframe(1, .2f));
            line.widthMultiplier = .05f;
            line.startColor = line.endColor = color;
            for (int i = 0; i < 49; i++)
            {
                float a = i / 48f * Mathf.PI * 2;
                line.SetPosition(i, new Vector3(Mathf.Sin(a), 0, Mathf.Cos(a)) * radius * (1 + Mathf.Sin(a * 7) * .015f));
            }

            StartCoroutine(Fade(line, life));
            return line;
        }

        IEnumerator Fade(LineRenderer line, float life)
        {
            float t = 0;
            var c = line.startColor;
            while (line && t < life)
            {
                t += Time.deltaTime;
                c.a = 1 - t / life;
                line.startColor = line.endColor = c;
                yield return null;
            }

            if (line)
                Destroy(line.gameObject);
        }

        // Curved, tapered orbital strokes ported from the original Sundial effect.
        public void SundialOrbit(Vector3 center, bool heavy)
        {
            for (int layer = 0; layer < 3; layer++)
            {
                var go = new GameObject("Sundial · painted flame orbit");
                go.transform.position = center;
                var line = go.AddComponent<LineRenderer>();
                line.sharedMaterial = ink;
                line.useWorldSpace = false;
                line.positionCount = 28;
                line.widthMultiplier = heavy ? .16f : .10f;
                line.widthCurve = new AnimationCurve(new Keyframe(0, 0), new Keyframe(.25f, 1), new Keyframe(1, 0));
                line.startColor = line.endColor = layer == 1 ? new Color(1, .80f, .38f) : new Color(.88f, .34f, .16f);
                for (int i = 0; i < 28; i++)
                {
                    float angle = i / 27f * Mathf.PI * 1.8f + layer * .9f;
                    float radius = heavy ? 2 : 1.6f;
                    line.SetPosition(i, new Vector3(Mathf.Sin(angle) * radius, .6f + Mathf.Sin(angle * 2) * .25f, Mathf.Cos(angle) * radius));
                }

                StartCoroutine(Fade(line, heavy ? .42f : .32f));
            }
        }

        public void Impact(Vector3 point, Color color)
        {
            Ring(point, color, .7f, .22f);
            for (int i = 0; i < 5; i++)
            {
                var g = new GameObject("Dry brush impact");
                var l = g.AddComponent<LineRenderer>();
                l.sharedMaterial = ink;
                l.positionCount = 3;
                l.startWidth = .065f;
                l.endWidth = 0;
                Vector3 d = Quaternion.Euler(i * 51, i * 71, i * 31) * Vector3.up;
                l.SetPositions(new[] { point, point + d * .25f, point + d * .6f });
                l.startColor = l.endColor = color;
                StartCoroutine(Fade(l, .20f));
            }
        }
    }
}
