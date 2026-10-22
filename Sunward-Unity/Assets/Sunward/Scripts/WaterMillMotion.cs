using UnityEngine;
using System.Linq;

namespace Sunward
{
    public sealed class WaterMillMotion : MonoBehaviour
    {
        public Transform wheel, shaft, pinion, spindle, millstone;
        public ParticleSystem spray;
        public Transform pestle;
        public Transform[] grainDrops;
        Vector3 pestleRest;
        Vector3[] grainRest;
        public GameFlow game;
        float angle;
        void Start()
        {
            if (pestle)
                pestleRest = pestle.localPosition;
            grainRest = new Vector3[grainDrops == null ? 0 : grainDrops.Length];
            for (int i = 0; i < grainRest.Length; i++)
                if (grainDrops[i])
                    grainRest[i] = grainDrops[i].localPosition;
            if (!game)
                return;
            game.valley.Data.boxes = game.valley.Data.boxes.Where(b => !(Mathf.Abs(b.x + 16.7f) < .01f && Mathf.Abs(b.z + 5) < .01f && Mathf.Abs(b.halfZ - .35f) < .01f)).ToArray();
            game.valley.Data.obstacles = game.valley.Data.obstacles.Where(o =>
                !(Mathf.Abs(o.x + 12.45f) < .01f && Mathf.Abs(o.z + 5) < .01f) &&
                !(Mathf.Abs(o.x + 20.175206f) < .08f && Mathf.Abs(o.z + 6.7f) < .08f)).ToArray();
        }

        void Update()
        {
            if (game && game.Blocked)
                return;
            angle = Mathf.Repeat(angle + Time.deltaTime * 18, 360);
            wheel.localRotation = Quaternion.Euler(angle, 0, 0);
            shaft.localRotation = Quaternion.Euler(angle, 0, 90);
            // Equal-size right-angle crown gears: 1:1 counter-rotation.
            pinion.localRotation = Quaternion.Euler(angle, 0, 0);
            spindle.localRotation = Quaternion.Euler(0, -angle, 0);
            millstone.localRotation = Quaternion.Euler(0, -angle, 0);
            // Four cam lobes lift and drop a rice pestle from the SAME wheel phase.
            // No independent clock: pausing the wheel freezes the whole workshop.
            if (pestle)
                pestle.localPosition = pestleRest + Vector3.up *
                    (.32f * Mathf.Pow(.5f + .5f * Mathf.Sin(angle * 4 * Mathf.Deg2Rad), 2));
            if (grainRest != null)
                for (int i = 0; i < grainRest.Length; i++)
                    if (grainDrops[i])
                    {
                        Vector3 p = grainRest[i];
                        p.y = .43f - Mathf.Repeat(angle / 45f + i / (float)grainRest.Length, 1) * .39f;
                        grainDrops[i].localPosition = p;
                    }
        }
    }
}
