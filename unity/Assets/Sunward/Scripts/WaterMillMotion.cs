using UnityEngine;
using System.Linq;

namespace Sunward
{
    public sealed class WaterMillMotion : MonoBehaviour
    {
        public Transform wheel, shaft, pinion, spindle, millstone;
        public ParticleSystem spray;
        public GameFlow game;
        float angle;
        void Start()
        {
            if (!game)
                return;
            game.valley.Data.boxes = game.valley.Data.boxes.Where(b => !(Mathf.Abs(b.x + 16.7f) < .01f && Mathf.Abs(b.z + 5) < .01f && Mathf.Abs(b.halfZ - .35f) < .01f)).ToArray();
            game.valley.Data.obstacles = game.valley.Data.obstacles.Where(o => !(Mathf.Abs(o.x + 12.45f) < .01f && Mathf.Abs(o.z + 5) < .01f)).ToArray();
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
        }
    }
}
