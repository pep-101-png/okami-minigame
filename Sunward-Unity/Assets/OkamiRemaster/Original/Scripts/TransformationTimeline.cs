using System;
namespace Sunward.Remaster
{
    [Flags] public enum TransformationCue { None=0, Voice=1, Reveal=2, Settle=4, Finish=8 }
    // A single event clock also makes low-frame-rate playback and skipping safe.
    public sealed class TransformationTimeline
    {
        public const float Duration=3.2f,VoiceTime=.3f,RevealTime=1.35f,SettleTime=2.45f;
        public bool Playing { get; private set; }
        public float Elapsed { get; private set; }
        TransformationCue fired;
        public bool Begin()
        {if(Playing)return false;Playing=true;Elapsed=0;fired=TransformationCue.None;return true;}
        public TransformationCue Tick(float dt)
        {
            if(!Playing)return TransformationCue.None;
            Elapsed=Math.Min(Duration,Elapsed+Math.Max(0,dt));
            TransformationCue due=TransformationCue.None;
            if(Elapsed>=VoiceTime)due|=TransformationCue.Voice;
            if(Elapsed>=RevealTime)due|=TransformationCue.Reveal;
            if(Elapsed>=SettleTime)due|=TransformationCue.Settle;
            if(Elapsed>=Duration)due|=TransformationCue.Finish;
            var result=due&~fired;fired|=result;
            if((result&TransformationCue.Finish)!=0)Playing=false;
            return result;
        }
        public TransformationCue Skip()
        {if(!Playing)return TransformationCue.None;Elapsed=Duration;return Tick(0)&~TransformationCue.Voice;}
        public void Cancel(){Playing=false;Elapsed=0;fired=TransformationCue.None;}
    }
}
