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
            FireBonus(game.Profile,Now);game.Stamina=Mathf.Min(game.MaxStamina,game.Stamina+50);game.Save.Save();
            game.Services.RestAt(Fire+new Vector3(-1.15f,0,-.15f),90);game.Notify("Hearth blessing · +50 stamina for five minutes");
        }
        void Update(){if(!game)return;game.Health=Mathf.Min(game.Health,game.MaxHealth);game.Stamina=Mathf.Min(game.Stamina,game.MaxStamina);}
    }
}
