using UnityEngine;
namespace Sunward.Remaster
{
    public static class AwakenedWeaponArts
    {
        public static float BrushPower(string id)=>!OriginalWeaponEvolution.IsAwakened(id)?1:Base(id)=="wp28"?1.8f:Base(id)=="wp25" || Base(id)=="wp27" || Base(id)=="wp22"?1.5f:1.2f;
        static string Base(string id)=>OriginalWeaponCatalog.Find(id)?.resource??"wp25";
        public static void Contact(GameFlow g,EnemyBrain target,bool charged)
        {
            if(!OriginalWeaponEvolution.IsAwakened(g.Profile.equipped))return;string art=Base(g.Profile.equipped);var point=target.transform.position+Vector3.up*.4f;
            if(art=="wp20" || art=="wp24")
            {
                if(!target.Dead){var burn=target.GetComponent<DivineBurn>();if(!burn)burn=target.gameObject.AddComponent<DivineBurn>();burn.Begin(g,target,art=="wp24"?4:2);}
                if(charged)Pulse(g,point,art=="wp24"?5:3,art=="wp24"?18:10,"Flame",new Color(1,.35f,.08f));
            }
            else if(art=="wp2e"){if(charged){Pulse(g,point,4,8,"SpiritGlow",new Color(.35f,.75f,1));foreach(var enemy in g.Enemies)if(enemy && !enemy.Dead && Vector3.Distance(enemy.transform.position,point)<4)enemy.Freeze(.9f);}}
            else if(charged)
            {
                if(art=="wp21")Pulse(g,point,4,16,"Cloud",new Color(.8f,.6f,.3f),.7f);
                else if(art=="wp22" || art=="wp27")Pulse(g,point,5.5f,14,"Wind",new Color(.65f,1,.8f),.35f);
                else if(art=="wp23")g.Energy=Mathf.Min(g.MaxEnergy,g.Energy+6);
                else if(art=="wp25")Pulse(g,point,4,12,"Spirit",new Color(1,.9f,.7f));
                else if(art=="wp26")for(int i=0;i<7 && !target.Dead;i++){target.Damage(3*g.Combat.FormMultiplier,g.Player.transform.forward,.05f);CelestialBrush.Burst("Wind",point+new Vector3(Mathf.Sin(i)*.6f,i*.12f,0),1,1.2f);}
                else if(art=="wp2a")Pulse(g,point,4.5f,12,"SpiritGlow",new Color(1,.9f,.6f));
                else if(art=="wp2d"){g.Health=Mathf.Min(g.MaxHealth,g.Health+3);g.Energy=Mathf.Min(g.MaxEnergy,g.Energy+3);CelestialBrush.Burst("Blossom",point,8,.3f);}
            }
        }
        public static void BrushHit(GameFlow g,EnemyBrain enemy,bool allowSword=true)
        {
            if(!OriginalWeaponEvolution.IsAwakened(g.Profile.equipped))return;
            if(Base(g.Profile.equipped)=="wp28" && allowSword){FallingDivineSword.Begin(g,enemy.transform.position);}
            if(Base(g.Profile.equipped)=="wp2c"){enemy.Stun(.65f);g.Energy=Mathf.Min(g.MaxEnergy,g.Energy+3);}
        }
        public static void Pulse(GameFlow g,Vector3 point,float radius,float damage,string paint,Color tint,float stun=.12f)
        {
            var p=OriginalAtmosphere.Create(paint,null,point,0,radius*.55f,.7f,1.5f,radius*.45f);if(p){var m=p.main;m.startColor=tint;p.Emit(18);Object.Destroy(p.gameObject,1.2f);}
            foreach(var e in g.Enemies.ToArray())if(e && !e.Dead && Vector3.Distance(e.transform.position,point)<radius)
            e.Damage(damage*g.Combat.FormMultiplier,(e.transform.position-point).normalized,stun);
        }
    }
    public sealed class DivineBurn:MonoBehaviour
    {
        GameFlow game;EnemyBrain enemy;float remaining,tick,power;ParticleSystem flame;
        public void Begin(GameFlow g,EnemyBrain target,float damage){game=g;enemy=target;remaining=3;power=damage*g.Combat.FormMultiplier;if(!flame)flame=OriginalAtmosphere.Create("Flame",transform,Vector3.up*.7f,4,.25f,.65f,.1f,.3f);}
        void Update(){if(!game || !enemy || enemy.Dead || !game.InTrial){Destroy(this);return;}if(game.Blocked)return;remaining-=Time.deltaTime;tick-=Time.deltaTime;if(tick<=0){tick=1;enemy.Damage(power,Vector3.zero,0);}if(remaining<=0)Destroy(this);}
        void OnDestroy(){if(flame)Destroy(flame.gameObject);}
    }
    public sealed class FallingDivineSword:MonoBehaviour
    {
        GameFlow game;GameObject blade;Vector3 point;float time;bool landed;
        public static void Begin(GameFlow g,Vector3 at){var root=new GameObject("Eighth Wonder · divine falling sword");var effect=root.AddComponent<FallingDivineSword>();effect.game=g;effect.point=at;root.transform.position=at;effect.blade=VillageFestival.Place(root.transform,"Okami/wp28",Vector3.up*11,new Vector3(2.5f,.7f,8),new Vector3(-90,0,0));}
        void Update(){if(!game){Destroy(gameObject);return;}if(game.Blocked)return;time+=Time.deltaTime;if(blade)blade.transform.localPosition=Vector3.up*Mathf.Lerp(11,3,Mathf.Clamp01(time/.6f));if(!landed && time>=.6f){landed=true;AwakenedWeaponArts.Pulse(game,point,5.5f,35,"Cloud",new Color(.8f,.7f,.4f),.5f);game.Audio.Cue("heavy-impact");}if(time>1.2f)Destroy(gameObject);}
    }
}
