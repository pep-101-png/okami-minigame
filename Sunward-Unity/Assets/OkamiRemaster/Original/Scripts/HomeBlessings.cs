using System;
using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class HomeBlessings:MonoBehaviour
    {
        public GameFlow game;
        public static readonly Vector3 Fire=VillageInteriors.HomeCentre+new Vector3(2,.05f,0);
        public static long Now=>DateTimeOffset.UtcNow.ToUnixTimeSeconds();
        public static int HealthBonus(ProfileData p,long now)=>p.bedBlessingUntil>now?50:0;
        public static int StaminaBonus(ProfileData p,long now)=>p.bedBlessingUntil>now || p.fireBlessingUntil>now?50:0;
        public static void FireBonus(ProfileData p,long now){p.fireBlessingUntil=Math.Max(p.fireBlessingUntil,now+300);}
        public static void BedBonus(ProfileData p,long now){p.bedBlessingUntil=Math.Max(p.bedBlessingUntil,now+900);}
        public void SitByFire()
        {
            if(!VillageInteriors.Home(game.Player.transform.position))return;
            FireBonus(game.Profile,Now);game.Stamina=game.MaxStamina;game.Player.StopMotion();game.Save.Save();
            game.Services.RestAt(Fire+new Vector3(-1.15f,0,-.15f),90);game.Notify("Hearth blessing · +50 stamina for five minutes");
        }
        public static string Status(ProfileData p,long now)
        {
            long bed=Math.Max(0,p.bedBlessingUntil-now),fire=Math.Max(0,p.fireBlessingUntil-now);
            string text=bed>0?"Bed blessing · +50 health & stamina · "+(bed/60)+":"+(bed%60).ToString("D2"):"";
            if(fire>bed)text+=(text.Length>0?" / ":"")+"Hearth · +50 stamina · "+(fire/60)+":"+(fire%60).ToString("D2");
            return text;
        }
        void Update(){if(!game)return;game.Health=Mathf.Min(game.Health,game.MaxHealth);game.Stamina=Mathf.Min(game.Stamina,game.MaxStamina);}
    }
}
