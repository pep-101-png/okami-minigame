// Actual weapon definitions/catalog/evolution; only Unity construction and effects doubled.
using System;using System.Text.Json;using Sunward;using Sunward.Remaster;
namespace UnityEngine{
public class Object{public static T Instantiate<T>(T value)=>JsonSerializer.Deserialize<T>(JsonSerializer.Serialize(value,new JsonSerializerOptions{IncludeFields=true}),new JsonSerializerOptions{IncludeFields=true});public static implicit operator bool(Object o)=>o!=null;}
public class ScriptableObject:Object{}public class GameObject:Object{public T AddComponent<T>()where T:new()=>new T();}public class Transform:Object{public GameObject gameObject=new GameObject();}public struct Vector3{public static Vector3 zero=>new Vector3();}public struct Color{public Color(float r,float g,float b,float a){}}
public class ParticleSystem:Object{public struct MainModule{public bool useUnscaledTime;public Color startColor;}public MainModule main=>new MainModule();}public class CreateAssetMenuAttribute:Attribute{public string menuName;}
public static class Mathf{public static float Clamp01(float x)=>Math.Clamp(x,0,1);}
}
namespace Sunward{public class ProfileData{public string[] owned=new[]{"spear"};public string equipped="spear";public int coins;}}
namespace Sunward.Remaster{public class ThunderWeaponAura{public bool unscaled;}public static class OriginalAtmosphere{public static UnityEngine.ParticleSystem Create(string n,UnityEngine.Transform p,UnityEngine.Vector3 v,float a,float b,float c,float d,float e)=>null;}}
class Tests{
static int n;static void Check(bool ok,string why){n++;if(!ok)throw new Exception(why);}
static void Main(){
var p=new ProfileData{coins=10000};Check(!OriginalWeaponCatalog.Buy(p,"wp29e") && p.coins==10000,"Shop bypasses maze");
foreach(var entry in OriginalWeaponCatalog.All)OriginalWeaponCatalog.Buy(p,entry.id);
Check(p.owned.Length==15,"Native catalogue lost a weapon");OriginalWeaponEvolution.Unlock(p);Check(p.owned.Length==16,"Awakening not included");
var seen=new System.Collections.Generic.HashSet<string>();for(int i=0;i<16;i++){p.equipped=OriginalWeaponCatalog.Next(p);seen.Add(p.equipped);}Check(seen.Count==16 && seen.Contains("wp29e"),"Cycle skips evolved weapon or native gear");
var baseDef=OriginalWeaponCatalog.Definition(OriginalWeaponCatalog.Find("wp29"),new WeaponDefinition(),new WeaponDefinition());var evo=OriginalWeaponCatalog.Definition(OriginalWeaponCatalog.Find("wp29e"),new WeaponDefinition(),new WeaponDefinition());
void Same(Strike a,Strike b){Check(a.clip==b.clip,"Awakening replaces original motion");Check(Math.Abs(b.damage/a.damage-1.35f)<.0001,"Incorrect evolved damage");Check(Math.Abs(b.range/a.range-1.15f)<.0001,"Incorrect evolved reach");Check(a.duration==b.duration && a.stagger==b.stagger,"Awakening changes timing/stun");}
for(int i=0;i<baseDef.light.Length;i++)Same(baseDef.light[i],evo.light[i]);Same(baseDef.heavy[0],evo.heavy[0]);Same(baseDef.charged,evo.charged);Same(baseDef.chargedHeavy,evo.chargedHeavy);Same(baseDef.air,evo.air);
Check(evo.id=="wp29e" && OriginalWeaponCatalog.Find("wp29e").resource=="wp29","Reward is unrelated model");Console.WriteLine("PASS "+n+" actual catalogue, 16-weapon cycle, purchase guard and evolved strike checks; no Unity runtime claim");}
}
