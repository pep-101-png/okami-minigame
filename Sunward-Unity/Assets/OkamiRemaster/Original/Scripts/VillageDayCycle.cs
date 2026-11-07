using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class VillageDayCycle:MonoBehaviour
    {
        public const float Period=900;
        public GameFlow game;bool pending;float saveTime;
        public static bool Tick(ProfileData p,float realSeconds)
        {
            if(float.IsNaN(realSeconds)||float.IsInfinity(realSeconds)||realSeconds<0)return false;
            p.dayElapsed+=realSeconds;bool changed=false;
            while(p.dayElapsed>=Period){p.dayElapsed-=Period;p.night=!p.night;changed=true;}
            return changed;
        }
        public static bool SleepTime(ProfileData p,int seed)=>p.night && p.dayElapsed>90+(Mathf.Abs(seed)%4)*45 && p.dayElapsed<Period-120;
        public void AdvanceByBed(){game.Profile.night=!game.Profile.night;game.Profile.dayElapsed=0;pending=true;game.Save.Save();}
        void Update()
        {
            if(!game || !game.Player || game.Panel=="title")return;
            game.Profile.playSeconds+=Time.unscaledDeltaTime;
            if(Tick(game.Profile,Time.unscaledDeltaTime)){pending=true;game.Save.Save();}
            saveTime+=Time.unscaledDeltaTime;if(saveTime>=60){saveTime=0;game.Save.Save();}
            if(pending && !game.Blocked && !game.InTrial && !game.Home.Active && !game.Player.Locked && !VillageInteriors.AnyRoom(game.Player.transform.position) && !HeavenlyGarden.Inside(game.Player.transform.position))
            {pending=false;game.Presentation.SkyTransition(game.Profile.night);}
        }
    }
}
