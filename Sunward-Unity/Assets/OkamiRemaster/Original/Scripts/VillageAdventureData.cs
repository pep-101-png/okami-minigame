using System;
namespace Sunward.Remaster
{
    [Serializable]public sealed class VillageAdventureData
    {
        public int[] mastery=new int[15],caught=new int[6],fish=new int[6];
        public int projects,moonStage,moonBattles;public bool moonDiscovered,moonCharm;
    }
    public static class VillageAdventureRules
    {
        public static bool Validate(ProfileData p)
        {
            if(p.adventures==null)p.adventures=new VillageAdventureData();var a=p.adventures;
            if(a.mastery==null)a.mastery=new int[15];if(a.caught==null)a.caught=new int[6];if(a.fish==null)a.fish=new int[6];
            if(a.mastery.Length!=15 || a.caught.Length!=6 || a.fish.Length!=6 || a.moonBattles<0 || (a.moonBattles&~6)!=0 || a.projects<0 || a.projects>15 || a.moonStage<0 || a.moonStage>3 || a.moonCharm && a.moonStage!=3)return false;
            foreach(int n in a.mastery)if(n<0 || n>3)return false;
            for(int i=0;i<6;i++)if(a.caught[i]<0 || a.caught[i]>1000000 || a.fish[i]<0 || a.fish[i]>9999 || a.fish[i]>a.caught[i])return false;
            return true;
        }
        public static bool Project(ProfileData p,int i)=>i>=0 && i<4 && (p.adventures.projects&(1<<i))!=0;
        public static readonly string[] ProjectNames={"Riverside tea garden","Farm shelter improvements","Bridge & river walk","Pond fishing retreat"};
        public static readonly int[] ProjectCoins={300,600,450,500},ProjectProduce={3,6,0,2},ProjectFish={1,0,0,4};
        public static int FishInPouch(ProfileData p){int n=0;foreach(int f in p.adventures.fish)n+=f;return n;}
        public static bool BuildProject(ProfileData p,int i)
        {
            if(i<0 || i>=4 || Project(p,i) || p.coins<ProjectCoins[i] || p.vegetables<ProjectProduce[i] || FishInPouch(p)<ProjectFish[i])return false;
            p.coins-=ProjectCoins[i];p.vegetables-=ProjectProduce[i];int left=ProjectFish[i];
            for(int j=0;j<6 && left>0;j++){int n=Math.Min(left,p.adventures.fish[j]);p.adventures.fish[j]-=n;left-=n;}
            p.adventures.projects|=1<<i;p.praise+=25;return true;
        }
        public static bool LessonReward(ProfileData p,int weapon,int tier)
        {
            if(weapon<0 || weapon>=15 || tier<1 || tier>3 || p.adventures.mastery[weapon]!=tier-1)return false;
            p.adventures.mastery[weapon]=tier;p.coins+=tier==1?150:tier==2?300:600;p.xp+=tier==1?100:tier==2?200:400;return true;
        }
        public static readonly string[] FishNames={"River carp","Painted koi","Speckled trout","Green char","Sweetfish","Moonlit salmon"};
        public static readonly string[] FishModels={"ana1","ana5","ana6","ana8","anac","anad"};
        public static readonly int[] FishValue={12,25,30,60,15,90};
        public static string FishHint(int i)=>i==0?"A patient fish. Often near the bank in daylight.":i==1?"Gather near offered food.":i==2?"Active in daylight, drawn to food.":i==3?"Visits the restored fishing retreat after sunset.":i==4?"A small silver-green fish, easiest to see during the day.":"A rare night visitor. Feed the pond and watch the moon's reflection.";
        public static bool FishAvailable(ProfileData p,int i,bool fed)=>i>=0 && i<6 && (i==3?p.night && Project(p,3):i==5?p.night && fed:i==1?fed:i==0 || !p.night);
        public static bool Catch(ProfileData p,int i,bool fed)
        {
            if(!FishAvailable(p,i,fed) || p.adventures.fish[i]>=9999 || p.adventures.caught[i]>=1000000)return false;
            bool first=p.adventures.caught[i]==0;p.adventures.caught[i]++;p.adventures.fish[i]++;if(first){p.xp+=i>=3?60:30;p.praise+=5;}return true;
        }
        public static int SellFish(ProfileData p,int i)
        {if(i<0 || i>=6)return 0;int count=p.adventures.fish[i];p.coins+=count*FishValue[i];p.adventures.fish[i]=0;return count;}
        public static bool MoonReward(ProfileData p)
        {if(p.adventures.moonStage!=3 || p.adventures.moonBattles!=6 || p.adventures.moonCharm)return false;p.adventures.moonCharm=true;p.coins+=400;p.xp+=500;return true;}
        public static string VillageHint(ProfileData p)=>!p.adventures.moonDiscovered?"Some old trail stones only catch the light after sunset. Look beyond the first bridge; a circle of flowers remembers the way.":!p.adventures.moonCharm?"The moon's path answers three things: a flower's return, a clean brushstroke, and a stone opened from within.":"The charm grows quiet when blades are drawn. In peaceful moments, it helps your Ink return.";
    }
}
