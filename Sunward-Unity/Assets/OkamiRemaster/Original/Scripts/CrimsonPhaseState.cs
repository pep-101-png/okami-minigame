namespace Sunward.Remaster
{
    public enum CrimsonStage { Armoured, Rising, Flame, Defeated }
    public sealed class CrimsonPhaseState
    {
        public CrimsonStage Stage { get; private set; }
        public bool TryRise()
        {if(Stage!=CrimsonStage.Armoured)return false;Stage=CrimsonStage.Rising;return true;}
        public void Ignite(){if(Stage==CrimsonStage.Rising)Stage=CrimsonStage.Flame;}
        public void Defeat(){if(Stage==CrimsonStage.Flame)Stage=CrimsonStage.Defeated;}
        public float DamageMultiplier=>Stage==CrimsonStage.Flame?2:1;
    }
}
