using UnityEngine;

namespace Sunward
{
    public sealed class CollectibleShelf : MonoBehaviour
    {
        public Transform[] slots;
        public GameFlow game;
        readonly System.Collections.Generic.Dictionary<string, GameObject> entries = new System.Collections.Generic.Dictionary<string, GameObject>();
        public void Register(string id, GameObject prefab)
        {
            if (string.IsNullOrWhiteSpace(id) || !prefab)
                return;
            entries[id] = prefab;
            Refresh();
        }

        public bool Award(string id)
        {
            if (!entries.ContainsKey(id) || System.Array.IndexOf(game.Profile.collectibles, id) >= 0)
                return false;
            var a = game.Profile.collectibles;
            System.Array.Resize(ref a, a.Length + 1);
            a[a.Length - 1] = id;
            game.Profile.collectibles = a;
            game.Save.Save();
            Refresh();
            return true;
        }

        public void Refresh()
        {
            foreach (var slot in slots)
                foreach (Transform child in slot)
                    Destroy(child.gameObject);
            int i = 0;
            foreach (var id in game.Profile.collectibles)
                if (entries.TryGetValue(id, out var prefab) && i < slots.Length)
                    Instantiate(prefab, slots[i++], false);
        }
    }
}
