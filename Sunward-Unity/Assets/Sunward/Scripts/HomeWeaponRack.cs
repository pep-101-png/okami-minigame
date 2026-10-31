using UnityEngine;

namespace Sunward
{
    public sealed class HomeWeaponRack : MonoBehaviour
    {
        public GameFlow game;
        public GameObject displays;
        void LateUpdate()
        {
            if (displays)
                displays.SetActive(!game.InTrial && HomeCutaway.Inside(game.Player.transform.position));
        }
    }
}
