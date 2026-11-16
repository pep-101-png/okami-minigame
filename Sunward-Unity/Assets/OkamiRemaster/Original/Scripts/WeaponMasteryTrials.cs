using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    [DefaultExecutionOrder(85)]
    public sealed class WeaponMasteryTrials:MonoBehaviour
    {
        public GameFlow game;public bool Active{get;private set;}public int Weapon{get;private set;}public int Tier{get;private set;}
        public static readonly Vector3 Scroll=VillageInteriors.DojoCentre+new Vector3(7,.05f,7);
        public static readonly string[] Art={"ignite","shock","gust","inkreturn","ignite","cutwave","seven","gust","fallingsword","thunderstorm","radiance","life","purify","renewal","freeze"};
        readonly Dictionary<string,int> counts=new Dictionary<string,int>();GameObject court;Vector3 returnPoint;Quaternion returnFacing;string previousWeapon;float health,stamina,ink,remaining,nextSpawn;int hurt;
        public int Count(string kind)=>counts.TryGetValue(kind,out var n)?n:0;
        public string Status=>"MASTERY · "+OriginalWeaponCatalog.All[Weapon].title+" · "+Tier+" / 3 · "+Mathf.CeilToInt(remaining)+"s";
        string Deflections=>Weapon==12 && Tier>1?" · deflections "+Count("deflect")+" / "+(Tier==3?3:1):"";
        public string Objective=>Tier==1?"Land "+Count("hit")+" / 6 hits, "+Count("charged")+" / 2 charged hits, and "+Count("brush")+" / 1 brush hit.":ArtGoal+" · "+Count(Art[Weapon])+" / "+Goal+(Tier==3?" · brush hits "+Count("brush")+" / 3 · damage contacts "+hurt+" / 5":" · charged hits "+Count("charged")+" / 2")+Deflections;
        int Goal=>Weapon==3?12:Weapon==6?14:Weapon==8?2:Tier==3?6:3;
        public string ArtGoal=>Weapon==0 || Weapon==4?"Ignite enemies":Weapon==1?"Catch enemies in earth shockwaves":Weapon==2 || Weapon==7?"Catch enemies in charged wind crescents":Weapon==3?"Recover Ink with charged contacts; spend Ink with your brush first":Weapon==5?"Land charged cutting waves":Weapon==6?"Land the seven successive cuts":Weapon==8?"Land falling swords with Power Slash":Weapon==9?"Connect the glowing blade tip to enemies with the brush":Weapon==10?"Land charged sacred-light bursts":Weapon==11?"Defeat enemies to recover health":Weapon==12?"Brush away incoming shots and purify enemies with brush hits":Weapon==13?"Recover health and Ink with charged contacts":"Freeze enemies with charged casts";
        void Start()
        {
            court=VillageAdventures.Court(transform,VillageAdventures.PracticeCentre,false);court.SetActive(false);
            var scroll=new GameObject("Dojo mastery scroll · all fifteen instruments");scroll.transform.SetParent(transform,false);scroll.transform.position=Scroll;
            VillageAdventures.Prop(scroll.transform,"vt11",Vector3.zero,new Vector3(.7f,1.7f,.12f),90);
        }
        public bool Begin(int weapon,int tier)
        {
            if(Active || game.InTrial || game.Health<=0 || weapon<0 || weapon>=15 || tier<1 || tier>3 || !VillageServices.InDojo(game.Player.transform.position))return false;
            var entry=OriginalWeaponCatalog.Display(game.Profile,OriginalWeaponCatalog.All[weapon]);if(!OriginalWeaponCatalog.Owns(game.Profile,entry.id) || tier>game.Profile.adventures.mastery[weapon]+1 || tier>1 && !OriginalWeaponEvolution.IsAwakened(entry.id))return false;
            var festival=game.GetComponent<FestivalChallenges>();if(festival && festival.Active)return false;
            returnPoint=game.Player.transform.position;returnFacing=game.Player.transform.rotation;previousWeapon=game.Profile.equipped;health=game.Health;stamina=game.Stamina;ink=game.Energy;
            Weapon=weapon;Tier=tier;remaining=tier==1?120:tier==2?150:180;nextSpawn=0;hurt=0;counts.Clear();game.Close();Active=true;court.SetActive(true);Physics.SyncTransforms();
            game.Profile.equipped=entry.id;game.Combat.Equip();game.StartMasteryBattle();game.Health=tier>1 && (weapon==11 || weapon==13)?game.MaxHealth*.6f:game.MaxHealth;game.Stamina=game.MaxStamina;game.Energy=tier>1?game.MaxEnergy*.25f:game.MaxEnergy;
            game.Notify(tier==1?"Practice the weapon, charged contacts and your brush":ArtGoal);return true;
        }
        public void Record(string kind,int count=1)
        {if(!Active || OriginalWeaponEvolution.BaseId(game.Profile.equipped)!=OriginalWeaponCatalog.All[Weapon].id || count<=0)return;counts[kind]=Count(kind)+count;}
        public void Hurt(){if(Active)hurt++;}
        public bool GoalsMet=>Tier==1?Count("hit")>=6 && Count("charged")>=2 && Count("brush")>=1:Count(Art[Weapon])>=Goal && (Weapon!=12 || Count("deflect")>=(Tier==3?3:1)) && (Tier==3?Count("brush")>=3 && hurt<=5:Count("charged")>=2);
        void Update()
        {
            if(!game || !game.Player || !court)return;
            if(!Active)
            {if(!game.Blocked && VillageServices.InDojo(game.Player.transform.position) && Vector3.Distance(game.Player.transform.position,Scroll)<2.4f){game.WorldPrompt("E · Read the weapon mastery scroll");if(game.Player.input.Interact.WasPressedThisFrame())game.SetPanel("mastery");}return;}
            if(!game.InTrial){Complete(false);return;}if(game.Blocked)return;
            remaining-=Time.deltaTime;if(remaining<=0 || Tier==3 && hurt>5){game.EndMasteryBattle(false);return;}
            if(GoalsMet){game.EndMasteryBattle(true);return;}
            game.WorldPrompt(Objective);nextSpawn-=Time.deltaTime;int alive=game.Enemies.FindAll(e=>e && !e.Dead).Count;
            if(alive<3 && nextSpawn<=0)
            {
                nextSpawn=1;int seed=Count("kill")+alive;var at=VillageAdventures.PracticeCentre+new Vector3(Mathf.Sin(seed*2.4f)*7,.05f,Mathf.Cos(seed*2.4f)*7);
                float power=(1+(ProgressionRules.Level(game.Profile)-1)*.045f+game.Profile.upgrades.strength*.18f)*(1+game.Profile.upgrades.spear*.12f)*game.Combat.FormMultiplier;
                float health=(Tier==1?35:Weapon==11?25:60)*power;
                game.SpawnPracticeSpirit(Weapon==12 || Tier==3 && seed%3==0?"ranged":seed%2==0?"reed":"wisp",at,health);
            }
        }
        public void Complete(bool won)
        {
            if(!Active)return;Active=false;bool reward=won && VillageAdventureRules.LessonReward(game.Profile,Weapon,Tier);
            var id=OriginalWeaponEvolution.Replaced(game.Profile,previousWeapon)?OriginalWeaponEvolution.EvolvedId(previousWeapon):previousWeapon;
            game.Profile.equipped=id;game.Health=Mathf.Clamp(health,1,game.MaxHealth);game.Stamina=Mathf.Min(stamina,game.MaxStamina);game.Energy=Mathf.Min(ink,game.MaxEnergy);game.Player.Locked=false;game.Close();game.Combat.Equip();game.Player.Teleport(returnPoint);game.Player.transform.rotation=returnFacing;court.SetActive(false);
            game.Save.Save();var camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.SnapFocus();game.Audio.Cue(won?"collect":"bell");game.Notify(won?(reward?"Mastery recorded · first-completion coins and XP saved":"Practice complete · this lesson's reward was already claimed"):"Lesson ended · return to the scroll whenever you wish");
        }
        public void Cancel(){if(Active)game.EndMasteryBattle(false);}
        void OnDisable(){Cancel();}
    }
}
