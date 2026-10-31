using System;
using UnityEngine;

namespace Sunward.Remaster
{
    // The existing controller/EnemyBrain/VillageResident still owns gameplay.
    // Only original MD skinning and sampled MOT transforms drive the appearance.
    [DefaultExecutionOrder(40)]
    public sealed class OriginalActor : MonoBehaviour
    {
        public string resource, idle, walk, run, windup, strike, recover, death;
        public Vector3 modelOffset;
        public float modelScale = 1;
        public bool splitAttackClip;
        public string chargeAttack,slamAttack,rangedAttack;
        public string AttackMotion(string move)=>move=="charge" && !string.IsNullOrEmpty(chargeAttack)?chargeAttack:move=="slam" && !string.IsNullOrEmpty(slamAttack)?slamAttack:(move=="shot" || move=="fan") && !string.IsNullOrEmpty(rangedAttack)?rangedAttack:strike;
        public bool holdIdlePose;
        public GameFlow game;
        public bool Ready { get; private set; }
        public string CurrentSourceMotion { get; private set; }
        NativePaintedRig rig;
        NativePoseBank bank;
        NativePoseBank.Clip current;
        EnemyBrain enemy;
        Vector3 previous;
        Vector3[] fromPosition, fromScale;
        Quaternion[] fromRotation;
        float time, blendTime, filteredSpeed;
        bool moving, running;
        string activity;
        float activityRate=1;
        bool activityLoop;
        public string seatedArmMotion;
        public float ActivityLength(string name) => bank!=null && bank.Find(name)!=null?bank.Find(name).Duration:0;
        public void PlayActivity(string name,bool loop,float rate=1,float phase=0)
        {
            if(!Ready || string.IsNullOrEmpty(name) || bank.Find(name)==null)return;
            activity=name;activityLoop=loop;activityRate=rate;Change(name);
            time=Mathf.Clamp01(phase)*current.Duration;
        }
        public void EndActivity(){activity=null;Change(idle);}

        string lastState;

        void Awake()
        {
            foreach (var renderer in GetComponentsInChildren<Renderer>(true)) renderer.enabled = false;
            var improvised = GetComponent<ResidentLocomotion>();
            if (improvised) improvised.enabled = false;
            enemy = GetComponentInParent<EnemyBrain>();
            if (!game)
            {
                var resident = GetComponent<VillageResident>();
                if (resident) game = resident.game;
                else if (enemy) game = enemy.game;
            }
            previous = transform.position;
            try
            {
                bank = new NativePoseBank(resource + "/Poses");
                rig = new NativePaintedRig(resource, transform);
                if (bank.BoneCount != rig.Bones.Length) throw new InvalidOperationException("Original model and motion skeletons disagree: " + resource);
                rig.Root.transform.localPosition = modelOffset;
                rig.Root.transform.localScale = Vector3.one * modelScale;
                fromPosition = new Vector3[bank.BoneCount];
                fromRotation = new Quaternion[bank.BoneCount];
                fromScale = new Vector3[bank.BoneCount];
                if (bank.Find(idle) == null) throw new InvalidOperationException("Original idle is missing: " + idle);
                Change(idle);
                bank.Sample(current, 0, rig.Bones, fromPosition, fromRotation, fromScale, 1, true);
                if(enemy)foreach(var renderer in rig.Root.GetComponentsInChildren<SkinnedMeshRenderer>())
                {renderer.localBounds=new Bounds(Vector3.zero,new Vector3(32,24,32));renderer.updateWhenOffscreen=true;}
                rig.Root.SetActive(true);
                Ready = true;
            }
            catch (Exception error)
            {
                if (rig != null) rig.Dispose();
                Debug.LogError("Original Okami actor could not load; gameplay remains active. " + error.Message, this);
            }
        }

        void Change(string name)
        {
            var next = bank.Find(string.IsNullOrEmpty(name) ? idle : name);
            if (next == null) next = bank.Find(idle);
            if (next == current) return;
            for (int i = 0; i < rig.Bones.Length; i++)
            {
                fromPosition[i] = rig.Bones[i].localPosition;
                fromRotation[i] = rig.Bones[i].localRotation;
                fromScale[i] = rig.Bones[i].localScale;
            }
            current = next; CurrentSourceMotion = next.Name; time = blendTime = 0;
        }

        void LateUpdate()
        {
            if (!Ready) return;
            Vector3 delta = transform.position - previous;
            delta.y = 0; previous = transform.position;
            float dt = Time.deltaTime;
            float speed = delta.magnitude < 1 ? delta.magnitude / Mathf.Max(dt, .0001f) : 0;
            filteredSpeed=Mathf.Lerp(filteredSpeed,speed,1-Mathf.Exp(-dt*10));
            moving=filteredSpeed>(moving?.08f:.15f);
            running=filteredSpeed>(running?2.8f:3.4f);
            string state = enemy ? enemy.State : "village";
            string selected = moving ? walk : idle;
            bool loop = true;
            if (holdIdlePose && selected == idle) loop = false;
            float duration = 0;
            if (enemy)
            {
                if (!game) game = enemy.game;
                if (state == "windup") { selected = splitAttackClip?AttackMotion(enemy.ActiveMove):windup; duration = enemy.VisualStateDuration; loop = false; }
                else if (state == "strike") { selected = AttackMotion(enemy.ActiveMove); duration = enemy.VisualStateDuration; loop = false; }
                else if (state == "recover") { selected = splitAttackClip?AttackMotion(enemy.ActiveMove):recover; duration = enemy.VisualStateDuration; loop = false; }
                else if (state == "dead") { selected = death; duration = 1.1f; loop = false; }
                else if (running && !string.IsNullOrEmpty(run)) selected = run;
            }
            if(!enemy && !string.IsNullOrEmpty(activity)){selected=activity;loop=activityLoop;}
            bool gaitChange=enemy && state=="approach" && lastState==state && selected!=CurrentSourceMotion && current!=null;
            float phase=gaitChange?Mathf.Repeat(time,current.Duration)/current.Duration:0;
            Change(selected);
            if(gaitChange)time=phase*current.Duration;
            if (state != lastState) { time = 0; lastState = state; }
            blendTime += dt;
            if ((!game || !game.Blocked) && (!enemy || !enemy.VisualStunned))
            {
                float pace=duration>.001f?current.Duration/duration:enemy && moving?Mathf.Clamp(filteredSpeed/(running?4.5f:2),.4f,1.5f):!string.IsNullOrEmpty(activity)?activityRate:1;
                time+=dt*pace;
            }
            float sampleTime = time;
            if (enemy && splitAttackClip && (state == "windup" || state == "strike" || state == "recover"))
            {
                float start = state == "windup" ? 0 : state == "strike" ? .25f : .62f;
                float end = state == "windup" ? .25f : state == "strike" ? .62f : 1;
                sampleTime = current.Duration * Mathf.Lerp(start, end, enemy.VisualStateProgress);
            }
            bank.Sample(current, sampleTime, rig.Bones, fromPosition, fromRotation, fromScale, Mathf.Clamp01(blendTime / .12f), loop);
            if(!string.IsNullOrEmpty(seatedArmMotion) && activity!=null)
                bank.SampleArmRotations(bank.Find(seatedArmMotion),time,rig.Bones,.7f);
        }

        void OnDestroy() { if (rig != null) rig.Dispose(); }
    }
}
