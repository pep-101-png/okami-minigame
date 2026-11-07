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
        public float walkMetresPerSecond=.75f;
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
                renderer.enabled=phase==3?group==1:group==0 || group==2 || (phase==2 && group==3);
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
        public float seatedArmRate=1,seatedArmPause;
        public string seatedHeadMotion;
        public float seatedHeadWeight=.65f;
        public float ActivityLength(string name) => bank!=null && bank.Find(name)!=null?bank.Find(name).Duration:0;
        public void PlayActivity(string name,bool loop,float rate=1,float phase=0)
        {
            if(!Ready || string.IsNullOrEmpty(name) || bank.Find(name)==null)return;
            activity=name;activityLoop=loop;activityRate=rate;Change(name);
            time=Mathf.Clamp01(phase)*current.Duration;
        }
        public void EndActivity(){activity=null;Change(idle);}

        public ImpMotionProfile Imp { get; private set; }
        public float ImpWorldScale=>modelScale*(enemy && enemy.definition?enemy.definition.scale:Mathf.Abs(transform.localScale.y));
        public float CurrentSourceTime { get; private set; }
        bool cannonPending;Vector3 cannonTarget;float cannonDamage;
        public Vector3 CannonMuzzle=>NativeBone(21)?NativeBone(21).TransformPoint(Imp.cannon.Muzzle):transform.position+Vector3.up;
        public void QueueCannon(Vector3 target,float damage){cannonPending=true;cannonTarget=target;cannonDamage=damage;}
        string impState,impSoundClip;float impSoundTime=-.001f,impPoseTime;
        void TickImp(float dt,float speed)
        {
            if(enemy.Frozen || (game && game.Blocked && !enemy.Dead))return;
            string state=enemy.State;
            bool locomotion=state=="approach";
            string selected=Imp.Clip(state,enemy.ActiveMove) ?? (locomotion && speed>.08f?walk:idle);
            bool loop=locomotion;
            bool continuingAttack=(impState=="windup" || impState=="strike") && (state=="strike" || state=="recover") && selected==CurrentSourceMotion;
            if(impState!=state){if(!continuingAttack)impPoseTime=0;impState=state;}
            if(selected!=CurrentSourceMotion)impPoseTime=0;
            Change(selected);blendTime+=dt;
            float sample;
            if(state=="windup" || state=="strike" || state=="recover" || state=="stagger" || state=="aim")
                sample=current.Duration*Imp.Phase(state,enemy.VisualStateProgress,enemy.ActiveMove);
            else
            {
                float metres=Imp.walkDistance*ImpWorldScale;
                float pace=selected==walk?speed*current.Duration/Mathf.Max(.05f,metres):1;
                impPoseTime+=dt*Mathf.Clamp(pace,.25f,4.5f);sample=impPoseTime;
            }
            CurrentSourceTime=loop?Mathf.Repeat(sample,current.Duration):Mathf.Min(sample,current.Duration);
            float blend=Mathf.Clamp01(blendTime/.09f);
            bank.Sample(current,sample,rig.Bones,fromPosition,fromRotation,fromScale,blend,loop);
            // Root X/Z is consumed by EnemyBrain through its CharacterController.
            // Root Y stays in the original bank, so jumping attacks can leave the floor.
            rig.Bones[0].localPosition=new Vector3(0,rig.Bones[0].localPosition.y,0);
            enemy.SetImpHeight(rig.Bones[0].localPosition.y*ImpWorldScale);
            // Release after sampling this frame, so the shell starts at the live
            // barrel mouth instead of yesterday's attachment-pivot pose.
            if(cannonPending)
            {
                if(!enemy.Dead && state=="strike" && Imp.IsCannon(enemy.ActiveMove))ImpCannonProjectile.Spawn(game,CannonMuzzle,cannonTarget,cannonDamage,Imp.cannon);
                cannonPending=false;
            }
            var motion=Imp.Find(selected);float before=impSoundClip==selected?impSoundTime:-.001f;
            if(motion!=null && motion.sounds!=null && game && game.Audio)
                foreach(var e in motion.sounds)
                    if((loop && CurrentSourceTime<before-.01f?e.time>before || e.time<=CurrentSourceTime:e.time>before && e.time<=CurrentSourceTime))
                        game.Audio.World(e.cue,transform.position,18,.42f*e.gain,false,e.pitch>0?e.pitch:1);
            impSoundClip=selected;impSoundTime=CurrentSourceTime;
        }

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
                Imp=ImpMotionProfile.Load(resource);
                bank = new NativePoseBank(resource + "/Poses");
                rig = new NativePaintedRig(resource, transform);
                if (bank.BoneCount != rig.Bones.Length) throw new InvalidOperationException("Original model and motion skeletons disagree: " + resource);
                rig.Root.transform.localPosition = modelOffset;
                rig.Root.transform.localScale = Vector3.one * modelScale;
                fromPosition = new Vector3[bank.BoneCount];
                fromRotation = new Quaternion[bank.BoneCount];
                fromScale = new Vector3[bank.BoneCount];
                if(Imp!=null)foreach(var motion in Imp.motions)if(bank.Find(motion.name)==null)throw new InvalidOperationException("Original imp motion is missing: "+motion.name);
                if (bank.Find(idle) == null) throw new InvalidOperationException("Original idle is missing: " + idle);
                Change(idle);
                bank.Sample(current, 0, rig.Bones, fromPosition, fromRotation, fromScale, 1, true);
                if(enemy)foreach(var renderer in rig.Root.GetComponentsInChildren<SkinnedMeshRenderer>(true))
                {renderer.localBounds=new Bounds(Vector3.zero,Imp!=null?new Vector3(12,12,14):new Vector3(32,24,32));renderer.updateWhenOffscreen=Imp==null;}
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
            bool sunburstFall=enemy && enemy.Dead && game && game.Ultimate && game.Ultimate.Playing;
            float dt = bossCinematic || sunburstFall?Time.unscaledDeltaTime:Time.deltaTime;
            float speed = delta.magnitude < 1 ? delta.magnitude / Mathf.Max(dt, .0001f) : 0;
            filteredSpeed=Mathf.Lerp(filteredSpeed,speed,1-Mathf.Exp(-dt*10));
            moving=filteredSpeed>(moving?.08f:.15f);
            running=filteredSpeed>(running?2.8f:3.4f);
            if(enemy && Imp!=null){TickImp(dt,speed);return;}
            string state = enemy ? (enemy.VisualStunned?"hit":enemy.State) : "village";
            string selected = moving ? walk : idle;
            bool loop = true;
            if (holdIdlePose && selected == idle) loop = false;
            float duration = 0;
            if (enemy)
            {
                if (!game) game = enemy.game;
                if(state=="hit"){selected=bank.Find("em00_020")!=null?"em00_020":idle;duration=.22f;loop=false;}
                else if (state == "windup") { selected = splitAttackClip?AttackMotion(enemy.ActiveMove):windup; duration = enemy.VisualStateDuration; loop = false; }
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
            if ((bossCinematic || !game || !game.Blocked) && (!enemy || !enemy.VisualStunned || state=="hit"))
            {
                float pace=bossCinematic?1:duration>.001f?current.Duration/duration:enemy && moving?Mathf.Clamp(filteredSpeed/(running && run!=walk?4.5f:2),.4f,1.5f):!string.IsNullOrEmpty(activity)?activityRate:moving?Mathf.Clamp(filteredSpeed/Mathf.Max(.1f,walkMetresPerSecond),.3f,1.6f):1;
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
            if(!string.IsNullOrEmpty(seatedHeadMotion) && activity!=null)bank.SampleHeadRotations(bank.Find(seatedHeadMotion),time,rig.Bones,seatedHeadWeight);
            if(!string.IsNullOrEmpty(seatedArmMotion) && activity!=null)
            {
                var gesture=bank.Find(seatedArmMotion);
                if(gesture!=null)
                {
                    float gesturePhase=Mathf.Repeat(time*seatedArmRate,gesture.Duration+seatedArmPause);
                    float fade=seatedArmPause>0?Mathf.SmoothStep(0,1,gesturePhase/.2f)*Mathf.SmoothStep(0,1,(gesture.Duration-gesturePhase)/.25f):1;
                    if(gesturePhase<gesture.Duration)bank.SampleArmRotations(gesture,gesturePhase,rig.Bones,seatedArmWeight*fade);
                }
            }
        }

        void OnDestroy() { if(crimsonBody!=null){crimsonBody.Dispose();if(crimsonArmour!=null)crimsonArmour.Dispose();}else if(rig!=null)rig.Dispose(); }
    }
}
