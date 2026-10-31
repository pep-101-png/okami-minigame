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
        // Snapshot durations when states begin. Phase-two health changes must
        // not move the visible attack backwards while its timer is running.
        float visualDuration=.9f;
        public float VisualStateDuration => visualDuration;
        public bool VisualStunned => !Dead && stun>0;

        public float VisualStateProgress => Mathf.Clamp01(1 - timer / Mathf.Max(.001f, VisualStateDuration));

        CharacterController motor;
        Transform visual;
        Vector3 direction;
        float timer = .9f, stun, clock;
        int attacks;
        string move;
        public string ActiveMove=>move;
        Sunward.Remaster.OriginalActor nativeActor;
        bool struck;
        LineRenderer tell;
        Vector3 visualBase;
        bool originalVisual;
        float nativeAttackLength, chargeRemaining;
        float nextVoice;
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
            visualBase = visual.localPosition;
            var native = visual.GetComponentInChildren<Sunward.Remaster.OriginalActor>(true);
            nativeActor=native;
            originalVisual = native != null;
            if(native && native.Ready && native.splitAttackClip)nativeAttackLength=native.ActivityLength(native.strike);
        }

        public void Stun(float time)
        {
            stun = Mathf.Max(stun, definition.id == "boss" ? Mathf.Min(.30f, time) : time);
        }

        public void Damage(float damage, Vector3 away, float stagger)
        {
            if (Dead)
                return;
            Hp -= damage;
            if (game.Audio && (Dead || Time.time >= nextVoice)) { game.Audio.Enemy(definition.id,transform.position); nextVoice = Time.time + .9f; }
            Stun(stagger);
            if (motor.enabled)
                motor.Move(away * .15f);
            if (Dead)
            {
                State = "dead";
                timer = clock;
                if (tell)
                    Destroy(tell.gameObject);
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

        void Update()
        {
            if (!definition || game.Blocked || !game.InTrial)
                return;
            float dt = Time.deltaTime;
            clock += dt;
            if (Dead)
            {
                if (!originalVisual)
                {
                    visual.localScale = Vector3.one * definition.scale * Mathf.Max(0, 1 - (clock - timer));
                    visual.Rotate(0, dt * 40, 0);
                }
                return;
            }

            Vector3 diff = game.Player.transform.position - transform.position;
            diff.y = 0;
            float distance = diff.magnitude;
            bool boss = definition.id == "boss", ranged = definition.id == "ranged";
            if (diff.sqrMagnitude > .01f)
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(diff), dt * 7);
            if (!originalVisual)
            {
                visual.localPosition = visualBase + Vector3.up * (definition.id == "wisp" || ranged ? .12f + Mathf.Sin(clock * 4) * .10f : Mathf.Abs(Mathf.Sin(clock * 6)) * .035f);
                visual.localRotation = Quaternion.Euler(State == "windup" ? -12 : Mathf.Sin(clock * 5) * 3, 0, State == "approach" ? Mathf.Sin(clock * 6) * 3 : 0);
            }
            if (stun > 0)
            {
                stun -= dt;
                return;
            }

            timer -= dt;
            if (State == "approach")
            {
                float reach = ranged ? 9 : boss ? 4 : definition.id == "heavy" ? 2.8f : 2;
                if (distance > reach)
                    Move(diff.normalized * definition.speed * (Phase2 ? 1.2f : 1) * dt);
                else if (ranged && distance < 5)
                    Move(-diff.normalized * dt * 1.5f);
                if (timer <= 0 && distance < reach + 1)
                {
                    attacks++;
                    direction = diff.normalized;
                    move = boss ? new[]
                    {
                        "charge",
                        "slam",
                        "fan"
                    }[attacks % 3] : ranged ? "shot" : definition.id == "heavy" ? "slam" : "charge";
                    if(nativeActor && nativeActor.Ready && nativeActor.splitAttackClip)nativeAttackLength=nativeActor.ActivityLength(nativeActor.AttackMotion(move));
                    State = "windup";
                    timer = Mathf.Max(definition.windup * (Phase2 ? .8f : 1),nativeAttackLength*.25f);
                    visualDuration=timer;
                    struck = false;
                    tell = game.Fx.Ring(move == "slam" ? transform.position : game.Player.transform.position, new Color(.75f, .24f, .17f), move == "slam" ? (boss ? 5 : 3) : .7f, timer + .1f);
                }
            }
            else if (State == "windup" && timer <= 0)
            {
                State = "strike";
                game.Audio.World("attack",transform.position,12,.18f);
                chargeRemaining = move == "charge" ? (boss ? .65f : .32f) : 0;
                timer = Mathf.Max(move == "charge" ? chargeRemaining : .18f,nativeAttackLength*.37f);
                visualDuration=timer;
                if (move == "fan" || move == "shot")
                {
                    int count = move == "fan" ? (Phase2 ? 7 : 5) : 1;
                    for (int i = 0; i < count; i++)
                        game.Projectile(transform.position + Vector3.up, Quaternion.Euler(0, (i - (count - 1) * .5f) * 14, 0) * direction, definition.damage);
                    struck = true;
                }

                if (move == "slam")
                {
                    game.Fx.Ring(transform.position, new Color(.7f, .36f, .22f), boss ? 5 : 3);
                    game.Audio.World("heavy-impact",transform.position,16,.22f);
                    if (distance < (boss ? 5 : 3) && game.Player.transform.position.y < .9f)
                        game.Hurt(definition.damage, direction);
                    struck = true;
                }
            }
            else if (State == "strike")
            {
                if (move == "charge" && chargeRemaining>0)
                {
                    Vector3 before = transform.position;
                    float chargeStep=Mathf.Min(dt,chargeRemaining);chargeRemaining-=chargeStep;
                    Move(direction * chargeStep * (boss ? 10 : 7));
                    Vector3 a = game.Player.transform.position - before, travel = transform.position - before;
                    float t = travel.sqrMagnitude < .0001f ? 0 : Mathf.Clamp01(Vector3.Dot(a, travel) / travel.sqrMagnitude);
                    if (!struck && Vector3.Distance(before + travel * t, game.Player.transform.position) < (boss ? 2 : 1.1f))
                    {
                        game.Hurt(definition.damage, direction);
                        struck = true;
                    }
                }

                if (timer <= 0)
                {
                    State = "recover";
                    timer = Mathf.Max(boss ? .95f : .65f,nativeAttackLength*.38f);
                    visualDuration=timer;
                }
            }
            else if (State == "recover" && timer <= 0)
            {
                State = "approach";
                timer = boss ? .4f : .6f;
            }
        }
    }
}
