using System;
namespace Sunward.Remaster
{
    // Source wp2e pairs: PL 544..54b and WP 001..008 are each 30 frames.
    // PL 540 is a static ready pose, not the first primary strike.
    public static class TundraAttackRules
    {
        public const string Cast="Tundra_Cast", Charge="NativeCharge_tundra";
        public const float EnterBlend=.08f, ReturnBlend=.16f, ContactRadius=.28f;
        public static string Primary(int index)
        {if(index<0 || index>=8)throw new ArgumentOutOfRangeException(nameof(index));return "Tundra_"+(0x544+index).ToString("x3");}
        public static bool Owns(string state)=>state!=null && (state.StartsWith("Tundra_",StringComparison.Ordinal)||state==Charge);
        public static int WeaponClip(string state)
        {
            if(state==Cast)return 12;
            if(state=="Tundra_54f")return 15;
            for(int i=0;i<8;i++)if(state==Primary(i))return i+1;
            return -1;
        }
        public static int VisibleBeads(string state)=>state==Cast?6:12;
        public static float CastTime(float phase,float duration,float recovery,float loopDuration,out bool ending)
        {
            float t=Math.Max(0,Math.Min(1,phase))*duration,start=Math.Max(0,duration-recovery);
            ending=t>=start;
            int cycles=Math.Max(1,(int)Math.Round(start/Math.Max(.001f,loopDuration)));
            return ending?t-start:t/Math.Max(.001f,start)*(cycles*loopDuration);
        }
    }
}
