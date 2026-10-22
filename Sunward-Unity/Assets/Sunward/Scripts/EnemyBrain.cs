using UnityEngine;

namespace Sunward
{
    public sealed class EnemyBrain : MonoBehaviour
    {
        public GameFlow game;
        public EnemyDefinition definition;
        public float Hp, MaxHp;
        public bool Dead => Hp <= 0;
        public bool Phase2 => definition.id == "boss" && Hp < MaxHp * .5f;
        public string State { get; private set; } = "approach";
        public string MoveName => move;
        public float PresentationClock => clock;
        public float MovingSpeed { get; private set; }
        public float StateProgress => Mathf.Clamp01(1 - timer / Mathf.Max(.01f, stateDuration));
        public bool Stunned => stun > 0;

        CharacterController motor;
        Transform visual;
        Vector3 direction, previous, warningCenter;
        float warningRadius;
        float timer = .9f, stateDuration = .9f, stun, clock, fallVelocity;
        int attacks;
        string move;
        bool struck;
        LineRenderer tell, directionTell;
        public void Init(GameFlow flow, EnemyDefinition spec)
        {
            game = flow;
            definition = spec;
            MaxHp = Hp = Mathf.Ceil(spec.hp * (1 + Mathf.Sqrt(game.Profile.wins) * .30f + (ProgressionRules.Level(game.Profile) - 1) * .04f));
            gameObject.layer = 8;
            motor = gameObject.AddComponent<CharacterController>();
            motor.radius = spec.id == "boss" ? 1 : .45f;
            motor.height = spec.id == "boss" ? 3.6f : 1.7f;
            motor.center = Vector3.up * motor.height * .5f;
            visual = Instantiate(spec.visual, transform).transform;
            visual.localScale = Vector3.one * spec.scale;
            var presentation = visual.gameObject.AddComponent<EnemyPresentation>();
            presentation.Initialize(this);
            previous = transform.position;
        }

        void Enter(string state, float duration)
        {
            State = state;
            timer = stateDuration = Mathf.Max(.02f, duration);
        }

        void ClearTell()
        {
            if (tell) Destroy(tell.gameObject);
            if (directionTell) Destroy(directionTell.gameObject);
        }

        public void Stun(float time)
        {
            stun = Mathf.Max(stun, definition.id == "boss" ? Mathf.Min(.30f, time) : time);
            // A stagger interrupts an uncommitted strike; it cannot produce a
            // damage frame after its visible warning has already disappeared.
            if (State == "windup" && definition.id != "boss")
            {
                ClearTell();
                Enter("recover", .55f);
            }
            else if (State == "windup" && definition.id == "boss")
            {
                // Boss stagger pauses its timer: extend the visible ring by
                // the same amount so the actual hit never outlives its tell.
                if (tell) Destroy(tell.gameObject);
                tell = game.Fx.Ring(warningCenter, new Color(.75f, .24f, .17f), warningRadius, timer + stun + .05f);
            }
        }

        public void Damage(float damage, Vector3 away, float stagger)
        {
            if (Dead) return;
            Hp -= damage;
            Stun(stagger);
            if (motor.enabled) motor.Move(away * .15f);
            if (Dead)
            {
                State = "dead";
                timer = clock;
                ClearTell();
                motor.enabled = false;
                game.Reward(this);
                game.Fx.Ring(transform.position, new Color(.6f, .8f, .65f), 2);
                Destroy(gameObject, 1.1f);
            }
        }

        void Move(Vector3 delta)
        {
            motor.Move(delta);
            var p = transform.position;
            var d = p - new Vector3(35, p.y, 0);
            if (d.magnitude > 16.8f)
                motor.Move(new Vector3(35, p.y, 0) + d.normalized * 16.8f - p);
        }

        void DirectionWarning(float length)
        {
            var go = new GameObject("Spirit · committed attack direction");
            directionTell = go.AddComponent<LineRenderer>();
            directionTell.sharedMaterial = game.Fx.ink;
            directionTell.positionCount = 5;
            directionTell.widthMultiplier = .065f;
            directionTell.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            directionTell.receiveShadows = false;
            directionTell.startColor = directionTell.endColor = new Color(.88f, .37f, .14f, .8f);
            Vector3 start = transform.position + Vector3.up * .07f;
            Vector3 end = start + direction * length;
            Vector3 side = Vector3.Cross(Vector3.up, direction) * .3f;
            directionTell.SetPositions(new[] { start, end, end - direction * .5f + side, end, end - direction * .5f - side });
        }

        bool ClearAttack(Vector3 target)
        {
            return !Physics.Linecast(transform.position + Vector3.up * .8f, target + Vector3.up * .6f, 1 << 6, QueryTriggerInteraction.Ignore);
        }

        void Melee(float range, float arc)
        {
            Vector3 d = game.Player.transform.position - transform.position;
            float y = d.y;
            d.y = 0;
            if (d.magnitude < range && y < 1.2f && y > -.7f &&
                (d.sqrMagnitude < .001f || Vector3.Dot(direction, d.normalized) >= arc) && ClearAttack(game.Player.transform.position))
                game.Hurt(definition.damage, direction);
            struck = true;
        }

