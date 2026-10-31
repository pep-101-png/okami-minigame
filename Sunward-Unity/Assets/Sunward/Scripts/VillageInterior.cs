using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    // The old solid house navigation block is replaced by the actual room walls.
    public sealed class VillageInterior : MonoBehaviour
    {
        public WolfMotor player;
        public Valley valley;
        public Vector2 halfSize;
        public Renderer[] cutaway;
        public Vector2 legacyHouse;
        public bool Contains(Vector3 position)
        {
            Vector3 p = position - transform.position;
            return Mathf.Abs(p.x) < halfSize.x + .5f && Mathf.Abs(p.z) < halfSize.y + .5f;
        }
        void Start()
        {
            if (!valley) return;
            var boxes = new List<BoxData>();
            foreach (var box in valley.Data.boxes)
                if (Mathf.Abs(box.x - legacyHouse.x) > .02f || Mathf.Abs(box.z + legacyHouse.y) > .02f)
                    boxes.Add(box);
            valley.Data.boxes = boxes.ToArray();
        }
        void LateUpdate()
        {
            if (!player) return;
            bool inside = Contains(player.transform.position);
            foreach (var renderer in cutaway)
                if (renderer) renderer.enabled = !inside;
        }
    }
}
