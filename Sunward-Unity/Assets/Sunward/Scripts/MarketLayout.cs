using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    public sealed class MarketLayout : MonoBehaviour
    {
        public Valley valley;
        void Start()
        {
            if (!valley) return;
            var boxes = new List<BoxData>();
            foreach (var box in valley.Data.boxes)
                if (!(Mathf.Abs(Mathf.Abs(box.x) - 4.8f) < .02f && Mathf.Abs(box.z) < .02f && Mathf.Abs(box.halfX - 1.2f) < .02f))
                    boxes.Add(box);
            valley.Data.boxes = boxes.ToArray();
        }
    }
}
