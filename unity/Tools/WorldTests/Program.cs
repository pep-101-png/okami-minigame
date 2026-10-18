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
 var data=JsonUtility.FromJson<ValleyData>(File.ReadAllText(root+"/Assets/Sunward/Data/Valley.json"));var world=data.world;
 foreach(var npc in world.npcs){var p=new Vector3(npc.position[0],npc.position[1],npc.position[2]);Need(VillageNavigation.FindSafe(world,p,out var safe)&&VillageNavigation.Clear(world,safe),"Safe spawn: "+npc.name);}
 int recovery=0;for(int z=-29;z<=29;z+=2){var water=new Vector3(Valley.RiverX(z),-1,-z);Need(VillageNavigation.FindSafe(world,water,out var safe,.55f,16)&&Valley.Depth(safe)<=.1f,"River escape near z="+z);recovery++;}
 for(int i=0;i<=10000;i++){float h=Valley.BridgeHeight(i/10000f);if(!float.IsFinite(h)||h<.1f||h>.521f)throw new Exception("Invalid bridge height");}
 Need(Valley.BridgeHeight(0)==.1f&&Valley.BridgeHeight(1)==.1f,"Bridge finite and level endpoints");
 foreach(var box in world.boxes)Need(!VillageNavigation.Clear(world,new Vector3(box.x,0,-box.z)),"Building/rail rejected");
 int grounded=0,components=0;
 using var reader=new BinaryReader(File.OpenRead(root+"/Assets/Sunward/Data/Valley.bytes"));
 foreach(var asset in data.assets.Where(a=>a.name=="TownV3"))foreach(var m in asset.meshes){if(data.materials[m.material].kind!="stone"&&data.materials[m.material].kind!="grass-blade")continue;reader.BaseStream.Position=m.offset;int nv=reader.ReadInt32(),ni=reader.ReadInt32();var v=new Vector3[nv];for(int i=0;i<nv;i++){v[i]=new(reader.ReadSingle(),reader.ReadSingle(),reader.ReadSingle());reader.BaseStream.Position+=36;}var ix=new int[ni];for(int i=0;i<ni;i++)ix[i]=reader.ReadInt32();int n=EnvironmentGrounding.Adjust(v,ix,data.materials[m.material],world);grounded+=n;components++;Need(v.All(p=>float.IsFinite(p.y)),"Finite grounded geometry "+m.material);}
 Need(grounded>0,"Actual V3 floating decoration components corrected: "+grounded);
 var result=new{safe_npc_spawns=world.npcs.Length,river_recovery_locations=recovery,bridge_samples=10001,grounded_components=grounded,checked_meshes=components,unity_editor="NOT RUN",note="Actual navigation, height and grounding C# executed against a test-only numerical shim. No Unity physics, rendering or Play Mode claim."};File.WriteAllText(root+"/Review/world-validation.json",JsonSerializer.Serialize(result,new JsonSerializerOptions{WriteIndented=true}));
 }
}
