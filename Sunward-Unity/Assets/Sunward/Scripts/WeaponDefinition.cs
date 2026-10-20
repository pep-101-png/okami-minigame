using UnityEngine;

namespace Sunward
{
    [System.Serializable]
    public class Strike
    {
        public string clip;
        public float duration = .4f, damage = 1, range = 3.3f, arc = .8f, start = .35f, end = .5f, lunge = 2, stagger = .4f;
    }

    [CreateAssetMenu(menuName = "Sunward/Weapon")]
    public sealed class WeaponDefinition : ScriptableObject
    {
        public string id, title;
        public GameObject visual;
        public Strike[] light;
        public Strike[] heavy;
        public Strike charged, chargedHeavy, air;
    }
}
