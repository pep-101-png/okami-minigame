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
        public const float WalkSpeed = LocomotionTuning.WalkSpeed, JogSpeed = LocomotionTuning.JogSpeed, SprintSpeed = LocomotionTuning.SprintSpeed;
        public const float Gravity = 21f;
        public float Speed { get; private set; }
        public float Vertical { get; private set; }

        public float Invulnerable;
        public bool Grounded { get; private set; }
        public bool Swimming { get; private set; }

        public bool Locked;
        public Vector3 Velocity { get; private set; }

        Vector3 horizontal, dodgeDirection;
        WolfBodyCollision bodyCollision;
        float dodgeTimer, coyote, jumpBuffer, landing;
        bool doubleUsed;
        float waterLeap, airborneTime;
        public bool Dodging => dodgeTimer > 0;

        void Awake()
        {
            controller = GetComponent<CharacterController>();
            input = GetComponent<WolfInput>();
            bodyCollision = GetComponent<WolfBodyCollision>();
            if (!bodyCollision)
                bodyCollision = gameObject.AddComponent<WolfBodyCollision>();
        }

        public void Teleport(Vector3 point)
        {
            controller.enabled = false;
            transform.position = point;
            controller.enabled = true;
            horizontal = Vector3.zero;
            Vertical = 0;
            Speed = 0;
            Swimming = false;
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
            controller.Move(bodyCollision ? bodyCollision.Sweep(delta) : delta);
            // The player can now enter the river. NPC navigation keeps its
            // existing dry-land routes; swimming owns the player's buoyancy.
            var guarded = transform.position;
            if (game.InTrial)
            {
                var d = guarded - new Vector3(35, guarded.y, 0);
                float radius=game.BossTrial?29:17;
                if (d.magnitude > radius)
                    guarded = new Vector3(35, guarded.y, 0) + d.normalized * radius;
            }

            guarded=Sunward.Remaster.NativeHomeRoom.Guard(old,guarded);
            guarded=Sunward.Remaster.LowerArena.Guard(guarded);
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
            waterLeap = Mathf.Max(0, waterLeap - dt);
            if (UpdateSwimming(dt)) return;
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
            float target = input.Walk.IsPressed() ? WalkSpeed : input.Sprint.IsPressed() && game.Stamina > 5 ? SprintSpeed : JogSpeed;
            target *= (1 + game.Profile.upgrades.movement * .03f)*game.Combat.FormMultiplier;
            if (game.Combat.Busy)
                target *= .17f;
            horizontal = Vector3.MoveTowards(horizontal, direction * target, dt * (direction.sqrMagnitude > .01f ? 13 : 17));
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
                game.Fx.JumpLeaves(transform.position);
                game.Audio.Cue("jump");
                Grounded = false;
            }

            float previousY = Vertical;
            Vertical -= Gravity * dt;
            if (game.Combat.Attacking && animationView.Current == "AirStrike" && !Grounded)
                Vertical = Mathf.Min(Vertical, -12);
            Vector3 movement = (Dodging ? dodgeDirection * (9*game.Combat.FormMultiplier) : horizontal) * dt + Vector3.up * Vertical * dt;
            bool wasAir = !Grounded;
            if(wasAir)airborneTime+=dt;
            Vector3 beforeMove = transform.position;
            Push(movement);
            h = valley.Height(transform.position);
            if (Vertical <= 0 && (controller.isGrounded || transform.position.y < h + .035f))
            {
                if (transform.position.y < h)
                    controller.Move(Vector3.up * (h - transform.position.y));
                Grounded = true;
                Vertical = -2;
            }

            if (wasAir && Grounded && airborneTime>.12f && previousY < -3)
            {
                landing = previousY < -9 ? .38f : .20f;
                animationView.Play(previousY < -9 ? "Land_Heavy" : "Land_Soft", .05f, landing);
                game.Audio.Cue("land");
            }

            if(Grounded)airborneTime=0;
            landing = Mathf.Max(0, landing - dt);
            dodgeTimer = Mathf.Max(0, dodgeTimer - dt);
            Vector3 actual = (transform.position - beforeMove) / Mathf.Max(dt, .00001f);
            actual.y = 0;
            Speed = Dodging ? horizontal.magnitude : actual.magnitude;
            Velocity = actual;
            float turn = 0;
            if (direction.sqrMagnitude > .01f && !game.Combat.Busy && !Dodging)
            {
                float angle = Vector3.SignedAngle(transform.forward, direction, Vector3.up);
                turn = angle / 60;
                var rotation = Quaternion.RotateTowards(transform.rotation, Quaternion.LookRotation(direction), dt * (Speed > 5 ? 260 : 420));
                if (!bodyCollision || bodyCollision.CanTurn(rotation))
                    transform.rotation = rotation;
            }

            if (!Dodging && !game.Combat.Busy && landing <= 0)
                animationView.Locomotion(Speed, turn, !Grounded, Vertical);
            game.Stamina = Mathf.Clamp(game.Stamina + dt * (Speed/game.Combat.FormMultiplier > 5 ? -7 : 19 + game.Profile.upgrades.stamina), 0, game.MaxStamina);
            game.Energy = Mathf.Min(game.MaxEnergy, game.Energy + dt * (game.InTrial ? 5 : 12));
        }
        bool UpdateSwimming(float dt)
        {
            bool deep = !game.InTrial && !Sunward.Remaster.NativeHomeRoom.At(transform.position) && !Sunward.Remaster.LowerArena.Inside(transform.position) && !Sunward.Remaster.LowerArena.Shaft(transform.position) && Valley.Depth(transform.position) > .42f;
            if (!deep || waterLeap > 0 || transform.position.y > .02f)
            {
                if (Swimming) animationView.Play("Land_Soft", .1f, .2f, true);
                Swimming = false; return false;
            }
            Swimming = true; Grounded = false; doubleUsed = false; dodgeTimer = 0;
            game.Combat.Cancel();
            Vector2 m = input.Move.ReadValue<Vector2>();
            Vector3 forward = view.forward; forward.y = 0; forward.Normalize();
            Vector3 right = view.right; right.y = 0; right.Normalize();
            Vector3 direction = Vector3.ClampMagnitude(forward * m.y + right * m.x, 1);
            horizontal = Vector3.MoveTowards(horizontal, direction * (input.Sprint.IsPressed() ? 2.0f : 1.35f)*game.Combat.FormMultiplier, dt * 5);
            // Put the torso at the waterline so the leg stroke is submerged.
            float surface = Mathf.Max(valley.Height(transform.position)+.03f, -.34f - .38f);
            Vertical = 0;
            Vector3 before = transform.position;
            Push(horizontal * dt + Vector3.up * Mathf.Clamp(surface - before.y, -dt * 3, dt * 3));
            Velocity = (transform.position - before) / Mathf.Max(.001f, dt); Speed = new Vector2(Velocity.x, Velocity.z).magnitude;
            if (direction.sqrMagnitude > .01f) transform.rotation = Quaternion.RotateTowards(transform.rotation, Quaternion.LookRotation(direction), dt * 160);
            animationView.Play(Speed > .15f ? "Swim_Move" : "Swim_Idle", .22f);
            var native = GetComponent<Sunward.Remaster.NativeAmaterasu>();
            if(native)native.SwimSpeed(Speed);
            game.Stamina = Mathf.Min(game.MaxStamina, game.Stamina + dt * 5);
            game.Energy = Mathf.Min(game.MaxEnergy, game.Energy + dt * 8);
            if (input.Jump.WasPressedThisFrame())
            {
                Swimming = false; waterLeap = .65f; Vertical = 6.4f;
                animationView.Play("Jump_Standing", .08f, .35f, true); game.Audio.Cue("water");
            }
            return true;
        }
    }
}
