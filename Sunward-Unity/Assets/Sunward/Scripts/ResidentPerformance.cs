using System.Collections.Generic;
using UnityEngine;

namespace Sunward
{
    // Ambient performances share the existing resident skeleton; they do not
    // replace named dialogue residents or take control of quest state.
    [DefaultExecutionOrder(70)]
    public sealed class ResidentPerformance : MonoBehaviour
    {
        public enum Activity { Conversation, Training, Eating, Violin }
        public Activity activity;
        public ResidentLocomotion gait;
        public Transform instrument, bow;
        public AudioClip conversation, practice, music;
        public int variation;
        static readonly List<ResidentPerformance> residents = new List<ResidentPerformance>();
        AudioSource voice;
        MarketWalker diningWalker;
        Vector3 previous;
        float nextPhrase, previousBeat;
        void OnEnable() { residents.Add(this); }
        void OnDisable() { residents.Remove(this); }
        void Start()
        {
            if (!gait) gait = GetComponentInParent<ResidentLocomotion>();
            if (!gait) { enabled = false; return; }
            previous = gait.transform.position;
            diningWalker = gait.GetComponent<MarketWalker>();
            nextPhrase = Time.time + 1 + variation * .73f;
            voice = gameObject.AddComponent<AudioSource>();
            voice.spatialBlend = 1;
            voice.minDistance = 2;
            voice.maxDistance = activity == Activity.Violin ? 13 : 7;
            voice.rolloffMode = AudioRolloffMode.Linear;
            voice.volume = activity == Activity.Violin ? .14f : .06f;
            if (activity == Activity.Violin && music)
            {
                voice.clip = music;
                voice.loop = true;
                voice.Play();
            }
        }
        void LateUpdate()
        {
            if (!gait || !gait.game) return;
            bool paused = gait.game.Blocked || gait.game.InTrial;
            if (voice && activity == Activity.Violin) voice.volume = paused ? 0 : .14f;
            Vector3 delta = gait.transform.position - previous;
            previous = gait.transform.position;
            if (paused || delta.sqrMagnitude > .000025f) return;
            float t = Time.time + variation * .67f;
            if (activity == Activity.Training)
            {
                float cycle = Mathf.Repeat(t, 3.6f);
                float strike = Mathf.SmoothStep(0, 1, Mathf.Clamp01((cycle - 1.25f) / .22f));
                float recover = Mathf.SmoothStep(0, 1, Mathf.Clamp01((cycle - 1.65f) / .9f));
                float pose = strike * (1 - recover);
                gait.spine.localRotation = Quaternion.Euler(6 + pose * 14, -10 + pose * 19, 0);
                gait.arms[0].localRotation = Quaternion.Euler(-95 + pose * 58, 10, 8);
                gait.arms[1].localRotation = Quaternion.Euler(-100 + pose * 65, -10, -8);
                gait.forearms[0].localRotation = Quaternion.Euler(-26, 0, 0);
                gait.forearms[1].localRotation = Quaternion.Euler(-32, 0, 0);
                if (cycle >= 1.47f && previousBeat < 1.47f && voice && practice) voice.PlayOneShot(practice, .6f);
                previousBeat = cycle;
            }
            else if (activity == Activity.Violin)
            {
                gait.head.localRotation = Quaternion.Euler(7, -17, -8);
                gait.arms[0].localRotation = Quaternion.Euler(-61, -22, -25);
                gait.forearms[0].localRotation = Quaternion.Euler(-55, 0, 0);
                gait.arms[1].localRotation = Quaternion.Euler(-55 + Mathf.Sin(t * 2.7f) * 9, 26, 20);
                gait.forearms[1].localRotation = Quaternion.Euler(-43 + Mathf.Sin(t * 2.7f) * 16, 0, 0);
                if (bow) bow.localPosition = new Vector3(.07f + Mathf.Sin(t * 2.7f) * .075f, .12f, .15f);
            }
            else if (activity == Activity.Eating)
            {
                if (diningWalker && !diningWalker.Dining) return;
                float spoon = (Mathf.Sin(t * .8f) + 1) * .5f;
                gait.arms[1].localRotation = Quaternion.Euler(-38 - spoon * 16, 0, -12);
                gait.forearms[1].localRotation = Quaternion.Euler(-35 - spoon * 35, 0, 0);
                gait.head.localRotation = Quaternion.Euler(9 + spoon * 3, -5, 0);
            }
            else
            {
                ResidentPerformance partner = null;
                float nearest = 3.2f * 3.2f;
                foreach (var other in residents)
                {
                    if (!other || other == this || !other.gait || other.activity != Activity.Conversation) continue;
                    float distance = (other.gait.transform.position - gait.transform.position).sqrMagnitude;
                    if (distance > .25f && distance < nearest) { nearest = distance; partner = other; }
                }
                if (!partner) return;
                Vector3 direction = partner.gait.transform.position - gait.transform.position;
                float yaw = Vector3.SignedAngle(gait.transform.forward, direction, Vector3.up);
                gait.head.localRotation = Quaternion.Euler(Mathf.Sin(t * 2) * 2, Mathf.Clamp(yaw, -42, 42), 0);
                gait.arms[variation % 2].localRotation = Quaternion.Euler(-12 + Mathf.Sin(t * 1.4f) * 7, 0, variation % 2 == 0 ? 8 : -8);
                if (Time.time > nextPhrase)
                {
                    if (voice && conversation) voice.PlayOneShot(conversation, .6f);
                    nextPhrase = Time.time + 7 + variation % 4;
                }
            }
        }
    }
}
