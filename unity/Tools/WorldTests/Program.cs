using System;
using System.IO;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using Sunward;
using Sunward.Editor;
using UnityEngine;
class Program {
 static void Need(bool ok,string message){if(!ok)throw new Exception(message);Console.WriteLine("PASS "+message);}
 static void Main(){
 string root=Directory.Exists("unity")?"unity":".";
 RevolvedGeometry.Build(RevolvedGeometry.LanternRoof,32,out var roof,out var roofUV,out var roofIndices);
 MeshSafety.Validate("New actual stone lantern cap",roof,roofIndices);
 var edges=new Dictionary<(int,int),int>();
 for(int i=0;i<roofIndices.Length;i+=3)for(int j=0;j<3;j++){
 int a=roofIndices[i+j],b=roofIndices[i+(j+1)%3];var key=a<b?(a,b):(b,a);edges.TryGetValue(key,out int count);edges[key]=count+1;
 }
 Need(edges.Values.All(n=>n==2),"Actual lantern roof geometry is closed, including poles and circumference seam");
 double volume=0;for(int i=0;i<roofIndices.Length;i+=3){var a=roof[roofIndices[i]];var b=roof[roofIndices[i+1]];var c=roof[roofIndices[i+2]];volume+=(a.x*(b.y*c.z-b.z*c.y)+a.y*(b.z*c.x-b.x*c.z)+a.z*(b.x*c.y-b.y*c.x))/6.0;}
 Need(volume>0,"Actual lantern cap has outward winding, not just closed edges");
 using(var obj=new StreamWriter(root+"/Review/lantern-roof-audit.obj")){
 foreach(var v in roof)obj.WriteLine(FormattableString.Invariant($"v {v.x} {v.y} {v.z}"));
 for(int i=0;i<roofIndices.Length;i+=3)obj.WriteLine($"f {roofIndices[i]+1} {roofIndices[i+1]+1} {roofIndices[i+2]+1}");
 }
 var random=new Random(7102);
 for(int sample=0;sample<5000;sample++){
 float a=.05f+(float)random.NextDouble()*2,b=.05f+(float)random.NextDouble()*2,d=(float)random.NextDouble()*8;
 LimbArc.Solve(a,b,d,out float x,out float h,out float reach);
 if(!float.IsFinite(x)||!float.IsFinite(h)||MathF.Abs(MathF.Sqrt(x*x+h*h)-a)>.0001f||MathF.Abs(MathF.Sqrt((reach-x)*(reach-x)+h*h)-b)>.0001f)throw new Exception("Limb lengths changed in solve "+sample);
 }
 Need(true,"5000 actual shared limb solves preserve upper/lower lengths, including unreachable targets");
 bool invalidLimb=false;try{LimbArc.Solve(float.NaN,1,1,out _,out _,out _);}catch(ArgumentOutOfRangeException){invalidLimb=true;}Need(invalidLimb,"Nonfinite limb input rejected");
 Need(Vector3.Distance(HomeLayout.Bed,HomeLayout.Mirror)>4,"Separate sleep/mirror zones");
 var data=JsonUtility.FromJson<ValleyData>(File.ReadAllText(root+"/Assets/Sunward/Data/Valley.json"));var world=data.world;
 foreach(var npc in world.npcs){var p=new Vector3(npc.position[0],npc.position[1],npc.position[2]);Need(VillageNavigation.FindSafe(world,p,out var safe)&&VillageNavigation.Clear(world,safe),"Safe spawn: "+npc.name);}
 var materials=data.assets.Where(a=>a.name=="TownV3").SelectMany(a=>a.meshes).Select(m=>m.material).Distinct().ToArray();
 var families=new Dictionary<string,int>();
 foreach(int id in materials){string family=SurfaceArtRules.Family(data.materials[id]);if(family==null)continue;if(!families.ContainsKey(family))families[family]=0;families[family]++;Need(File.Exists(root+"/Assets/Sunward/Textures/Art/Paint-"+family+".png")&&File.Exists(root+"/Assets/Sunward/Textures/Art/Paint-"+family+"-normal.png"),"Connected art source for real TownV3 material "+id);}
 foreach(string family in new[]{"wood","roof","stone","plaster","meadow"})Need(families.ContainsKey(family),"Actual Windflower uses new "+family+" artwork");
 File.WriteAllText(root+"/Review/art-binding-plan.json",JsonSerializer.Serialize(new{source="actual TownV3 mesh material indices",material_families=families,unity_scene_references="REQUIRE LOCAL UNITY VALIDATION"},new JsonSerializerOptions{WriteIndented=true}));
 bool rejected=false;try{MeshSafety.Validate("test invalid generated mesh",new[]{new Vector3(0,float.NaN,0)},new[]{0,0,0});}catch(InvalidOperationException){rejected=true;}Need(rejected,"NaN mesh identified before collision cooking");
 int recovery=0;for(int z=-29;z<=29;z+=2){var water=new Vector3(Valley.RiverX(z),-1,-z);Need(VillageNavigation.FindSafe(world,water,out var safe,.55f,16)&&Valley.Depth(safe)<=.1f,"River escape near z="+z);recovery++;}
 for(int i=0;i<=10000;i++){float h=Valley.BridgeHeight(i/10000f);if(!float.IsFinite(h)||h<.1f||h>.521f)throw new Exception("Invalid bridge height");}
 Need(Valley.BridgeHeight(0)==.1f&&Valley.BridgeHeight(1)==.1f,"Bridge finite and level endpoints");
 foreach(var box in world.boxes)Need(!VillageNavigation.Clear(world,new Vector3(box.x,0,-box.z)),"Building/rail rejected");
 int grounded=0,components=0;
 using var reader=new BinaryReader(File.OpenRead(root+"/Assets/Sunward/Data/Valley.bytes"));
 foreach(var asset in data.assets.Where(a=>a.name=="TownV3"))foreach(var m in asset.meshes){if(data.materials[m.material].kind!="stone"&&data.materials[m.material].kind!="grass-blade")continue;reader.BaseStream.Position=m.offset;int nv=reader.ReadInt32(),ni=reader.ReadInt32();var v=new Vector3[nv];for(int i=0;i<nv;i++){v[i]=new(reader.ReadSingle(),reader.ReadSingle(),reader.ReadSingle());reader.BaseStream.Position+=36;}var ix=new int[ni];for(int i=0;i<ni;i++)ix[i]=reader.ReadInt32();int n=EnvironmentGrounding.Adjust(v,ix,data.materials[m.material],world);grounded+=n;components++;Need(v.All(p=>float.IsFinite(p.y)),"Finite grounded geometry "+m.material);}
 Need(grounded>0,"Actual V3 floating decoration components corrected: "+grounded);
 var result=new{limb_samples=5000,safe_npc_spawns=world.npcs.Length,river_recovery_locations=recovery,bridge_samples=10001,grounded_components=grounded,checked_meshes=components,unity_editor="NOT RUN",note="Actual navigation, height and grounding C# executed against a test-only numerical shim. No Unity physics, rendering or Play Mode claim."};File.WriteAllText(root+"/Review/world-validation.json",JsonSerializer.Serialize(result,new JsonSerializerOptions{WriteIndented=true}));
 }
}
