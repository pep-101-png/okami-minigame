using System;
using UnityEngine;

namespace Sunward.Remaster
{
    [DefaultExecutionOrder(50)]
    public sealed class OriginalWeaponView : MonoBehaviour
    {
        NativePaintedRig rig;
        NativePoseBank bank;
        NativePoseBank.Clip idle, action;
        string package, family, actionState;
        float idleTime, actionPhase, blendTime, blendLength,chargeLift,returnLift;
        public float ChargeLift=>chargeLift;
        bool returning, extrasHidden;
        Vector3[] position,scale;
        Quaternion[] rotation;
        SkinnedMeshRenderer[] renderers;
        WolfCombat combat;
        Mesh clearanceMesh;readonly System.Collections.Generic.List<Vector3> clearanceVertices=new System.Collections.Generic.List<Vector3>();
        readonly Vector3[] points=new Vector3[12];
        bool Tundra=>package=="wp2e";
        public void Load(string source,string kind="reflector")
        {
            if(rig!=null)rig.Dispose();
            package=source;family=kind;rig=new NativePaintedRig("Okami/"+source,transform);
            bank=new NativePoseBank("Okami/"+source+"/Poses");
            if(bank.BoneCount!=rig.Bones.Length)throw new InvalidOperationException("Original weapon skeleton mismatch: "+source);
            position=new Vector3[bank.BoneCount];scale=new Vector3[bank.BoneCount];rotation=new Quaternion[bank.BoneCount];
            for(int i=0;i<position.Length;i++){position[i]=rig.Bones[i].localPosition;scale[i]=Vector3.one;rotation[i]=Quaternion.identity;}
            idle=bank.Find(package+(family=="glaive"?"_001":"_000"));
            if(idle==null)throw new InvalidOperationException("Original weapon idle is missing: "+source);
            renderers=rig.Root.GetComponentsInChildren<SkinnedMeshRenderer>(true);
            foreach(var renderer in renderers)
            {renderer.localBounds=new Bounds(Vector3.zero,new Vector3(64,32,64));renderer.updateWhenOffscreen=true;}
            combat=GetComponentInParent<WolfCombat>();
            if(Tundra)
            {
                combat=GetComponentInParent<WolfCombat>();
                foreach(int i in new[]{1,2,3,4,5,6,7,8,12,15})
                    if(bank.Find(package+"_"+i.ToString("x3"))==null)throw new InvalidOperationException("Original Tundra action missing: "+i);
            }
            rig.Root.SetActive(true);Sample(idle,0,true,1);
        }
        string Action(string state)
        {
            if(Tundra)
            {int clip=TundraAttackRules.WeaponClip(state);return clip<0?null:package+"_"+clip.ToString("x3");}
            if(family!="rosary")return null;
            string suffix=state.Substring(state.LastIndexOf('_')+1);
            int index=suffix=="540"?1:suffix=="542"?2:suffix=="544"?3:suffix=="546"?4:suffix=="548"?5:suffix=="54a"?6:suffix=="54b"?8:suffix=="54f"?15:12;
            return package+"_"+index.ToString("x3");
        }
        public float AttackLength(string state)
        {var name=Action(state);var clip=name==null?null:bank.Find(name);return clip==null?0:clip.Duration;}
        void Capture()
        {
            for(int i=0;i<position.Length;i++)
            {position[i]=rig.Bones[i].localPosition;rotation[i]=rig.Bones[i].localRotation;scale[i]=rig.Bones[i].localScale;}
        }
        void ExtraBeads(bool visible)
        {
            extrasHidden=!visible;
            foreach(var renderer in renderers)
            {
                var name=renderer.sharedMesh.name.Split('-');
                if(name.Length>1 && int.TryParse(name[1],out int group) && group>=3)renderer.enabled=visible;
            }
        }
        public void BeginAttack(string state)
        {
            var name=Action(state);action=name==null?null:bank.Find(name);actionState=state;
            if(!Tundra)return;
            if(action==null)throw new InvalidOperationException("Unmapped Tundra attack: "+state);
            // Casts author only bones 1..6. The other six must not pile up at
            // the unanimated origin. Restore hidden bones at rest before a whip.
            if(extrasHidden && state!=TundraAttackRules.Cast)
            {
                var p=new Vector3[position.Length];var r=new Quaternion[position.Length];var s=new Vector3[position.Length];
                for(int i=0;i<p.Length;i++){p[i]=rig.Bones[i].localPosition;r[i]=rig.Bones[i].localRotation;s[i]=rig.Bones[i].localScale;}
                Sample(idle,idleTime,true,1);
                for(int i=0;i<rig.Bones.Length;i++)if(i<8 || i>13){rig.Bones[i].localPosition=p[i];rig.Bones[i].localRotation=r[i];rig.Bones[i].localScale=s[i];}
            }
            Capture();blendTime=0;blendLength=TundraAttackRules.EnterBlend;returning=false;actionPhase=0;
            ExtraBeads(state!=TundraAttackRules.Cast);
        }
        public void AttackPhase(float phase)
        {
            if(Tundra){actionPhase=Mathf.Clamp01(phase);return;}
            if(action!=null)Sample(action,Mathf.Clamp01(phase)*action.Duration,false,1);
        }
        public void EndAttack()
        {
            if(Tundra && rig!=null && action!=null)
            {Capture();returnLift=chargeLift;blendTime=0;blendLength=TundraAttackRules.ReturnBlend;returning=true;}
            action=null;
        }
        void LateUpdate()
        {
            if(rig==null || idle==null)return;
            if(package=="wp29")
            {
                // These are complementary blade/spike sections, not exclusive forms.
                foreach(var r in renderers)r.enabled=true;
            }
            if(!Tundra)
            {if(action!=null)return;idleTime+=Time.deltaTime;Sample(idle,idleTime,true,1);BladeClearance();return;}
            if(combat && combat.game && combat.game.Blocked)return;
            blendTime+=Time.deltaTime;
            float blend=blendLength>0?Mathf.SmoothStep(0,1,blendTime/blendLength):1;
            if(action!=null)
            {
                Sample(action,actionPhase*action.Duration,false,blend);

            }
            else
            {
                idleTime+=Time.deltaTime;Sample(idle,idleTime,true,returning?blend:1);
                if(returning && blend>=1){returning=false;ExtraBeads(true);}
            }
            ChargeClearance();
            if(action!=null)
            {
                int count=TundraAttackRules.VisibleBeads(actionState);for(int i=0;i<count;i++)points[i]=rig.Bones[i+2].TransformPoint(new Vector3(0,0,-.055f));
                if(combat)combat.TundraBeadContacts(points,count);
            }
        }
        void BladeClearance()
        {
            if(package!="wp29")return;rig.Root.transform.localPosition=Vector3.zero;
            if(!combat || !combat.HoldingCharge)return;
            var body=combat.GetComponent<NativeAmaterasu>();if(!body || !body.Ready || !body.Head)return;
            // Preserve the recovered charge pose. Move only the separate weapon
            // skin back over the shoulders, then clear the live skull volume.
            float size=body.FullPower?1.2f:1;float radius=.45f*size;rig.Root.transform.position+=Vector3.up*(.22f*size)-combat.transform.forward*(.5f*size);
            if(!clearanceMesh)clearanceMesh=new Mesh();float lift=0;var head=body.Head.position;
            foreach(var renderer in renderers)if(renderer.enabled)
            {
                renderer.BakeMesh(clearanceMesh);clearanceVertices.Clear();clearanceMesh.GetVertices(clearanceVertices);
                foreach(var vertex in clearanceVertices){var p=renderer.transform.TransformPoint(vertex);float d=(p.x-head.x)*(p.x-head.x)+(p.z-head.z)*(p.z-head.z);if(d<radius*radius)lift=Mathf.Max(lift,head.y+Mathf.Sqrt(radius*radius-d)-p.y);}
            }
            rig.Root.transform.position+=Vector3.up*(lift>0?lift+.025f:0);
        }
        void ChargeClearance()
        {
            rig.Root.transform.localPosition=Vector3.zero;
            // Native PL00_54c + WP2e_00c: source spiral minimum is -0.564 m.
            // Raise only the released cast, with the same enter/return blend as
            // the beads. Held charge still uses the player's anatomical socket.
            float blend=blendLength>0?Mathf.SmoothStep(0,1,blendTime/blendLength):1;
            chargeLift=action!=null && actionState==TundraAttackRules.Cast?.72f*blend:returning?returnLift*(1-blend):0;
            rig.Root.transform.position+=Vector3.up*chargeLift;
        }
        void Sample(NativePoseBank.Clip clip,float time,bool loop,float blend)=>bank.Sample(clip,time,rig.Bones,position,rotation,scale,blend,loop);
        void OnDestroy(){if(clearanceMesh)Destroy(clearanceMesh);if(rig!=null)rig.Dispose();}
    }
}
