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
        float impHeight;
        public float HitHeight=>(motor?motor.height:1.7f)+impHeight;
        public void SetImpHeight(float height){if(!IsImp || !motor)return;float next=Mathf.Max(0,height);if(Mathf.Abs(next-impHeight)<.004f)return;impHeight=next;motor.center=Vector3.up*(motor.height*.5f+impHeight);}
        public bool Frozen=>Time.time<frozenUntil;
        public bool VisualStunned => !Dead && (stun>0 || State=="stagger" || Frozen);
        float frozenUntil,nextFreeze;
        public void Freeze(float duration){if(definition.id=="boss"){Stun(.12f);return;}if(Time.time<nextFreeze)return;frozenUntil=Time.time+Mathf.Min(1.2f,duration);nextFreeze=frozenUntil+2;}

        public float VisualStateProgress => Mathf.Clamp01(1 - timer / Mathf.Max(.001f, VisualStateDuration));

        CharacterController motor;
        Transform visual;
        Vector3 direction,impAim;
        float timer = .9f, stun, clock;
        int attacks;
        string move;
        public string ActiveMove=>move;
        Sunward.Remaster.OriginalActor nativeActor;
        bool IsImp=>nativeActor && nativeActor.Imp!=null;
        string rootMotionState;Vector3 previousAttackRoot;
        void ImpRootMotion()
        {
            if(!IsImp || (State!="windup" && State!="strike" && State!="recover")){rootMotionState=null;return;}
            var profile=nativeActor.Imp;
            if(rootMotionState!=State){rootMotionState=State;previousAttackRoot=profile.Root(State,0,move);}
            Vector3 next=profile.Root(State,VisualStateProgress,move);
            Vector3 delta=transform.rotation*((next-previousAttackRoot)*nativeActor.ImpWorldScale);previousAttackRoot=next;
            if(definition.id=="ranged")
            {
                // Native drum recoil is authored for a much larger battlefield.
                // Consume it through collision/range limits instead of retreating
                // out of the trial and leaving the shot animation off camera.
                Vector3 away=transform.position-game.Player.transform.position;away.y=0;
                if((away+delta).magnitude>Mathf.Max(10,away.magnitude) && Vector3.Dot(delta,away)>0)
                    delta-=away.normalized*Vector3.Dot(delta,away.normalized);
            }
            if(delta.sqrMagnitude>0)Move(delta);
        }
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
            if(IsImp){motor.height=Mathf.Max(.85f,1.7f*nativeActor.ImpWorldScale);motor.radius=Mathf.Clamp(.52f*nativeActor.ImpWorldScale,.24f,.6f);motor.center=Vector3.up*motor.height*.5f;}
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
            if(IsImp)
            {
                if(time<=0 || Time.time<nextStagger || Dead)return;
                nextStagger=Time.time+.75f;State="stagger";timer=visualDuration=.32f;stun=0;struck=true;rootMotionState=null;
                if(tell){Destroy(tell.gameObject);tell=null;}return;
            }
            if(definition.id!="boss"){if(Time.time<nextStagger)return;nextStagger=Time.time+.45f;time=Mathf.Min(.18f,time);}
            stun=Mathf.Max(stun,time);
        }

        public void Damage(float damage, Vector3 away, float stagger)=>ReceiveDamage(damage,away,stagger,false);
        // Only the active sunburst may show its non-boss victims falling during its camera hold.
        public void SunburstHit(Vector3 from)
        {
            if(!game.Ultimate || !game.Ultimate.Playing || !game.Ultimate.Detonated || definition.id=="boss")return;
            ReceiveDamage(MaxHp+1,(transform.position-from).normalized,.7f,true);
        }
        void ReceiveDamage(float damage,Vector3 away,float stagger,bool sunburst)
        {
            if (Dead || BossRising || (game.CinematicActive && !sunburst))
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
            if (!IsImp && game.Audio && (Dead || Time.time >= nextVoice)) { game.Audio.Enemy(definition.id,transform.position); nextVoice = Time.time + .9f; }
            Stun(stagger);
            if (motor.enabled && definition.id!="boss")
                motor.Move(away * .15f);
            if (Dead)
            {
                frozenUntil=stun=0;rootMotionState=null;
                if(definition.id=="boss")crimson.Defeat();
                State = "dead";
                timer = clock;
                if (tell)
                    Destroy(tell.gameObject);
                motor.enabled = false;
                game.Reward(this);
                game.Fx.Ring(transform.position, new Color(.6f, .8f, .65f), 2);
                if(IsImp && game.Audio)game.Audio.World("imp-eb00-0",transform.position,14,.22f);
                Destroy(gameObject, IsImp?1.5f:1.1f);
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

            if(Frozen)return;
            Vector3 diff = game.Player.transform.position - transform.position;
            diff.y = 0;
            float distance = diff.magnitude;
            bool boss = definition.id == "boss", ranged = definition.id == "ranged";
            if ((State=="approach" || (!IsImp && State=="recover")) && diff.sqrMagnitude > .01f)
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
            ImpRootMotion();
            diff=game.Player.transform.position-transform.position;diff.y=0;distance=diff.magnitude;
            if (State == "approach")
            {
                float reach = ranged ? 9 : boss ? 4*BossScale : definition.id == "heavy" ? 2.8f : 2;
                if (distance > reach)
                {
                    float speed=definition.speed;
                    if(IsImp)speed=Mathf.Min(speed,nativeActor.Imp.walkDistance*nativeActor.ImpWorldScale/Mathf.Max(.1f,nativeActor.ActivityLength(nativeActor.walk))*2.4f);
                    Move(diff.normalized * speed * (Phase2 ? 1.2f : 1) * dt);
                }
                else if (ranged && distance < 5)
                    Move(-diff.normalized * dt * 1.5f);
                if (timer <= 0 && distance < reach + (IsImp?.05f:1))
                {
                    attacks++;
                    direction = diff.normalized;
                    move = boss ? new[]
                    {
                        "charge",
                        "slam",
                        "fan"
                    }[attacks % 3] : ranged ? "shot" : "melee";
                    if(IsImp){move=nativeActor.Imp.Choose(attacks,ranged && distance<3.5f);impAim=game.Player.transform.position+Vector3.up*.55f;}
                    if(nativeActor && nativeActor.Ready && nativeActor.splitAttackClip)nativeAttackLength=nativeActor.ActivityLength(nativeActor.AttackMotion(move));
                    State = "windup";
                    timer = Mathf.Max(definition.windup * (Phase2 ? .8f : 1),nativeAttackLength*.25f);
                    if(IsImp)timer=Mathf.Max(definition.windup,nativeActor.Imp.Duration("windup",move));
                    visualDuration=timer;rootMotionState=null;
                    struck = false;
                    tell = game.Fx.Ring(move == "slam" ? transform.position : game.Player.transform.position, new Color(.75f, .24f, .17f), move == "slam" ? (boss ? 5*BossScale : 3) : .7f, timer + .1f);
                }
            }
            else if ((State == "windup" || State=="aim") && timer <= 0)
            {
                if(IsImp && State=="windup" && !string.IsNullOrEmpty(nativeActor.Imp.Clip("aim",move)))
                {State="aim";timer=visualDuration=nativeActor.Imp.Duration("aim",move);return;}
                State = "strike";
                if(!IsImp)game.Audio.World("attack",transform.position,12,.18f);
                chargeRemaining = move == "charge" ? (boss ? .65f : .32f) : 0;
                timer = Mathf.Max(move == "charge" ? chargeRemaining : .18f,nativeAttackLength*.37f);
                if(IsImp)timer=nativeActor.Imp.Duration("strike",move);
                visualDuration=timer;
                if (!IsImp && (move == "fan" || move == "shot"))
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
                if(IsImp && nativeActor.Imp.IsCannon(move) && !struck && VisualStateProgress>=nativeActor.Imp.Contact(move))
                {struck=true;nativeActor.QueueCannon(impAim,AttackDamage);}
                if((move=="melee" || (IsImp && !nativeActor.Imp.IsCannon(move))) && !struck && VisualStateProgress>=(IsImp?nativeActor.Imp.Contact(move):.55f))
                {
                    struck=true;float reach=definition.id=="heavy"?3.2f:2.6f;
                    if(distance<reach && Vector3.Dot(direction,diff.normalized)>.15f && Mathf.Abs(game.Player.transform.position.y-transform.position.y)<1.25f)
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
                    if(IsImp)timer=nativeActor.Imp.Duration("recover",move);
                    visualDuration=timer;
                }
            }
            else if (State == "stagger" && timer<=0){State="approach";timer=.45f;rootMotionState=null;}
            else if (State == "recover" && timer <= 0)
            {
                State = "approach";
                timer = boss ? .4f : .6f;
            }
        }
    }
}
