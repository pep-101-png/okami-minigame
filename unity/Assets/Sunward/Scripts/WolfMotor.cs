using UnityEngine;

namespace Sunward
{
    [RequireComponent(typeof(CharacterController), typeof(WolfInput))]
    public sealed class WolfMotor : MonoBehaviour
    {
        public Valley valley;
        public GameFlow game;
        public WolfAnimation animationView;
        public Transform view;
        public CharacterController controller;
        public WolfInput input;
        public float Speed { get; private set; }
        public float Vertical { get; private set; }

        public float Invulnerable;
        public bool Grounded { get; private set; }

        public bool Locked;
        public Vector3 Velocity { get; private set; }

        Vector3 horizontal, dodgeDirection;
        float dodgeTimer, coyote, jumpBuffer, landing;
        bool doubleUsed;
        public bool Dodging => dodgeTimer > 0;

        void Awake()
        {
            controller = GetComponent<CharacterController>();
            input = GetComponent<WolfInput>();
        }

        public void Teleport(Vector3 point)
        {
            controller.enabled = false;
            transform.position = point;
            controller.enabled = true;
            horizontal = Vector3.zero;
            Vertical = 0;
            Speed = 0;
        }

        public void Recover(Vector3 point)
        {
            Teleport(point);
            dodgeTimer = landing = jumpBuffer = 0;
            doubleUsed = false;
            Grounded = true;
            Invulnerable = Mathf.Max(Invulnerable, .8f);
            animationView.Play("Land_Soft", .08f, .25f, true);
        }

        public void Push(Vector3 delta)
        {
            if (!controller.enabled)
                return;
            Vector3 old = transform.position;
            controller.Move(delta);
            var guarded = valley.GuardRiver(old, transform.position);
            if (game.InTrial)
            {
                var d = guarded - new Vector3(35, guarded.y, 0);
                if (d.magnitude > 17.0f)
                    guarded = new Vector3(35, guarded.y, 0) + d.normalized * 17;
            }

            var b = valley.Data.bounds;
            guarded.x = Mathf.Clamp(guarded.x, b.minX + .5f, b.maxX - .5f);
            guarded.z = Mathf.Clamp(guarded.z, -b.maxZ + .5f, -b.minZ - .5f);
            if ((guarded - transform.position).sqrMagnitude > .000001f)
                controller.Move(guarded - transform.position);
        }

        void Update()
        {
            if (game == null || valley == null || game.Blocked || Locked)
                return;
            float dt = Time.deltaTime;
            Invulnerable = Mathf.Max(0, Invulnerable - dt);
            float h = valley.Height(transform.position);
            Grounded = (controller.isGrounded || transform.position.y <= h + .075f) && Vertical <= 0;
            if (Grounded)
            {
                coyote = .12f;
                doubleUsed = false;
                if (Vertical < 0)
                    Vertical = -2;
            }
            else
                coyote -= dt;
            if (input.Jump.WasPressedThisFrame())
                jumpBuffer = .15f;
            else
                jumpBuffer -= dt;
            var m = input.Move.ReadValue<Vector2>();
            var forward = view.forward;
            forward.y = 0;
            forward.Normalize();
            var right = view.right;
            right.y = 0;
            right.Normalize();
            Vector3 direction = Vector3.ClampMagnitude(forward * m.y + right * m.x, 1);
            float target = input.Walk.IsPressed() ? .57f : input.Sprint.IsPressed() && game.Stamina > 5 ? 5.3f : 2.45f;
            target *= 1 + game.Profile.upgrades.movement * .03f;
            if (game.Combat.Busy)
                target *= .17f;
            horizontal = Vector3.MoveTowards(horizontal, direction * target, dt * (direction.sqrMagnitude > .01f ? 9 : 12));
            if (input.Dodge.WasPressedThisFrame() && game.Stamina >= 18 && !Dodging)
            {
                game.Stamina -= 18;
                game.Combat.Cancel();
                dodgeDirection = direction.sqrMagnitude > .01f ? direction : transform.forward;
                dodgeTimer = .32f;
                Invulnerable = .36f;
                float side = Vector3.Dot(dodgeDirection, transform.right), front = Vector3.Dot(dodgeDirection, transform.forward);
                animationView.Play(Mathf.Abs(side) > .5f ? side > 0 ? "Dodge_Right" : "Dodge_Left" : front < 0 ? "Dodge_Back" : Speed > 4 ? "Dodge_Sprint" : "Dodge_Forward", .06f, .32f);
                game.Audio.Cue("dash");
            }

            if (jumpBuffer > 0 && (coyote > 0 || (!doubleUsed && game.Profile.upgrades.movement >= 2)))
            {
                game.Combat.Cancel();
                bool second = coyote <= 0;
                Vertical = second ? 7.4f : 7.2f;
                if (second)
                    doubleUsed = true;
                jumpBuffer = 0;
                coyote = 0;
                animationView.Play(second ? "Jump_Double" : Speed > 4 ? "Jump_Sprint" : Speed > 1 ? "Jump_Jog" : "Jump_Standing", .07f);
                game.Fx.Ring(transform.position, new Color(.7f, .85f, .7f), 1.3f);
                game.Audio.Cue("jump");
                Grounded = false;
            }

            float previousY = Vertical;
            Vertical -= 21 * dt;
            if (game.Combat.Attacking && animationView.Current == "AirStrike" && !Grounded)
                Vertical = Mathf.Min(Vertical, -12);
            Vector3 movement = (Dodging ? dodgeDirection * 9 : horizontal) * dt + Vector3.up * Vertical * dt;
            bool wasAir = !Grounded;
            Push(movement);
            h = valley.Height(transform.position);
            if (Vertical <= 0 && (controller.isGrounded || transform.position.y < h + .035f))
            {
                if (transform.position.y < h)
                    controller.Move(Vector3.up * (h - transform.position.y));
                Grounded = true;
                Vertical = -2;
            }

            if (wasAir && Grounded)
            {
                landing = previousY < -9 ? .38f : .20f;
                animationView.Play(previousY < -9 ? "Land_Heavy" : "Land_Soft", .05f, landing);
                game.Audio.Cue("land");
            }

            landing = Mathf.Max(0, landing - dt);
            dodgeTimer = Mathf.Max(0, dodgeTimer - dt);
            Speed = horizontal.magnitude;
            Velocity = horizontal;
            float turn = 0;
            if (direction.sqrMagnitude > .01f && !game.Combat.Busy && !Dodging)
            {
                float angle = Vector3.SignedAngle(transform.forward, direction, Vector3.up);
                turn = angle / 60;
                transform.rotation = Quaternion.RotateTowards(transform.rotation, Quaternion.LookRotation(direction), dt * (Speed > 4 ? 230 : 400));
            }

            if (!Dodging && !game.Combat.Busy && landing <= 0)
                animationView.Locomotion(Speed, turn, !Grounded, Vertical);
            game.Stamina = Mathf.Clamp(game.Stamina + dt * (Speed > 4 ? -7 : 19 + game.Profile.upgrades.stamina), 0, game.MaxStamina);
            game.Energy = Mathf.Min(game.MaxEnergy, game.Energy + dt * (game.InTrial ? 5 : 12));
        }
    }
}