        void Update()
        {
            if (!definition || !game || game.Blocked || !game.InTrial) return;
            float dt = Time.deltaTime;
            clock += dt;
            MovingSpeed = Vector3.Distance(transform.position, previous) / Mathf.Max(dt, .0001f);
            previous = transform.position;
            if (Dead)
            {
                visual.localScale = Vector3.one * definition.scale * Mathf.Max(0, 1 - (clock - timer));
                return;
            }
            // Ground the collision root even during windup/recovery. Spirit
            // hovering is a visual offset, never a suspended controller.
            fallVelocity = motor.isGrounded && fallVelocity < 0 ? -2 : Mathf.Max(-30, fallVelocity - 21 * dt);
            motor.Move(Vector3.up * fallVelocity * dt);
            if (stun > 0)
            {
                stun -= dt;
                MovingSpeed = 0;
                return;
            }

            Vector3 diff = game.Player.transform.position - transform.position;
            diff.y = 0;
            float distance = diff.magnitude;
            bool boss = definition.id == "boss", ranged = definition.id == "ranged";
            // Commit the facing at windup, so dodging a painted tell is useful.
            if ((State == "approach" || State == "recover") && diff.sqrMagnitude > .01f)
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(diff), dt * 7);
            timer -= dt;
            if (State == "approach")
            {
                float reach = ranged ? 9 : boss ? 4 : definition.id == "heavy" ? 2.8f : 2;
                if (distance > reach)
                    Move(diff.normalized * definition.speed * (Phase2 ? 1.2f : 1) * dt);
                else if (ranged && distance < 5)
                    Move(-diff.normalized * dt * 1.5f);
                if (timer <= 0 && distance < reach + 1 && ClearAttack(game.Player.transform.position))
                {
                    attacks++;
                    direction = diff.sqrMagnitude > .001f ? diff.normalized : transform.forward;
                    move = boss ? new[] { "charge", "slam", "fan" }[attacks % 3] :
                        ranged ? (attacks % 3 == 0 ? "fan" : "shot") :
                        definition.id == "heavy" ? "slam" :
                        definition.id == "wisp" ? "pounce" :
                        definition.id == "elite" ? (attacks % 2 == 0 ? "charge" : "sweep") : "sweep";
                    Enter("windup", definition.windup * (Phase2 ? .8f : 1));
                    struck = false;
                    warningCenter = move == "slam" || move == "sweep" ? transform.position : game.Player.transform.position;
                    warningRadius = move == "slam" ? (boss ? 5 : 3) : move == "sweep" ? 2.2f : .7f;
                    tell = game.Fx.Ring(warningCenter, new Color(.75f, .24f, .17f), warningRadius, stateDuration + .05f);
                    if (move == "charge" || move == "pounce" || move == "shot" || move == "fan") DirectionWarning(boss ? 6 : ranged ? 4 : 2.5f);
                }
            }
            else if (State == "windup" && timer <= 0)
            {
                ClearTell();
                Enter("strike", move == "charge" ? (boss ? .65f : .32f) : move == "pounce" ? .38f : .3f);
                if (move == "fan" || move == "shot")
                {
                    int count = move == "fan" ? (boss ? (Phase2 ? 7 : 5) : 3) : 1;
                    for (int i = 0; i < count; i++)
                        game.Projectile(transform.position + Vector3.up, Quaternion.Euler(0, (i - (count - 1) * .5f) * 14, 0) * direction, definition.damage);
                    struck = true;
                }
            }
            else if (State == "strike")
            {
                if (move == "charge" || move == "pounce")
                {
                    Vector3 before = transform.position;
                    Move(direction * dt * (boss ? 10 : move == "pounce" ? 8 : 7));
                    Vector3 a = game.Player.transform.position - before, travel = transform.position - before;
                    float u = travel.sqrMagnitude < .0001f ? 0 : Mathf.Clamp01(Vector3.Dot(a, travel) / travel.sqrMagnitude);
                    if (!struck && Vector3.Distance(before + travel * u, game.Player.transform.position) < (boss ? 2 : 1.1f) && ClearAttack(game.Player.transform.position))
                    {
                        game.Hurt(definition.damage, direction);
                        struck = true;
                    }
                }
                else if (!struck && StateProgress >= .35f)
                {
                    if (move == "slam")
                    {
                        game.Fx.Ring(transform.position, new Color(.7f, .36f, .22f), boss ? 5 : 3);
                        game.Audio.Cue("land");
                        Melee(boss ? 5 : 3, -1);
                    }
                    else if (move == "sweep")
                    {
                        game.Fx.Ring(transform.position, new Color(.83f, .64f, .3f), 2.2f, .2f);
                        Melee(2.35f, -.1f);
                    }
                }
                if (timer <= 0) Enter("recover", boss ? .95f : .7f);
            }
            else if (State == "recover" && timer <= 0)
                Enter("approach", boss ? .4f : .6f);
        }

        void OnDestroy() { ClearTell(); }
    }
}
