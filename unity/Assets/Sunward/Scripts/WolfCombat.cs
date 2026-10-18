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
        GameObject spearView, discView;
        Strike strike;
        float elapsed, hold, grace;
        int chain;
        bool heavy, queued, charging;
        readonly HashSet<EnemyBrain> hit = new HashSet<EnemyBrain>();
        readonly Collider[] contacts = new Collider[48];
        float barkCooldown, voice;
        void Start()
        {
            spearView = Instantiate(spear.visual, headSocket);
            discView = Instantiate(sundial.visual, backSocket);
            discView.transform.localScale = Vector3.one * .9f;
            Equip();
        }

        public void Equip()
        {
            weapon = game.Profile.equipped == "sundial" ? sundial : spear;
            if (spearView)
            {
                spearView.SetActive(weapon == spear);
                discView.SetActive(weapon == sundial);
            }
        }

        public void Rest(bool rest)
        {
            if (spearView)
                spearView.SetActive(!rest && game.Profile.equipped == "spear");
            if (discView)
                discView.SetActive(!rest && game.Profile.equipped == "sundial");
        }

        public void Cancel()
        {
            strike = null;
            charging = false;
            queued = false;
            chain = 0;
            grace = 0;
        }

        void Begin(Strike next)
        {
            strike = next;
            elapsed = 0;
            hit.Clear();
            charging = false;
            motor.animationView.Play(next.clip, .06f, next.duration, true);
            game.Audio.Cue("attack");
        }

        void Update()
        {
            if (!game || game.Blocked || motor.Locked)
                return;
            float dt = Time.deltaTime;
            barkCooldown = Mathf.Max(0, barkCooldown - dt);
            grace -= dt;
            voice = Mathf.Max(0, voice - dt);
            if (voice > 0)
                return;
            if (motor.input.Switch.WasPressedThisFrame() && !Busy && System.Array.IndexOf(game.Profile.owned, "sundial") >= 0)
            {
                game.Profile.equipped = game.Profile.equipped == "spear" ? "sundial" : "spear";
                game.Save.Save();
                Equip();
            }

            if (motor.input.Bark.WasPressedThisFrame() && barkCooldown <= 0 && game.Energy >= 15)
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
                elapsed += dt;
                float p = elapsed / strike.duration;
                if (motor.input.Light.WasPressedThisFrame() || motor.input.Heavy.WasPressedThisFrame())
                    queued = true;
                motor.Push(transform.forward * (strike.lunge * Mathf.Sin(Mathf.Clamp01(p) * Mathf.PI) * dt));
                if (p >= strike.start && p <= strike.end)
                    Hit();
                if (p >= 1)
                {
                    strike = null;
                    grace = .52f;
                    if (queued)
                    {
                        queued = false;
                        chain = (chain + 1) % (heavy ? weapon.heavy.Length : weapon.light.Length);
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
                    Begin(weapon.air);
                    return;
                }

                heavy = motor.input.Heavy.WasPressedThisFrame();
                charging = true;
                hold = 0;
            }

            if (charging)
            {
                hold += dt;
                bool pressed = heavy ? motor.input.Heavy.IsPressed() : motor.input.Light.IsPressed();
                if (hold > .28f)
                    motor.animationView.Play(heavy ? "ChargeHeavy" : "ChargeLight");
                if (!pressed)
                {
                    if (hold > .28f)
                    {
                        chain = 0;
                        Begin(heavy ? weapon.chargedHeavy : weapon.charged);
                    }
                    else
                    {
                        if (grace <= 0)
                            chain = 0;
                        else
                            chain = (chain + 1) % (heavy ? weapon.heavy.Length : weapon.light.Length);
                        Begin((heavy ? weapon.heavy : weapon.light)[chain]);
                    }
                }
            }
        }

        void Hit()
        {
            int n = Physics.OverlapSphereNonAlloc(transform.position + Vector3.up * .6f, strike.range, contacts, 1 << 8, QueryTriggerInteraction.Collide);
            for (int i = 0; i < n; i++)
            {
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
                mul *= 1 + (weapon == spear ? game.Profile.upgrades.spear * .12f : game.Profile.upgrades.sundial * .14f);
                e.Damage(strike.damage * mul, d.normalized, strike.stagger);
                game.Fx.Impact(e.transform.position + Vector3.up * .8f, weapon == spear ? new Color(.9f, .75f, .48f) : new Color(1, .38f, .13f));
                game.Audio.Cue("impact");
                game.HitPause(.04f);
            }
        }
    }
}
