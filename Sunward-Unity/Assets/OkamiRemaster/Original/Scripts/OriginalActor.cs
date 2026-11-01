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
        public void SetVenueVisible(bool visible){if(rig!=null)foreach(var r in rig.Root.GetComponentsInChildren<Renderer>())r.enabled=visible;}
        public string CurrentSourceMotion { get; private set; }
        NativePaintedRig rig,crimsonBody,crimsonArmour;
        NativePoseBank crimsonArmourBank;
        Vector3[] armourPosition,armourScale;Quaternion[] armourRotation;float armourTime;bool showArmour;
        public Transform NativeBone(int index)=>Ready && rig!=null && index>=0 && index+1<rig.Bones.Length?rig.Bones[index+1]:null;
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
        bool activityLoop,cinematicActivity;
        public void BeginBossCinematic(){cinematicActivity=true;activity="em65_032";activityLoop=false;Change(activity);time=0;}
        public void EndBossCinematic(){cinematicActivity=false;if(Ready)EndActivity();}
        public SkinnedMeshRenderer CrimsonSurface { get; private set; }
        public bool SetCrimsonFlame(bool flame)=>SetCrimsonPhase(flame?3:2);
        public bool SetCrimsonPhase(int phase)
        {
            if(rig==null || resource!="Okami/em11")return false;
            crimsonBody=rig;
            if(phase==1 && crimsonArmour==null)
            {
                // WP19 is Crimson Helm's separate armour, not EM65's beast body.
                // Its first 32 bind bones match EM11; four extra bones animate cloth.
                crimsonArmour=new NativePaintedRig("Okami/crimson-armour",transform);
                crimsonArmourBank=new NativePoseBank("Okami/crimson-armour/Poses");
                armourPosition=new Vector3[crimsonArmourBank.BoneCount];armourScale=new Vector3[crimsonArmourBank.BoneCount];armourRotation=new Quaternion[crimsonArmourBank.BoneCount];
                for(int i=0;i<armourPosition.Length;i++){armourPosition[i]=crimsonArmour.Bones[i].localPosition;armourScale[i]=Vector3.one;armourRotation[i]=Quaternion.identity;}
                foreach(var r in crimsonArmour.Root.GetComponentsInChildren<SkinnedMeshRenderer>(true)){r.localBounds=new Bounds(Vector3.zero,new Vector3(32,24,32));r.updateWhenOffscreen=true;}
                crimsonArmour.Root.transform.localPosition=modelOffset;crimsonArmour.Root.transform.localScale=Vector3.one*modelScale;
            }
            showArmour=phase==1;if(crimsonArmour!=null)crimsonArmour.Root.SetActive(showArmour);
            CrimsonSurface=null;
            foreach(var renderer in rig.Root.GetComponentsInChildren<SkinnedMeshRenderer>(true))
            {
                var parts=renderer.sharedMesh.name.Split('-');if(parts.Length<2 || !int.TryParse(parts[1],out int group))continue;
                renderer.enabled=phase==3?group==1:group==0 || group==2;
                renderer.localBounds=new Bounds(Vector3.zero,new Vector3(32,24,32));renderer.updateWhenOffscreen=true;
                if(renderer.enabled && (!CrimsonSurface || renderer.sharedMesh.vertexCount>CrimsonSurface.sharedMesh.vertexCount))CrimsonSurface=renderer;
            }
            rig.Root.SetActive(true);if(showArmour)SampleArmour(0);return CrimsonSurface;
        }
        void SampleArmour(float dt)
        {
            if(!showArmour || crimsonArmour==null)return;
            armourTime+=dt;crimsonArmourBank.Sample(crimsonArmourBank.Find("wp19_000"),armourTime,crimsonArmour.Bones,armourPosition,armourRotation,armourScale,1,true);
            for(int i=0;i<=32;i++)
            {crimsonArmour.Bones[i].localPosition=rig.Bones[i].localPosition;crimsonArmour.Bones[i].localRotation=rig.Bones[i].localRotation;crimsonArmour.Bones[i].localScale=rig.Bones[i].localScale;}
        }
        public string seatedArmMotion;
        public float seatedArmWeight=.7f;
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
                if(enemy)foreach(var renderer in rig.Root.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                {renderer.localBounds=new Bounds(Vector3.zero,new Vector3(32,24,32));renderer.updateWhenOffscreen=true;}
                if(resource=="Okami/em11")SetCrimsonPhase(enemy?enemy.BossPhase:2);
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
            bool bossCinematic=cinematicActivity && game && game.BossTransformation && game.BossTransformation.Playing;
            float dt = bossCinematic?Time.unscaledDeltaTime:Time.deltaTime;
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
            if(cinematicActivity && activity!=null){selected=activity;loop=false;duration=0;}
            bool gaitChange=enemy && state=="approach" && lastState==state && selected!=CurrentSourceMotion && current!=null;
            float phase=gaitChange?Mathf.Repeat(time,current.Duration)/current.Duration:0;
            Change(selected);
            if(gaitChange)time=phase*current.Duration;
            if (state != lastState) { time = 0; lastState = state; }
            blendTime += dt;
            if ((bossCinematic || !game || !game.Blocked) && (!enemy || !enemy.VisualStunned))
            {
                float pace=bossCinematic?1:duration>.001f?current.Duration/duration:enemy && moving?Mathf.Clamp(filteredSpeed/(running && run!=walk?4.5f:2),.4f,1.5f):!string.IsNullOrEmpty(activity)?activityRate:1;
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
            SampleArmour(dt);
            if(!string.IsNullOrEmpty(seatedArmMotion) && activity!=null)
                bank.SampleArmRotations(bank.Find(seatedArmMotion),time,rig.Bones,seatedArmWeight);
        }

        void OnDestroy() { if(crimsonBody!=null){crimsonBody.Dispose();if(crimsonArmour!=null)crimsonArmour.Dispose();}else if(rig!=null)rig.Dispose(); }
    }
}
