using UnityEngine;
namespace Sunward
{
    public sealed partial class GameFlow
    {
        public void StartMasteryBattle()
        {
            ClearEnemies();ClearProjectiles();if(Ultimate)Ultimate.ResetFight();InTrial=true;BossTrial=false;waiting=false;Wave=0;runCoins=runXp=0;
            Combat.Cancel();Player.Locked=false;Player.Teleport(Remaster.VillageAdventures.PracticeCentre+new Vector3(0,.05f,-9));Player.transform.rotation=Quaternion.identity;
            barrier=Fx.Boundary(Remaster.VillageAdventures.PracticeCentre,25);
        }
        public EnemyBrain SpawnPracticeSpirit(string id,Vector3 at,float health)
        {
            var spec=System.Array.Find(spirits,s=>s.id==id);if(!spec)return null;
            var root=new GameObject("Mastery practice · "+spec.title);root.transform.position=at;var brain=root.AddComponent<EnemyBrain>();brain.Init(this,spec);brain.Hp=brain.MaxHp=health;Enemies.Add(brain);return brain;
        }
        public void StartTrailBattle(int stage)
        {
            ClearEnemies();ClearProjectiles();InTrial=true;BossTrial=false;waiting=false;Wave=0;runCoins=runXp=0;
            if(Ultimate)Ultimate.ResetFight();barrier=Fx.Boundary(Remaster.VillageAdventures.TrailCentre,25);
            var centre=Remaster.VillageAdventures.TrailCentre+Remaster.MoonlitTrail.Puzzles[stage==1?0:2];
            SpawnPracticeSpirit(stage==1?"reed":"heavy",centre+new Vector3(-3,.05f,0),80+ProgressionRules.Level(Profile)*4);
            SpawnPracticeSpirit(stage==1?"wisp":"ranged",centre+new Vector3(3,.05f,0),60+ProgressionRules.Level(Profile)*3);
        }
        public void EndTrailBattle(bool win)
        {if(!Adventures || !Adventures.Trail || !Adventures.Trail.BattleActive)return;InTrial=BossTrial=waiting=false;Combat.Cancel();ClearBarrier();ClearProjectiles();ClearEnemies();Adventures.Trail.BattleFinished(win);}
        public void EndMasteryBattle(bool win)
        {
            if(!Adventures || !Adventures.Mastery || !Adventures.Mastery.Active)return;
            InTrial=BossTrial=waiting=false;Combat.Cancel();ClearBarrier();ClearProjectiles();ClearEnemies();Adventures.Mastery.Complete(win);
        }
    }
}
