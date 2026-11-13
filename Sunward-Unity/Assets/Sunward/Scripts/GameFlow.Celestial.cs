using UnityEngine;
namespace Sunward
{
    public sealed partial class GameFlow
    {
        public bool StartCelestialTrial(EnemyDefinition spec,Vector3 centre)
        {
            if(InTrial || Blocked || Health<=0 || !Celestial || !spec)return false;
            Close();ClearEnemies();if(Ultimate)Ultimate.ResetFight();InTrial=BossTrial=true;waiting=false;Wave=0;runCoins=runXp=0;
            Health=MaxHealth;Stamina=MaxStamina;Energy=MaxEnergy;Combat.Cancel();Combat.Equip();
            Player.Teleport(centre+new Vector3(0,.04f,-15));Player.transform.rotation=Quaternion.identity;
            barrier=Fx.Boundary(centre,25);
            var obj=new GameObject(spec.title);obj.transform.position=centre+new Vector3(0,.03f,8);obj.transform.rotation=Quaternion.Euler(0,180,0);
            var brain=obj.AddComponent<EnemyBrain>();brain.Init(this,spec);Enemies.Add(brain);return true;
        }
        void FinishCelestial(bool win)
        {
            InTrial=BossTrial=waiting=false;Combat.Cancel();Combat.Rest(false);ClearBarrier();ClearProjectiles();Player.Locked=Health<=0;
            if(win)
            {
                Profile.shiranuiUnlock=Mathf.Max(Profile.shiranuiUnlock,Celestial.Kind);
                Profile.coins+=Celestial.Kind==1?1600:4000;Profile.xp+=Celestial.Kind==1?1400:2500;
                Sunward.Remaster.AwakeningProgress.Record(this,"boss");Audio.VictoryMusic(true);
            }
            else{Profile.defeats++;ClearEnemies();Health=MaxHealth;}
            Save.Save();Close();Celestial.Complete(win);
        }
        public void LeaveCelestial()
        {if(InTrial && Celestial && Celestial.Active)FinishCelestial(false);}
    }
}
