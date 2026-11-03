using UnityEngine;

namespace Sunward
{
    public sealed class EnemyBrain : MonoBehaviour
    {
        public GameFlow game;
        public EnemyDefinition definition;
        public float Hp, MaxHp;
        readonly Sunward.Remaster.CrimsonPhaseState crimson=new Sunward.Remaster.CrimsonPhaseState();
        public bool BossRising=>definition && definition.id=="boss" && crimson.Transitioning;
        public int BossPhase=>definition && definition.id=="boss"?crimson.Phase:0;
        public float BossScale=>crimson.ScaleMultiplier;
        public bool FlamePhase=>definition && definition.id=="boss" && crimson.Stage==Sunward.Remaster.CrimsonStage.Flame;
        public float AttackDamage=>definition.damage*crimson.DamageMultiplier;
        public bool Dead => Hp <= 0;
        public bool Phase2 => definition.id == "boss" && (FlamePhase || Hp < MaxHp * .5f);
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
        float nextVoice,nextStagger;
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
            if(spec.id=="boss")gameObject.AddComponent<Sunward.Remaster.CrimsonHelmAscension>().Initialise(this,nativeActor);
        }

        public void Stun(float time)
        {
            if(definition.id=="boss")
            {
                // Damage remains valid, but ordinary bead contacts cannot restart
                // every windup or extend one flinch into a permanent stun lock.
                if(BossRising || State=="windup" || State=="strike" || Time.time<nextStagger || time<=0)return;
                nextStagger=Time.time+2.5f;time=Mathf.Min(.12f,time);
            }
            if(definition.id!="boss"){if(Time.time<nextStagger)return;nextStagger=Time.time+.45f;time=Mathf.Min(.18f,time);}
            stun=Mathf.Max(stun,time);
        }

        public void Damage(float damage, Vector3 away, float stagger)
        {
            if (Dead || BossRising || game.CinematicActive)
                return;
            Hp -= damage;
            if(Hp<=0 && definition.id=="boss" && crimson.TryRise())
            {
                Hp=MaxHp;State="transform";stun=chargeRemaining=0;struck=true;
                if(tell){Destroy(tell.gameObject);tell=null;}
                var sequence=GetComponent<Sunward.Remaster.CrimsonHelmAscension>();
                if(!sequence)sequence=gameObject.AddComponent<Sunward.Remaster.CrimsonHelmAscension>();
                sequence.Begin(this,nativeActor);return;
            }
            if (game.Audio && (Dead || Time.time >= nextVoice)) { game.Audio.Enemy(definition.id,transform.position); nextVoice = Time.time + .9f; }
            Stun(stagger);
            if (motor.enabled && definition.id!="boss")
                motor.Move(away * .15f);
            if (Dead)
            {
                if(definition.id=="boss")crimson.Defeat();
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

        public void SetRebirthScale(float multiplier)
        {
            visual.localScale=Vector3.one*(definition.scale*multiplier);
            motor.height=3.6f*multiplier;motor.radius=multiplier;motor.center=Vector3.up*(motor.height*.5f);
            GroundBoss();
        }
        public void CompleteRebirth()
        {
            crimson.Ignite();SetRebirthScale(crimson.ScaleMultiplier);State="approach";timer=.8f;visualDuration=.8f;
            stun=chargeRemaining=0;struck=false;
        }

        void GroundBoss()
        {
            if(!definition || definition.id!="boss" || !game || !game.valley)return;
            var p=transform.position;if(!Sunward.Remaster.LowerArena.Height(p,out var floor))return;
            if(Mathf.Abs(p.y-floor)>.025f)
            {bool enabled=motor.enabled;motor.enabled=false;p.y=floor+.015f;transform.position=p;motor.enabled=enabled;}
        }
        void Move(Vector3 delta)
        {
            motor.Move(delta);
            var p = transform.position;
            var d = p - new Vector3(35, p.y, 0);
            float radius=game.BossTrial?Mathf.Min(29,31-motor.radius-.6f):16.8f;
            if (d.magnitude > radius)
                motor.Move(new Vector3(35, p.y, 0) + d.normalized * radius - p);
            GroundBoss();
        }

        void Update()
        {
            if (!definition || game.Blocked || !game.InTrial)
                return;
            GroundBoss();
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
            if ((State=="approach" || State=="recover") && diff.sqrMagnitude > .01f)
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
                float reach = ranged ? 9 : boss ? 4*BossScale : definition.id == "heavy" ? 2.8f : 2;
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
                    }[attacks % 3] : ranged ? "shot" : "melee";
                    if(nativeActor && nativeActor.Ready && nativeActor.splitAttackClip)nativeAttackLength=nativeActor.ActivityLength(nativeActor.AttackMotion(move));
                    State = "windup";
                    timer = Mathf.Max(definition.windup * (Phase2 ? .8f : 1),nativeAttackLength*.25f);
                    visualDuration=timer;
                    struck = false;
                    tell = game.Fx.Ring(move == "slam" ? transform.position : game.Player.transform.position, new Color(.75f, .24f, .17f), move == "slam" ? (boss ? 5*BossScale : 3) : .7f, timer + .1f);
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
                    Vector3 origin=transform.position+Vector3.up*(1.5f*BossScale);
                    Vector3 aim=boss?(game.Player.transform.position+Vector3.up*.7f-origin).normalized:direction;
                    for (int i = 0; i < count; i++)
                        game.Projectile(origin,Quaternion.Euler(0,(i-(count-1)*.5f)*14,0)*aim,AttackDamage,BossPhase!=2 && boss);
                    struck = true;
                }

                if (move == "slam")
                {
                    game.Fx.Ring(transform.position, new Color(.7f, .36f, .22f), boss ? 5*BossScale : 3);
                    game.Audio.World("heavy-impact",transform.position,16,.22f);
                    if (distance < (boss ? 5*BossScale : 3) && game.Player.transform.position.y < transform.position.y+.9f)
                        game.Hurt(AttackDamage, direction);
                    struck = true;
                }
            }
            else if (State == "strike")
            {
                // Normal imps swing in place; controller lunges previously slid
                // their stationary native weapon actions through the player.
                if(move=="melee" && !struck && VisualStateProgress>=.55f)
                {
                    struck=true;float reach=definition.id=="heavy"?3.2f:2.6f;
                    if(distance<reach && Mathf.Abs(game.Player.transform.position.y-transform.position.y)<1.25f)
                    {game.Hurt(AttackDamage,direction);game.Audio.World(definition.id=="heavy"?"heavy-impact":"impact",transform.position,12,.18f);}
                }
                if (move == "charge" && chargeRemaining>0)
                {
                    Vector3 before = transform.position;
                    float chargeStep=Mathf.Min(dt,chargeRemaining);chargeRemaining-=chargeStep;
                    Move(direction * chargeStep * (boss ? 10 : 7));
                    Vector3 a = game.Player.transform.position - before, travel = transform.position - before;
                    float t = travel.sqrMagnitude < .0001f ? 0 : Mathf.Clamp01(Vector3.Dot(a, travel) / travel.sqrMagnitude);
                    if (!struck && Vector3.Distance(before + travel * t, game.Player.transform.position) < (boss ? 2*BossScale : 1.1f))
                    {
                        game.Hurt(AttackDamage, direction);
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
