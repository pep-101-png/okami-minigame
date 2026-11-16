using UnityEngine;
namespace Sunward.Remaster
{
    public static class AwakenedWeaponArts
    {
        public static float SpecialPower(GameFlow g)=>1+AwakeningProgress.Rank(g.Profile,g.Profile.equipped)*.1f;
        public static float BrushPower(string id)=>!OriginalWeaponEvolution.IsAwakened(id)?1:Base(id)=="wp28"?1.8f:Base(id)=="wp25" || Base(id)=="wp27" || Base(id)=="wp22"?1.5f:1.2f;
        static string Base(string id)=>OriginalWeaponCatalog.Find(id)?.resource??"wp25";
        public static void Contact(GameFlow g,EnemyBrain target,bool charged)
        {
            if(!OriginalWeaponEvolution.IsAwakened(g.Profile.equipped))return;string art=Base(g.Profile.equipped);var point=target.transform.position+Vector3.up*.4f;
            if(art=="wp20" || art=="wp24")
            {
                if(!target.Dead){var burn=target.GetComponent<DivineBurn>();if(!burn)burn=target.gameObject.AddComponent<DivineBurn>();burn.Begin(g,target,art=="wp24"?4:2);VillageAdventures.Record(g,"ignite");}
                if(charged)Pulse(g,point,art=="wp24"?5:3,art=="wp24"?18:10,"Flame",new Color(1,.35f,.08f));
            }
            else if(art=="wp2e" && charged)
            {Pulse(g,point,4,8,"SpiritGlow",new Color(.35f,.75f,1));foreach(var enemy in g.Enemies)if(enemy && !enemy.Dead && Vector3.Distance(enemy.transform.position,point)<4){bool before=enemy.Frozen;enemy.Freeze(.9f);if(!before && enemy.Frozen)VillageAdventures.Record(g,"freeze");}}
            else if(charged)
            {
                if(art=="wp21")VillageAdventures.Record(g,"shock",Pulse(g,point,4,16,"Cloud",new Color(.8f,.6f,.3f),.7f));
                else if(art=="wp22" || art=="wp27")VillageAdventures.Record(g,"gust",Pulse(g,point,5.5f,14,"Wind",new Color(.65f,1,.8f),.35f));
                else if(art=="wp23"){float before=g.Energy;g.Energy=Mathf.Min(g.MaxEnergy,g.Energy+Mathf.RoundToInt(6*SpecialPower(g)));VillageAdventures.Record(g,"inkreturn",Mathf.RoundToInt(g.Energy-before));}
                else if(art=="wp25")VillageAdventures.Record(g,"cutwave",Pulse(g,point,4,12,"Spirit",new Color(1,.9f,.7f)));
                else if(art=="wp26" && !target.Dead)SevenCutSequence.Begin(g,target);
                else if(art=="wp2a")VillageAdventures.Record(g,"radiance",Pulse(g,point,4.5f,12,"SpiritGlow",new Color(1,.9f,.6f)));
                else if(art=="wp2d"){float hp=g.Health,ink=g.Energy;int n=Mathf.RoundToInt(3*SpecialPower(g));g.Health=Mathf.Min(g.MaxHealth,g.Health+n);g.Energy=Mathf.Min(g.MaxEnergy,g.Energy+n);if(g.Health>hp || g.Energy>ink)VillageAdventures.Record(g,"renewal");CelestialBrush.Burst("Blossom",point,8,.3f);}
            }
        }
        public static void BrushHit(GameFlow g,EnemyBrain enemy,bool allowSword=true)
        {
            if(!OriginalWeaponEvolution.IsAwakened(g.Profile.equipped))return;
            if(Base(g.Profile.equipped)=="wp28" && allowSword)FallingDivineSword.Begin(g,enemy.transform.position);
            if(Base(g.Profile.equipped)=="wp2c"){enemy.Stun(.65f);enemy.Weaken(4);g.Energy=Mathf.Min(g.MaxEnergy,g.Energy+Mathf.RoundToInt(3*SpecialPower(g)));VillageAdventures.Record(g,"purify");}
        }
        public static void Bark(GameFlow g)
        {
            if(!OriginalWeaponEvolution.IsAwakened(g.Profile.equipped))return;string art=Base(g.Profile.equipped);int recovery=0;
            foreach(var e in g.Enemies)if(e && !e.Dead && Vector3.Distance(e.transform.position,g.Player.transform.position)<5.5f)
            {
                if(art=="wp20" || art=="wp24"){var burn=e.GetComponent<DivineBurn>();if(!burn)burn=e.gameObject.AddComponent<DivineBurn>();burn.Begin(g,e,2);}
                else if(art=="wp29")e.Damage(6*g.Combat.FormMultiplier*SpecialPower(g),(e.transform.position-g.Player.transform.position).normalized,.12f);
                else if(art=="wp2e")e.Freeze(.5f);
                else if(art=="wp2c")e.Weaken(3);
                else if(art=="wp22" || art=="wp26" || art=="wp27")e.ElementPush(g.Player.transform.position);
                else if(art=="wp21" || art=="wp28")e.Stun(.35f);
                recovery++;
            }
            int n=Mathf.Min(6,recovery*2);if(art=="wp23" || art=="wp2a" || art=="wp2d")g.Energy=Mathf.Min(g.MaxEnergy,g.Energy+n);
            if(art=="wp2b" || art=="wp2d")g.Health=Mathf.Min(g.MaxHealth,g.Health+n);
        }
        public static int Pulse(GameFlow g,Vector3 point,float radius,float damage,string paint,Color tint,float stun=.12f)
        {
            var p=OriginalAtmosphere.Create(paint,null,point,0,radius*.55f,.7f,1.5f,radius*.45f);if(p){var m=p.main;m.startColor=tint;p.Emit(18);Object.Destroy(p.gameObject,1.2f);}
            int count=0;foreach(var e in g.Enemies.ToArray())if(e && !e.Dead && Vector3.Distance(e.transform.position,point)<radius){e.Damage(damage*g.Combat.FormMultiplier*SpecialPower(g),(e.transform.position-point).normalized,stun);count++;}return count;
        }
    }
    public sealed class DivineBurn:MonoBehaviour
    {
        GameFlow game;EnemyBrain enemy;float remaining,tick,power;ParticleSystem flame;
        public void Begin(GameFlow g,EnemyBrain target,float damage){game=g;enemy=target;remaining=3;power=damage*g.Combat.FormMultiplier*AwakenedWeaponArts.SpecialPower(g);if(!flame)flame=OriginalAtmosphere.Create("Flame",transform,Vector3.up*.7f,4,.25f,.65f,.1f,.3f);}
        void Update(){if(!game || !enemy || enemy.Dead || !game.InTrial){Destroy(this);return;}if(game.Blocked)return;remaining-=Time.deltaTime;tick-=Time.deltaTime;if(tick<=0){tick=1;enemy.Damage(power,Vector3.zero,0);}if(remaining<=0)Destroy(this);}
        void OnDestroy(){if(flame)Destroy(flame.gameObject);}
    }
    public sealed class FallingDivineSword:MonoBehaviour
    {
        GameFlow game;GameObject blade;Vector3 point;float time;bool landed;
        public static void Begin(GameFlow g,Vector3 at){var root=new GameObject("Eighth Wonder · divine falling sword");var effect=root.AddComponent<FallingDivineSword>();effect.game=g;effect.point=at;root.transform.position=at;effect.blade=VillageFestival.Place(root.transform,"Okami/wp28",Vector3.up*11,new Vector3(2.5f,.7f,8),new Vector3(-90,0,0));}
        public const float FallTime=.36f;
        void Update()
        {
            if(!game || !game.InTrial){Destroy(gameObject);return;}if(game.Blocked)return;time+=Time.deltaTime;
            if(blade){float u=Mathf.Clamp01(time/FallTime);blade.transform.localPosition=Vector3.up*Mathf.Lerp(11,3,u*u);}
            if(!landed && time>=FallTime)
            {
                landed=true;int hits=AwakenedWeaponArts.Pulse(game,point,5.5f,35,"Cloud",new Color(.8f,.7f,.4f),.5f);if(hits>0)VillageAdventures.Record(game,"fallingsword");
                SolarPaint.Create(game,point,2);game.Audio.DivineSwordImpact();var camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.Shake(.12f,.24f);
            }
            if(time>1.1f)Destroy(gameObject);
        }
    }
}
