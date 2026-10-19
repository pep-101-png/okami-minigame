using UnityEngine;

namespace Sunward
{
    public sealed class HangingWind : MonoBehaviour
    {
        public float phase, amplitude = 2;
        Quaternion rest;
        void Awake()
        {
            rest = transform.localRotation;
        }

        void Update()
        {
            transform.localRotation = rest * Quaternion.Euler(Mathf.Sin(Time.time * .8f + phase) * amplitude, 0, Mathf.Sin(Time.time * .63f + phase) * amplitude * .6f);
        }
    }
}
