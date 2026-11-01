namespace Sunward.Remaster
{
    public enum CrimsonStage { ArmouredFlame, SheddingArmour, Armoured, Rising, Flame, Defeated }
    public sealed class CrimsonPhaseState
    {
        public int Phase { get; private set; }=1;
        public bool Transitioning { get; private set; }
        bool defeated;
        public CrimsonStage Stage=>defeated?CrimsonStage.Defeated:Transitioning?(Phase==1?CrimsonStage.SheddingArmour:CrimsonStage.Rising):Phase==1?CrimsonStage.ArmouredFlame:Phase==2?CrimsonStage.Armoured:CrimsonStage.Flame;
        public bool TryRise()
        {if(defeated || Transitioning || Phase>=3)return false;Transitioning=true;return true;}
        public void Ignite(){if(Transitioning){Phase++;Transitioning=false;}}
        public void Defeat(){if(Phase==3 && !Transitioning)defeated=true;}
        public float ScaleMultiplier=>1<<(Phase-1);
        public float DamageMultiplier=>ScaleMultiplier;
    }
}
