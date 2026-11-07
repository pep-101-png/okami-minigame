using System;
using UnityEngine;

namespace Sunward.Remaster
{
    // Original MOT curves and SEQ sound events, inspected per instrument.
    // Gameplay owns horizontal controller motion; MOT retains its authored leap.
    [Serializable] public sealed class ImpMotionProfile
    {
        [Serializable] public sealed class Sound { public float time,gain; public string cue; }
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
        public string resource,attack,windup,recover;
        public bool separate;
        public float windupEnd,strikeEnd,contact,rate,walkDistance;
        public Motion[] motions;
        public Motion Find(string name){if(motions!=null)foreach(var m in motions)if(m.name==name)return m;return null;}
        public string Clip(string state)=>state=="windup"?windup:state=="recover"?recover:state=="strike"?attack:state=="stagger"?"em00_020":state=="dead"?"em00_032":null;
        public float Phase(string state,float progress)
        {
            if(separate || (state!="windup" && state!="strike" && state!="recover"))return Mathf.Clamp01(progress);
            return state=="windup"?Mathf.Lerp(0,windupEnd,progress):state=="strike"?Mathf.Lerp(windupEnd,strikeEnd,progress):Mathf.Lerp(strikeEnd,1,progress);
        }
        public float Duration(string state)
        {
            var m=Find(Clip(state));if(m==null)return .3f;
            if(state=="stagger")return .32f;
            float portion=separate?1:state=="windup"?windupEnd:state=="strike"?strikeEnd-windupEnd:1-strikeEnd;
            return Mathf.Max(.12f,m.duration*portion/Mathf.Max(.1f,rate));
        }
        public float StrikeContact=>separate?contact:Mathf.Clamp01((contact-windupEnd)/Mathf.Max(.001f,strikeEnd-windupEnd));
        public Vector3 Root(string state,float progress)
        {
            var m=Find(Clip(state));return m==null?Vector3.zero:m.Root(Phase(state,progress));
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
