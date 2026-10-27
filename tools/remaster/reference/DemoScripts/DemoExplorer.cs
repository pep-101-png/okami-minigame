using UnityEngine;

namespace SunwardVillageDemo
{
    public sealed class DemoExplorer : MonoBehaviour
    {
        public Camera viewCamera;
        public Vector3 overviewTarget = new Vector3(0, 2, 5);
        public Vector3 arrival = new Vector3(-1.6f, .12f, -10.8f);
        public Vector3 hallArrival = new Vector3(-1, .34f, 15.2f);
        CharacterController walker;
        bool walking;
        bool help = true;
        float yaw = 148, pitch = 38, distance = 60, verticalVelocity;
        float walkYaw, walkPitch;

        public bool IsWalking { get { return walking && walker != null && walker.enabled; } }
        public Vector3 VisitorPosition { get { return walker == null ? Vector3.zero : walker.transform.position; } }

        void Awake()
        {
            if (viewCamera == null) viewCamera = Camera.main;
            if (viewCamera == null) { enabled = false; return; }
            GameObject body = new GameObject("Demo visitor");
            walker = body.AddComponent<CharacterController>();
            walker.height = 1.8f; walker.radius = .28f; walker.center = new Vector3(0, .9f, 0);
            walker.stepOffset = .32f; walker.skinWidth = .025f; walker.enabled = false;
            viewCamera.nearClipPlane = .05f; viewCamera.farClipPlane = 250;
            ReturnToOverview();
        }
        void Update()
        {
            if (VillageInput.GetKeyDown(KeyCode.H)) help = !help;
            if (VillageInput.GetKeyDown(KeyCode.Tab)) { if (walking) ReturnToOverview(); else WalkTo(arrival); }
            if (VillageInput.GetKeyDown(KeyCode.Escape)) { Cursor.lockState = CursorLockMode.None; Cursor.visible = true; }
            if (!walking)
            {
                if (VillageInput.GetMouseButton(1)) { yaw += VillageInput.GetAxisRaw("Mouse X") * 3; pitch = Mathf.Clamp(pitch - VillageInput.GetAxisRaw("Mouse Y") * 2, 15, 80); }
                distance = Mathf.Clamp(distance - VillageInput.mouseScrollDelta.y * 2.5f, 12, 105);
                Vector3 offset = new Vector3(Mathf.Sin(yaw * Mathf.Deg2Rad) * Mathf.Cos(pitch * Mathf.Deg2Rad), Mathf.Sin(pitch * Mathf.Deg2Rad), Mathf.Cos(yaw * Mathf.Deg2Rad) * Mathf.Cos(pitch * Mathf.Deg2Rad));
                viewCamera.orthographic = true; viewCamera.orthographicSize = distance * .40f;
                viewCamera.transform.position = overviewTarget + offset * distance;
                viewCamera.transform.LookAt(overviewTarget);
                return;
            }
            if (Cursor.lockState == CursorLockMode.Locked)
            {
                walkYaw += VillageInput.GetAxisRaw("Mouse X") * 2;
                walkPitch = Mathf.Clamp(walkPitch - VillageInput.GetAxisRaw("Mouse Y") * 2, -80, 80);
            }
            else if (VillageInput.GetMouseButtonDown(0) && VillageInput.mousePosition.y < Screen.height - 345) { Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false; }
            float x = (VillageInput.GetKey(KeyCode.D) ? 1 : 0) - (VillageInput.GetKey(KeyCode.A) ? 1 : 0);
            float z = (VillageInput.GetKey(KeyCode.W) ? 1 : 0) - (VillageInput.GetKey(KeyCode.S) ? 1 : 0);
            Vector3 direction = Quaternion.Euler(0, walkYaw, 0) * Vector3.ClampMagnitude(new Vector3(x, 0, z), 1);
            if (walker.isGrounded) { verticalVelocity = -2; if (VillageInput.GetKeyDown(KeyCode.Space)) verticalVelocity = 4.8f; }
            else verticalVelocity += Physics.gravity.y * Time.deltaTime;
            walker.Move((direction * (VillageInput.GetKey(KeyCode.LeftShift) ? 5.5f : 3f) + Vector3.up * verticalVelocity) * Time.deltaTime);
            if (walker.transform.position.y < -8) WalkTo(arrival);
            viewCamera.transform.position = walker.transform.position + Vector3.up * 1.65f;
            viewCamera.transform.rotation = Quaternion.Euler(walkPitch, walkYaw, 0);
        }
        public void WalkTo(Vector3 point, float heading = 0)
        {
            walker.enabled = false; walker.transform.position = point; walker.enabled = true;
            walking = true; verticalVelocity = 0; walkYaw = heading; walkPitch = 0;
            viewCamera.orthographic = false; viewCamera.fieldOfView = 78;
            Cursor.lockState = CursorLockMode.Locked; Cursor.visible = false;
        }
        void ReturnToOverview()
        {
            walking = false; if (walker != null) walker.enabled = false;
            Cursor.lockState = CursorLockMode.None; Cursor.visible = true;
        }
        void OnDisable() { Cursor.lockState = CursorLockMode.None; Cursor.visible = true; }
        void OnGUI()
        {
            if (!help) { GUI.Label(new Rect(12, 12, 400, 28), "H: show controls"); return; }
            GUI.Box(new Rect(10, 10, 550, 330), "Sunward village - Village Breeze");
            GUI.Label(new Rect(23, 38, 520, 24), walking ? "WASD: walk   Mouse: look   Shift: jog   Space: jump   Esc: release mouse" : "Right mouse: orbit   Wheel: zoom   Tab: walk   H: hide controls");
            if (GUI.Button(new Rect(24, 71, 155, 30), "Explore on foot")) WalkTo(arrival);
            if (GUI.Button(new Rect(191, 71, 155, 30), "Inside the hall")) WalkTo(hallArrival);
            if (GUI.Button(new Rect(358, 71, 182, 30), "Village overview")) { overviewTarget = new Vector3(0,2,5); distance = 60; ReturnToOverview(); }
            if (GUI.Button(new Rect(24, 109, 250, 30), "Visit the river bridge")) WalkTo(new Vector3(9.55f, .15f, 5.6f), 90);
            if (GUI.Button(new Rect(287, 109, 253, 30), "Visit the shrine garden")) WalkTo(new Vector3(-8.8f, .15f, 15.8f), -90);
            DemoHouseDoors homes = DemoHouseDoors.Active;
            if (homes != null && homes.Homes != null)
            {
                for (int i = 0; i < homes.Homes.Length; ++i)
                {
                    DemoHouseDoors.Home home = homes.Homes[i];
                    if (GUI.Button(new Rect(24 + (i % 2) * 263, 182 + (i / 2) * 32, 253, 28), "Visit " + home.name)) WalkTo(home.arrival, home.heading);
                }
            }
            if (GUI.Button(new Rect(24, 286, 253, 28), "Farm overview"))
            {
                ReturnToOverview(); overviewTarget = new Vector3(-28, 2.7f, 5.8f); distance = 46;
            }
            DemoFarmAnimals farm = DemoFarmAnimals.Active;
            if (farm != null && GUI.Button(new Rect(287, 286, 253, 28), farm.Paused ? "Animal animation: paused" : "Animal animation: on")) farm.Paused = !farm.Paused;
            DemoWaterMotion water = DemoWaterMotion.Active;
            if (water != null && GUI.Button(new Rect(24, 148, 220, 26), water.Animated ? "Water animation: on" : "Water animation: paused")) water.Animated = !water.Animated;
            GUI.Label(new Rect(260, 150, 280, 24), "Approach doors to open; E: toggle");
        }
    }
}
