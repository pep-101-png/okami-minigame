using System;
using System.Collections.Generic;
using UnityEngine;

namespace SunwardVillageDemo
{
    // Runtime-only objects belong to the generated demo root and are never saved to the main game.
    public sealed class DemoHouseDoors : MonoBehaviour
    {
        [Serializable] public sealed class Data { public Home[] homes; public WallBox[] boxes; }
        [Serializable] public sealed class Home
        {
            public string id, name;
            public float floor, heading;
            public Vector3 inside, arrival, light;
            public Door[] doors;
        }
        [Serializable] public sealed class WallBox { public string name; public Vector3 center, size; public float yaw; }
        [Serializable] public sealed class Leaf { public string id; public string[] meshes; public Vector3 center, size, slide; }
        [Serializable] public sealed class Door { public string id; public Vector3 center, size; public float yaw; public Leaf[] leaves; }
        sealed class MovingDoor
        {
            public Door data;
            public string homeName;
            public Transform[] leaves;
            public float openness, lastNearby;
            public bool manuallyClosed;
        }
        readonly List<MovingDoor> doors = new List<MovingDoor>();
        DemoExplorer explorer;
        MovingDoor nearest;
        public static DemoHouseDoors Active { get; private set; }
        public Home[] Homes { get; private set; }

        public void Initialize(Dictionary<string, Transform> parts)
        {
            if (!Application.isPlaying) return;
            TextAsset asset = Resources.Load<TextAsset>("DemoGeometry/VillageHomes");
            if (asset == null) throw new InvalidOperationException("The separate demo house data is missing.");
            Data data = JsonUtility.FromJson<Data>(asset.text);
            if (data == null || data.homes == null || data.boxes == null) throw new InvalidOperationException("Invalid house data.");
            Homes = data.homes;
            foreach (WallBox box in data.boxes)
            {
                GameObject wall = new GameObject(box.name); wall.transform.SetParent(transform, false);
                wall.transform.localPosition = box.center; wall.transform.localRotation = Quaternion.Euler(0, box.yaw, 0);
                wall.AddComponent<BoxCollider>().size = box.size;
            }
            foreach (Home home in Homes)
            {
                GameObject lamp = new GameObject(home.name + " warm interior fill"); lamp.transform.SetParent(transform, false);
                lamp.transform.localPosition = home.light;
                Light light = lamp.AddComponent<Light>(); light.type = LightType.Point; light.color = new Color(1, .77f, .49f);
                light.intensity = .65f; light.range = home.id == "hall" ? 8 : 5; light.shadows = LightShadows.None;
                foreach (Door door in home.doors)
                {
                    MovingDoor moving = new MovingDoor { data = door, homeName = home.name, leaves = new Transform[door.leaves.Length], lastNearby = -10 };
                    for (int i = 0; i < door.leaves.Length; ++i)
                    {
                        Leaf leaf = door.leaves[i];
                        GameObject pivot = new GameObject("Sliding door " + leaf.id); pivot.transform.SetParent(transform, false);
                        pivot.transform.localPosition = leaf.center; moving.leaves[i] = pivot.transform;
                        foreach (string meshName in leaf.meshes)
                        {
                            Transform part;
                            if (!parts.TryGetValue(meshName, out part)) throw new InvalidOperationException("Missing animated door mesh: " + meshName);
                            part.SetParent(pivot.transform, false); part.localPosition = -leaf.center;
                        }
                        GameObject shape = new GameObject("Door safety collider"); shape.transform.SetParent(pivot.transform, false);
                        shape.transform.localRotation = Quaternion.Euler(0, door.yaw, 0); shape.AddComponent<BoxCollider>().size = leaf.size;
                    }
                    doors.Add(moving);
                }
            }
            explorer = FindFirstObjectByType<DemoExplorer>(); Active = this;
            Debug.Log("Village homes ready: " + Homes.Length + " buildings, " + doors.Count + " animated doorways. Approach to open; E to toggle. Closing pauses for the visitor.");
        }
        void Update()
        {
            if (explorer == null) { nearest = null; return; }
            bool visiting = explorer.IsWalking;
            Vector3 visitor = explorer.VisitorPosition + Vector3.up * .9f;
            float nearestDistance = 3; nearest = null;
            foreach (MovingDoor door in doors)
            {
                Vector3 center = transform.TransformPoint(door.data.center);
                Quaternion rotation = transform.rotation * Quaternion.Euler(0, door.data.yaw, 0);
                Vector3 local = Quaternion.Inverse(rotation) * (visitor - center);
                bool near = visiting && Mathf.Abs(local.z) < 2.5f && Mathf.Abs(local.x) < door.data.size.x * .5f + .7f && Mathf.Abs(local.y) < door.data.size.y * .5f + .6f;
                bool occupied = visiting && Mathf.Abs(local.z) < .85f && Mathf.Abs(local.x) < door.data.size.x * .5f + .4f && Mathf.Abs(local.y) < door.data.size.y * .5f + .6f;
                if (near)
                {
                    door.lastNearby = Time.time;
                    float distance = (visitor - center).magnitude;
                    if (distance < nearestDistance) { nearestDistance = distance; nearest = door; }
                }
                else if (Mathf.Abs(local.z) > 3.2f || Mathf.Abs(local.x) > door.data.size.x * .5f + 1.5f) door.manuallyClosed = false;
                bool open = occupied || (!door.manuallyClosed && (near || Time.time - door.lastNearby < 3));
                door.openness = Mathf.MoveTowards(door.openness, open ? 1 : 0, Time.deltaTime / 1.15f);
                float eased = Mathf.SmoothStep(0, 1, door.openness);
                for (int i = 0; i < door.leaves.Length; ++i) door.leaves[i].localPosition = door.data.leaves[i].center + door.data.leaves[i].slide * eased;
            }
            if (nearest != null && (DemoFarmAnimals.Active == null || !DemoFarmAnimals.Active.PetTargetAvailable) && VillageInput.GetKeyDown(KeyCode.E)) nearest.manuallyClosed = !nearest.manuallyClosed;
        }
        void OnGUI()
        {
            if (nearest != null && (DemoFarmAnimals.Active == null || !DemoFarmAnimals.Active.PetTargetAvailable)) GUI.Box(new Rect(Screen.width / 2f - 190, Screen.height - 54, 380, 32), nearest.homeName + " - E: " + (nearest.manuallyClosed ? "open doors" : "close doors"));
        }
        void OnDestroy() { if (Active == this) Active = null; }
    }
}
