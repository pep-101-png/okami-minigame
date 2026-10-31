using UnityEngine;
using UnityEngine.InputSystem;

namespace Sunward
{
    public sealed class WolfInput : MonoBehaviour
    {
        public InputAction Brush, Dig, Carry, Eat;
        public InputAction Move, Look, Jump, Dodge, Light, Heavy, Interact, Switch, Bark, Sprint, Walk, Pause, Orbit, Zoom, Journal;
        InputAction Button(string name, string key, string pad)
        {
            var a = new InputAction(name, InputActionType.Button);
            a.AddBinding(key);
            if (pad != null)
                a.AddBinding(pad);
            if (name == "Light")
                a.AddBinding("<Keyboard>/j");
            if (name == "Heavy")
                a.AddBinding("<Keyboard>/l");
            a.Enable();
            return a;
        }

        void Awake()
        {
            Move = new InputAction("Move", InputActionType.Value, expectedControlType: "Vector2");
            Move.AddCompositeBinding("2DVector").With("Up", "<Keyboard>/w").With("Down", "<Keyboard>/s").With("Left", "<Keyboard>/a").With("Right", "<Keyboard>/d");
            Move.AddBinding("<Gamepad>/leftStick");
            Move.Enable();
            Look = new InputAction("Look", InputActionType.Value);
            Look.AddBinding("<Mouse>/delta");
            Look.AddBinding("<Gamepad>/rightStick");
            Look.Enable();
            Jump = Button("Jump", "<Keyboard>/space", "<Gamepad>/buttonSouth");
            Dodge = Button("Dodge", "<Keyboard>/k", "<Gamepad>/buttonEast");
            Light = Button("Light", "<Mouse>/leftButton", "<Gamepad>/rightShoulder");
            Heavy = Button("Heavy", "<Mouse>/rightButton", "<Gamepad>/rightTrigger");
            Interact = Button("Interact", "<Keyboard>/e", "<Gamepad>/buttonWest");
            Switch = Button("Switch", "<Keyboard>/q", "<Gamepad>/dpad/right");
            Bark = Button("Bark", "<Keyboard>/b", "<Gamepad>/leftShoulder");
            Sprint = Button("Sprint", "<Keyboard>/leftShift", "<Gamepad>/leftStickPress");
            Walk = Button("Walk", "<Keyboard>/leftCtrl", "<Gamepad>/leftTrigger");
            Pause = Button("Pause", "<Keyboard>/escape", "<Gamepad>/start");
            Journal = Button("Journal", "<Keyboard>/tab", "<Gamepad>/select");
            Brush=Button("Brush","<Keyboard>/r","<Gamepad>/dpad/up");
            Dig=Button("Dig","<Keyboard>/f","<Gamepad>/dpad/down");
            Carry=Button("Carry","<Keyboard>/g",null);
            Eat=Button("Eat","<Keyboard>/h","<Gamepad>/dpad/left");
            Orbit = Button("Orbit", "<Mouse>/middleButton", null);
            Zoom = new InputAction("Zoom", binding: "<Mouse>/scroll/y");
            Zoom.Enable();
        }

        void OnDestroy()
        {
            foreach (var a in new[]
            {
                Brush, Dig, Carry, Eat,
                Move,
                Look,
                Jump,
                Dodge,
                Light,
                Heavy,
                Interact,
                Switch,
                Bark,
                Sprint,
                Walk,
                Pause,
                Journal,
                Orbit,
                Zoom
            }

            )
                a?.Dispose();
        }
    }
}
