using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    public sealed class WolfCombat : MonoBehaviour
    {
        public GameFlow game;
        public WolfMotor motor;
        public WeaponDefinition spear, sundial;
        public Transform headSocket, backSocket;
        public bool Busy => strike != null || charging || voice > 0;
        public bool Attacking => strike != null;

        WeaponDefinition weapon;
        Sunward.Remaster.OriginalWeaponCatalog.Entry originalWeapon;
        Sunward.Remaster.OriginalWeaponView originalView;
        public string EquippedTitle => originalWeapon != null ? originalWeapon.title : "Tsumugari";
        bool Glaive => originalWeapon == null || originalWeapon.family == "glaive";
        Sunward.Remaster.NativeAmaterasu nativeBody;
        Strike strike;
        float elapsed, hold, grace;
        int chain;
        bool heavy, queued, queuedHeavy, charging;
        readonly AttackSequence sequence = new AttackSequence();
        readonly HashSet<EnemyBrain> hit = new HashSet<EnemyBrain>();
        readonly HashSet<Sunward.Remaster.TrainingDummy> dummyHits = new HashSet<Sunward.Remaster.TrainingDummy>();
        readonly Collider[] contacts = new Collider[48];
        float barkCooldown, voice;
        void Start()
        {
            nativeBody=GetComponent<Sunward.Remaster.NativeAmaterasu>();
            if(nativeBody && nativeBody.Ready)backSocket=nativeBody.CreateBackSocket();
            Equip();
        }
        bool CombatArea => game.InTrial || Sunward.Remaster.VillageServices.InDojo(transform.position) || Sunward.Remaster.LowerArena.Inside(transform.position);
        public void Equip()
        {
            Cancel();
            originalWeapon=Sunward.Remaster.OriginalWeaponCatalog.Find(game.Profile.equipped);
            if(originalWeapon==null){game.Profile.equipped="spear";originalWeapon=Sunward.Remaster.OriginalWeaponCatalog.Find("spear");}
            if(weapon && weapon!=spear && weapon!=sundial)Destroy(weapon);
            weapon=Sunward.Remaster.OriginalWeaponCatalog.Definition(originalWeapon,spear,sundial);
            if(originalView){originalView.gameObject.SetActive(false);Destroy(originalView.gameObject);originalView=null;}
            // Start is called after GameFlow Awake; defer attachment until native
            // player Awake has completed. Never instantiate a second legacy view.
            if(!backSocket && nativeBody && nativeBody.Ready)backSocket=nativeBody.CreateBackSocket();
            if(backSocket)
            {
                var obj=new GameObject(originalWeapon.title+" · original instrument");obj.transform.SetParent(backSocket,false);
                originalView=obj.AddComponent<Sunward.Remaster.OriginalWeaponView>();originalView.Load(originalWeapon.resource,originalWeapon.family);
                obj.SetActive(CombatArea && !motor.Locked);
            }
        }
        public void Rest(bool rest)
        {if(originalView)originalView.gameObject.SetActive(!rest && CombatArea && !motor.Locked);}

        public void Cancel()
        {
            strike = null;
            if(originalView)originalView.EndAttack();
            charging = false;
            queued = false;
            chain = 0;
            grace = 0;
            sequence.Reset();
            voice = 0;
            hold = 0;
        }

        void Begin(Strike next)
        {
            float length=nativeBody && nativeBody.Ready?nativeBody.ClipLength(next.clip):next.duration;
            if(originalView)length=Mathf.Max(length,originalView.AttackLength(next.clip));
            strike=new Strike {clip=next.clip,duration=Mathf.Max(.2f,length),damage=next.damage,range=next.range,arc=next.arc,start=next.start,end=next.end,lunge=next.lunge,stagger=next.stagger};
            elapsed = 0;
            hit.Clear();
            dummyHits.Clear();
            charging = false;
            motor.animationView.Play(strike.clip,.06f,strike.duration,true);
            if(originalView)originalView.BeginAttack(strike.clip);
            game.Audio.Cue("weapon-"+originalWeapon.resource+(heavy?"-heavy":""));
            if (originalWeapon.resource=="wp24")
                game.Fx.SundialOrbit(transform.position, heavy);
        }

        void Update()
        {
            if (!game || !CombatArea || game.Blocked || motor.Locked || motor.Swimming)
                return;
            float dt = Time.deltaTime;
            barkCooldown = Mathf.Max(0, barkCooldown - dt);
            grace -= dt;
            voice = Mathf.Max(0, voice - dt);
            if (voice > 0)
                return;
            if (motor.input.Switch.WasPressedThisFrame() && !Busy)
            {
                game.Profile.equipped = Sunward.Remaster.OriginalWeaponCatalog.Next(game.Profile);
                game.Save.Save();
                Equip();
            }

            if (motor.input.Bark.WasPressedThisFrame() && !Busy && barkCooldown <= 0 && game.Energy >= 15)
            {
                game.Energy -= 15;
                barkCooldown = Mathf.Max(2.5f, 6 - game.Profile.upgrades.ability * .45f);
                voice = .55f;
                motor.animationView.Play("Bark", .06f, .55f);
                game.Audio.Cue("bark");
                game.Fx.Ring(transform.position, new Color(.8f, .9f, .7f), 5.5f);
                foreach (var e in game.Enemies)
                    if (Vector3.Distance(e.transform.position, transform.position) < 5.5f)
                        e.Stun(1.1f);
            }

            if (strike != null)
            {
                float previousPhase=elapsed/strike.duration;
                elapsed += dt;
                float p = elapsed / strike.duration;
                if (p > .25f && (motor.input.Light.WasPressedThisFrame() || motor.input.Heavy.WasPressedThisFrame()))
                {
                    queued = true;
                    queuedHeavy = motor.input.Heavy.WasPressedThisFrame();
                }

                motor.Push(transform.forward * (strike.lunge * Mathf.Sin(Mathf.Clamp01(p) * Mathf.PI) * dt));
                if (p >= strike.start && previousPhase <= strike.end)
                    Hit();
                if (p >= 1)
                {
                    strike = null;
                    if(originalView)originalView.EndAttack();
                    grace = .52f;
                    if (queued)
                    {
                        queued = false;
                        heavy = queuedHeavy;
                        chain = sequence.Select(heavy, true, weapon.light.Length, weapon.heavy.Length);
                        Begin((heavy ? weapon.heavy : weapon.light)[chain]);
                    }
                }

                return;
            }

            if (motor.Dodging)
                return;
            if (!charging && (motor.input.Light.WasPressedThisFrame() || motor.input.Heavy.WasPressedThisFrame()))
            {
                if (!motor.Grounded)
                {
                    heavy = motor.input.Heavy.WasPressedThisFrame();
                    sequence.Reset();
                    Begin(weapon.air);
                    return;
                }

                bool requestedHeavy = motor.input.Heavy.WasPressedThisFrame();
                if (requestedHeavy != heavy)
                    grace = 0;
                heavy = requestedHeavy;
                charging = true;
                hold = 0;
            }

            if (charging)
            {
                hold += dt;
                bool pressed = heavy ? motor.input.Heavy.IsPressed() : motor.input.Light.IsPressed();
                if (hold > .28f)
                {
                    motor.animationView.Play("NativeCharge_"+originalWeapon.family);
                    if(nativeBody)nativeBody.HoldChargePose();
                }
                if (!pressed)
                {
                    if (hold > .28f)
                    {
                        chain = 0;
                        sequence.Reset();
                        Begin(heavy ? weapon.chargedHeavy : weapon.charged);
                    }
                    else
                    {
                        chain = sequence.Select(heavy, grace > 0, weapon.light.Length, weapon.heavy.Length);
                        Begin((heavy ? weapon.heavy : weapon.light)[chain]);
                    }
                }
            }
        }

        void LateUpdate()
        {
            if(!originalView || !game)return;
            bool show=CombatArea && !motor.Locked && game.Panel!="result";
            if(originalView.gameObject.activeSelf!=show)originalView.gameObject.SetActive(show);
            if(strike!=null)originalView.AttackPhase(elapsed/Mathf.Max(.001f,strike.duration));
        }

        void Hit()
        {
            int n = Physics.OverlapSphereNonAlloc(transform.position + Vector3.up * .6f, strike.range, contacts, 1 << 8, QueryTriggerInteraction.Collide);
            for (int i = 0; i < n; i++)
            {
                var dummy = contacts[i].GetComponentInParent<Sunward.Remaster.TrainingDummy>();
                if (dummy && !dummyHits.Contains(dummy))
                {
                    Vector3 toward = dummy.transform.position - transform.position; toward.y = 0;
                    if (toward.sqrMagnitude < .01f || Vector3.Dot(transform.forward,toward.normalized) >= strike.arc)
                    { dummyHits.Add(dummy); dummy.Strike(); }
                    continue;
                }
                var e = contacts[i].GetComponentInParent<EnemyBrain>();
                if (!e || e.Dead || hit.Contains(e))
                    continue;
                var d = e.transform.position - transform.position;
                d.y = 0;
                if (d.sqrMagnitude > .01f && Vector3.Dot(transform.forward, d.normalized) < strike.arc)
                    continue;
                if (Physics.Linecast(transform.position + Vector3.up * .7f, e.transform.position + Vector3.up * .7f, 1 << 6, QueryTriggerInteraction.Ignore))
                    continue;
                hit.Add(e);
                float mul = 1 + (ProgressionRules.Level(game.Profile) - 1) * .045f + game.Profile.upgrades.strength * .18f;
                mul *= 1 + (Glaive ? game.Profile.upgrades.spear * .12f : game.Profile.upgrades.sundial * .14f);
                e.Damage(strike.damage * mul, d.normalized, strike.stagger);
                game.Fx.Impact(e.transform.position + Vector3.up * .8f, Glaive ? new Color(.9f, .75f, .48f) : new Color(1, .38f, .13f));
                game.Audio.Cue(heavy ? "heavy-impact" : originalWeapon.family=="reflector" ? "flame-impact" : "impact");
                game.HitPause(heavy ? .065f : .04f);
            }
        }
    }
}
