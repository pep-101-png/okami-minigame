using System;
using UnityEngine;

namespace Sunward.Remaster
{
    // Original MOT curves and SEQ sound events, inspected per instrument.
    // Gameplay owns horizontal controller motion; MOT retains its authored leap.
    [Serializable] public sealed class ImpMotionProfile
    {
        [Serializable] public sealed class Sound { public float time,gain,pitch; public string cue; }
        [Serializable] public sealed class Motion
        {
            public string name; public float duration; public float[] rootXZ; public Sound[] sounds;
            public Vector3 Root(float phase)
            {
                int count=rootXZ==null?0:rootXZ.Length/2;if(count<2)return Vector3.zero;
                float f=Mathf.Clamp01(phase)*(count-1);int a=Mathf.FloorToInt(f),b=Mathf.Min(a+1,count-1);float t=f-a;
                return new Vector3(Mathf.Lerp(rootXZ[a*2],rootXZ[b*2],t),0,Mathf.Lerp(rootXZ[a*2+1],rootXZ[b*2+1],t));
            }
        }
        [Serializable] public sealed class Attack
        {
            public string id,kind,windup,strike,recover,aim;
            public bool separate;public float windupEnd,strikeEnd,contact,rate;
        }
        [Serializable] public sealed class Cannon
        {
            public float[] muzzle;public float speed,gravity,radius,splash,firePitch,impactPitch;
            public string fireCue,impactCue;
            public Vector3 Muzzle=>new Vector3(muzzle[0],muzzle[1],muzzle[2]);
        }
        public Attack[] actions;public Cannon cannon;
        public string reaction,defeat;
        public Attack Action(string id){if(actions!=null)foreach(var a in actions)if(a.id==id)return a;return null;}
        public string Choose(int turn,bool close)
        {
            if(actions==null || actions.Length==0)return "melee";
            int count=0;foreach(var a in actions)if(cannon==null || (a.kind=="cannon")!=close)count++;
            if(count==0)return actions[0].id;
            int choice=(turn-1)%count;foreach(var a in actions)if(cannon==null || (a.kind=="cannon")!=close){if(choice--==0)return a.id;}
            return actions[0].id;
        }
        public bool IsCannon(string id)=>Action(id)?.kind=="cannon";
        public string resource,attack,windup,recover;
        public bool separate;
        public float windupEnd,strikeEnd,contact,rate,walkDistance;
        public Motion[] motions;
        public Motion Find(string name){if(motions!=null)foreach(var m in motions)if(m.name==name)return m;return null;}
        public string Clip(string state,string move=null)
        {
            var a=Action(move);
            return state=="windup"?(a?.windup??windup):state=="aim"?a?.aim:state=="recover"?(a?.recover??recover):state=="strike"?(a?.strike??attack):state=="stagger"?(string.IsNullOrEmpty(reaction)?"em00_020":reaction):state=="dead"?(string.IsNullOrEmpty(defeat)?"em00_032":defeat):null;
        }
        public float Phase(string state,float progress,string move=null)
        {
            var a=Action(move);bool split=!(a?.separate??separate);float w=a?.windupEnd??windupEnd,e=a?.strikeEnd??strikeEnd;
            if(!split || (state!="windup" && state!="strike" && state!="recover"))return Mathf.Clamp01(progress);
            return state=="windup"?Mathf.Lerp(0,w,progress):state=="strike"?Mathf.Lerp(w,e,progress):Mathf.Lerp(e,1,progress);
        }
        public float Duration(string state,string move=null)
        {
            var m=Find(Clip(state,move));if(m==null)return .3f;
            if(state=="stagger")return .32f;if(state=="aim")return .3f;
            var a=Action(move);float w=a?.windupEnd??windupEnd,e=a?.strikeEnd??strikeEnd;
            float portion=(a?.separate??separate)?1:state=="windup"?w:state=="strike"?e-w:1-e;
            return Mathf.Max(.12f,m.duration*portion/Mathf.Max(.1f,a?.rate??rate));
        }
        public float Contact(string move=null)
        {
            var a=Action(move);float c=a?.contact??contact,w=a?.windupEnd??windupEnd,e=a?.strikeEnd??strikeEnd;
            return (a?.separate??separate)?c:Mathf.Clamp01((c-w)/Mathf.Max(.001f,e-w));
        }
        public float StrikeContact=>Contact();
        public Vector3 Root(string state,float progress,string move=null)
        {
            var m=Find(Clip(state,move));return m==null?Vector3.zero:m.Root(Phase(state,progress,move));
        }
        [Serializable] sealed class Bank { public ImpMotionProfile[] profiles; }
        static Bank bank;
        public static ImpMotionProfile Load(string resource)
        {
            if(resource==null || !resource.StartsWith("Okami/em0"))return null;
            if(bank==null){var data=Resources.Load<TextAsset>("Okami/ImpMotions");if(data)bank=JsonUtility.FromJson<Bank>(data.text);}
            if(bank!=null && bank.profiles!=null)foreach(var p in bank.profiles)if(p.resource==resource)return p;
            return null;
        }
    }
}
