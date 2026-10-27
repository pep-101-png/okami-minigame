using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;

namespace SunwardVillageDemo
{
    // The review scene uses Sunward's existing Input System configuration.
    // Pixel deltas are scaled to the demo's former mouse-axis sensitivity.
    internal static class VillageInput
    {
        static KeyControl Key(KeyCode code)
        {
            Keyboard keyboard = Keyboard.current;
            if (keyboard == null) return null;
            switch (code)
            {
                case KeyCode.W: return keyboard.wKey;
                case KeyCode.A: return keyboard.aKey;
                case KeyCode.S: return keyboard.sKey;
                case KeyCode.D: return keyboard.dKey;
                case KeyCode.E: return keyboard.eKey;
                case KeyCode.H: return keyboard.hKey;
                case KeyCode.Space: return keyboard.spaceKey;
                case KeyCode.Tab: return keyboard.tabKey;
                case KeyCode.Escape: return keyboard.escapeKey;
                case KeyCode.LeftShift: return keyboard.leftShiftKey;
                default: return null;
            }
        }
        public static bool GetKey(KeyCode code) => Key(code)?.isPressed ?? false;
        public static bool GetKeyDown(KeyCode code) => Key(code)?.wasPressedThisFrame ?? false;
        static ButtonControl Button(int index)
        {
            Mouse mouse = Mouse.current;
            if (mouse == null) return null;
            return index == 0 ? mouse.leftButton : index == 1 ? mouse.rightButton : null;
        }
        public static bool GetMouseButton(int index) => Button(index)?.isPressed ?? false;
        public static bool GetMouseButtonDown(int index) => Button(index)?.wasPressedThisFrame ?? false;
        public static float GetAxisRaw(string axis)
        {
            Vector2 delta = Mouse.current?.delta.ReadValue() ?? Vector2.zero;
            return axis == "Mouse X" ? delta.x * .05f : axis == "Mouse Y" ? delta.y * .05f : 0;
        }
        public static Vector2 mousePosition => Mouse.current?.position.ReadValue() ?? Vector2.zero;
        public static Vector2 mouseScrollDelta => (Mouse.current?.scroll.ReadValue() ?? Vector2.zero) / 120f;
    }
}
