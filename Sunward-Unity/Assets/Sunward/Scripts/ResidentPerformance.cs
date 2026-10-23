using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    [DefaultExecutionOrder(70)]
    public sealed class ResidentPerformance : MonoBehaviour
    {
        public enum Activity { Conversation, Training, Eating, Violin }
        public Activity activity;
        public ResidentLocomotion gait;
        public Transform instrument, bow, practiceSword, mealBowl, teaCup;
        public AudioClip conversation, practice, music;
        public int variation;
        static readonly List<ResidentPerformance> residents = new List<ResidentPerformance>();
        AudioSource voice;
        MarketWalker diningWalker;
        Vector3 previous;
        float nextPhrase, previousBeat;
        void OnEnable() { residents.Add(this); }
        void OnDisable() { residents.Remove(this); if (gait) gait.Seated = false; }
        void Start()
        {
            if (!gait) gait = GetComponentInParent<ResidentLocomotion>();
            if (!gait) { enabled = false; return; }
            previous = gait.transform.position;
            diningWalker = gait.GetComponent<MarketWalker>();
            foreach (var prop in new[] { instrument, bow, practiceSword, mealBowl, teaCup })
                if (prop) prop.SetParent(gait.transform, true);
            nextPhrase = Time.time + 1 + variation * .73f;
            voice = gameObject.AddComponent<AudioSource>();
            voice.playOnAwake = false;
            // The orbit camera is well above the village: a 13m cutoff made the
            // musician inaudible. Gate by player distance and soften camera falloff.
            voice.spatialBlend = activity == Activity.Violin ? .55f : .35f;
            voice.minDistance = 7;
            voice.maxDistance = 36;
            voice.dopplerLevel = 0;
            voice.rolloffMode = AudioRolloffMode.Linear;
            voice.volume = 0;
            if (activity == Activity.Violin && music)
            {
                voice.clip = music;
                voice.loop = true;
                voice.Play();
            }
        }
        void Prop(Transform prop, Vector3 position, Quaternion rotation)
        {
            if (prop) prop.SetPositionAndRotation(gait.transform.TransformPoint(position), gait.transform.rotation * rotation);
        }
        Vector3 Hand(int side)
        {
            return gait.forearms[side].TransformPoint(new Vector3(side == 0 ? -.10f : .10f, -.24f, .052f));
        }
        void Reach(int side, Vector3 target)
        {
            var upper = gait.arms[side]; var lower = gait.forearms[side];
            Vector3 start = upper.position, hand = Hand(side), delta = target - start;
            float l1 = Vector3.Distance(start, lower.position), l2 = Vector3.Distance(lower.position, hand);
            if (delta.sqrMagnitude < .00001f || l1 < .001f || l2 < .001f) return;
            Vector3 axis = delta.normalized;
            LimbArc.Solve(l1, l2, delta.magnitude, out float along, out float bend, out float reach);
            Vector3 pole = Vector3.ProjectOnPlane(gait.transform.right * (side == 0 ? -1 : 1) - gait.transform.up * .2f, axis);
            if (pole.sqrMagnitude < .0001f) pole = Vector3.ProjectOnPlane(gait.transform.forward, axis);
            Vector3 elbow = start + axis * along + pole.normalized * bend;
            upper.rotation = Quaternion.FromToRotation(lower.position - start, elbow - start) * upper.rotation;
            lower.rotation = Quaternion.FromToRotation(Hand(side) - lower.position, start + axis * reach - lower.position) * lower.rotation;
        }
        void LateUpdate()
        {
            if (!gait || !gait.game) return;
            bool paused = gait.game.Blocked || gait.game.InTrial;
            float distance = Vector3.Distance(gait.transform.position, gait.game.Player.transform.position);
            float gain = 1 - Mathf.SmoothStep(0, 1, Mathf.InverseLerp(3, activity == Activity.Violin ? 18 : 8, distance));
            if (voice) voice.volume = Mathf.MoveTowards(voice.volume, paused ? 0 : gain * (activity == Activity.Violin ? .24f : .07f), Time.unscaledDeltaTime * .3f);
            Vector3 delta = gait.transform.position - previous; previous = gait.transform.position;
            bool dining = activity == Activity.Eating && (!diningWalker || diningWalker.Dining) && delta.sqrMagnitude < .000025f;
            gait.Seated = dining;
            if (mealBowl) mealBowl.gameObject.SetActive(dining);
            if (teaCup) teaCup.gameObject.SetActive(dining);
            if (paused || delta.sqrMagnitude > .000025f) return;
            float t = Time.time + variation * .67f;
            if (activity == Activity.Training && practiceSword)
            {
                float cycle = Mathf.Repeat(t, 3.6f);
                float strike = Mathf.SmoothStep(0, 1, Mathf.Clamp01((cycle - 1.25f) / .30f));
                float recover = Mathf.SmoothStep(0, 1, Mathf.Clamp01((cycle - 1.80f) / .9f));
                float pose = strike * (1 - recover);
                gait.spine.localRotation = Quaternion.Euler(2 + pose * 7, 0, 0);
                Prop(practiceSword, new Vector3(0, Mathf.Lerp(1.53f, 1.16f, pose), Mathf.Lerp(.13f, .33f, pose)), Quaternion.Euler(Mathf.Lerp(-18, 63, pose), 0, 0));
                Reach(1, practiceSword.position);
                Reach(0, practiceSword.TransformPoint(Vector3.down * .075f));
                if (cycle >= 1.55f && previousBeat < 1.55f && voice && practice && gain > .01f) voice.PlayOneShot(practice, .42f);
                previousBeat = cycle;
            }
            else if (activity == Activity.Violin && instrument && bow)
            {
                gait.head.localRotation = Quaternion.Euler(5, -15, -7);
                Prop(instrument, new Vector3(-.06f, 1.27f, .23f), Quaternion.Euler(0, 0, 62));
                Prop(bow, new Vector3(.06f + Mathf.Sin(t * 2.3f) * .10f, 1.27f, .30f), Quaternion.Euler(0, 0, -12));
                Reach(0, instrument.TransformPoint(new Vector3(0, .17f, .035f)));
                Reach(1, bow.TransformPoint(new Vector3(.17f, 0, 0)));
            }
            else if (dining)
            {
                float sip = Mathf.SmoothStep(0, 1, Mathf.Max(0, Mathf.Sin(t * .65f)));
                gait.head.localRotation = Quaternion.Euler(5 + sip * 4, -4, 0);
                Prop(mealBowl, new Vector3(-.16f, .73f, .28f), Quaternion.identity);
                Prop(teaCup, new Vector3(.16f, .66f + sip * .40f, .26f), Quaternion.Euler(-sip * 12, 0, 0));
                if (mealBowl) Reach(0, mealBowl.position);
                if (teaCup) Reach(1, teaCup.position);
            }
            else if (activity == Activity.Conversation)
            {
                ResidentPerformance partner = null; float nearest = 3.2f * 3.2f;
                foreach (var other in residents)
                {
                    if (!other || other == this || !other.gait || other.activity != Activity.Conversation) continue;
                    float d = (other.gait.transform.position - gait.transform.position).sqrMagnitude;
                    if (d > .25f && d < nearest) { nearest = d; partner = other; }
                }
                if (!partner) return;
                float yaw = Vector3.SignedAngle(gait.transform.forward, partner.gait.transform.position - gait.transform.position, Vector3.up);
                gait.head.localRotation = Quaternion.Euler(Mathf.Sin(t * 2) * 2, Mathf.Clamp(yaw, -42, 42), 0);
                gait.arms[variation % 2].localRotation = Quaternion.Euler(-12 + Mathf.Sin(t * 1.4f) * 7, 0, variation % 2 == 0 ? 8 : -8);
                if (Time.time > nextPhrase)
                {
                    if (voice && conversation && gain > .01f) voice.PlayOneShot(conversation, .6f);
                    nextPhrase = Time.time + 7 + variation % 4;
                }
            }
        }
    }
}
