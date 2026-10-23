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
        public Material sundialFlameMaterial;
        public bool Busy => strike != null || charging || voice > 0;
        public bool Attacking => strike != null;

        WeaponDefinition weapon;
        GameObject spearView, discView;
        Transform discAnchor, chest;
        Vector3 chestRestLocal;
        SundialFlames discFlames;
        bool resting;
        Strike strike;
        float elapsed, hold, grace;
        int chain;
        bool heavy, queued, queuedHeavy, charging;
        Vector3 spearRest, discRest;
        Quaternion spearRotation, discRotation;
        readonly AttackSequence sequence = new AttackSequence();
        readonly HashSet<EnemyBrain> hit = new HashSet<EnemyBrain>();
        readonly Collider[] contacts = new Collider[48];
        float barkCooldown, voice;
        void Start()
        {
            spearView = Instantiate(spear.visual, headSocket);
            // Imported disc geometry lies in XY. A dedicated motor-frame pivot
            // prevents legacy socket offsets pulling it below the player.
            discAnchor = new GameObject("Sundial · back shield pivot").transform;
            discAnchor.SetParent(transform, false);
            discView = Instantiate(sundial.visual, discAnchor);
            discView.transform.localScale = Vector3.one * .9f;
            discView.transform.localPosition = Vector3.zero;
            discView.transform.localRotation = Quaternion.identity;
            discFlames = discView.AddComponent<SundialFlames>();
            discFlames.Initialize(sundialFlameMaterial ? sundialFlameMaterial : game.Fx.ink);
            foreach (var bone in motor.animationView.animator.GetComponentsInChildren<Transform>())
                if (bone.name == "DEF_chest") chest = bone;
            chestRestLocal = chest ? transform.InverseTransformPoint(chest.position) : Vector3.zero;
            spearRest = spearView.transform.localPosition;
            discRest = discView.transform.localPosition;
            spearRotation = spearView.transform.localRotation;
            discRotation = discView.transform.localRotation;
            Equip();
        }

        public void Equip()
        {
            weapon = game.Profile.equipped == "sundial" ? sundial : spear;
            if (spearView)
            {
                spearView.SetActive(ShieldPresentationRules.Visible(game.InTrial, resting, motor.Locked, game.Panel == "result") && weapon == spear);
                discView.SetActive(ShieldPresentationRules.Visible(game.InTrial, resting, motor.Locked, game.Panel == "result") && weapon == sundial);
            }
        }

        public void Rest(bool rest)
        {
            resting = rest;
            if (spearView)
                spearView.SetActive(ShieldPresentationRules.Visible(game.InTrial, rest, motor.Locked, game.Panel == "result") && game.Profile.equipped == "spear");
            if (discView)
                discView.SetActive(ShieldPresentationRules.Visible(game.InTrial, rest, motor.Locked, game.Panel == "result") && game.Profile.equipped == "sundial");
        }

        public void Cancel()
        {
            strike = null;
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
            strike = next;
            elapsed = 0;
            hit.Clear();
            charging = false;
            motor.animationView.Play(next.clip, .06f, next.duration, true);
            game.Audio.Cue(heavy ? "heavy" : weapon == sundial ? "flame" : "attack");
            if (weapon == sundial)
                game.Fx.SundialOrbit(transform.position, heavy);
        }

        void Update()
        {
            if (!game || !game.InTrial || game.Blocked || motor.Locked)
                return;
            if (motor.Swimming)
            {
                if (Busy) Cancel();
                return;
            }
            float dt = Time.deltaTime;
            barkCooldown = Mathf.Max(0, barkCooldown - dt);
            grace -= dt;
            voice = Mathf.Max(0, voice - dt);
            if (voice > 0)
                return;
            if (motor.input.Switch.WasPressedThisFrame() && !Busy)
            {
                if (System.Array.IndexOf(game.Profile.owned, "sundial") < 0)
                {
                    game.Notify("Unlock Sundial Flame at Taro for 110 sun coins. Both weapons are displayed at home.");
                    return;
                }

                game.Profile.equipped = game.Profile.equipped == "spear" ? "sundial" : "spear";
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
                elapsed += dt;
                float p = elapsed / strike.duration;
                if (p > .25f && (motor.input.Light.WasPressedThisFrame() || motor.input.Heavy.WasPressedThisFrame()))
                {
                    queued = true;
                    queuedHeavy = motor.input.Heavy.WasPressedThisFrame();
                }

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
                    motor.animationView.Play(heavy ? "ChargeHeavy" : "ChargeLight");
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
            if (!spearView || !discView)
                return;
            bool show = ShieldPresentationRules.Visible(game.InTrial, resting, motor.Locked, game.Panel == "result");
            spearView.SetActive(show && game.InTrial && weapon == spear);
            discView.SetActive(show && weapon == sundial);
            // The legacy socket contains a bind-pose offset that moves below the
            // feet once the imported chest is animated. Mount in the motor frame,
            // with a bounded chest delta, instead of trusting that socket position.
            Vector3 motion = chest ? transform.InverseTransformPoint(chest.position) - chestRestLocal : Vector3.zero;
            motion = Vector3.ClampMagnitude(motion, ShieldPresentationRules.ChestMotionLimit);
            discAnchor.localPosition = new Vector3(0, ShieldPresentationRules.MountHeight, -.10f) + motion;
            discAnchor.localRotation = Quaternion.Euler(ShieldPresentationRules.TiltDegrees, Mathf.Sin(Time.time * 1.7f) * 2, Mathf.Sin(Time.time * 2.1f) * 2);
            float p = strike != null ? Mathf.Clamp01(elapsed / strike.duration) : 0;
            float accent = Mathf.Sin(p * Mathf.PI);
            spearView.transform.localPosition = spearRest + Vector3.back * (strike != null ? accent * (heavy ? .18f : .38f) : 0);
            spearView.transform.localRotation = spearRotation * Quaternion.Euler(heavy ? -22 * accent : 0, strike != null && strike.clip == "Sweep" ? Mathf.Sin(p * Mathf.PI * 2) * 35 : 0, 0);
            // Spin about the disc normal, never orbit the head or imported offsets.
            discView.transform.localPosition = discRest + Vector3.back * (accent * .12f);
            discView.transform.localRotation = discRotation * Quaternion.Euler(heavy ? accent * 14 : accent * -8, accent * 10, strike != null ? p * (heavy ? 1080 : 720) : Time.time * 12);
            discView.transform.localScale = Vector3.one * (.85f + accent * .06f + Mathf.Sin(Time.time * 2) * .008f);
            if (discFlames) discFlames.Intensity = strike != null ? accent : charging ? .5f : 0;
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
                game.Audio.Cue(heavy ? "heavy-impact" : weapon == sundial ? "flame-impact" : "impact");
                game.HitPause(heavy ? .065f : .04f);
            }
        }
    }
}
