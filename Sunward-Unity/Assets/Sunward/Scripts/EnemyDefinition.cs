using UnityEngine;

namespace Sunward
{
    [CreateAssetMenu(menuName = "Sunward/Spirit")]
    public sealed class EnemyDefinition : ScriptableObject
    {
        public string id, title;
        public GameObject visual;
        public float hp, damage, speed, scale, windup;
        public int reward, xp;
    }
}
