using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using UnityEngine;
using Sunward;
using Sunward.Editor;
static class EnvironmentChecks
{
 static void Need(bool ok,string label){if(!ok)throw new Exception(label);Console.WriteLine("PASS "+label);}
 public static void Run(string root,ValleyData data)
 {
  var records=data.assets.SelectMany(a=>a.meshes).ToArray();
  var arrays=new Dictionary<int,(Vector3[] v,int[] ix)>();
  (Vector3[] v,int[] ix) Read(int id)
  {
   if(arrays.TryGetValue(id,out var value))return value;
   using var r=new BinaryReader(File.OpenRead(root+"/Assets/Sunward/Data/Valley.bytes"));r.BaseStream.Position=records[id].offset;
   int nv=r.ReadInt32(),ni=r.ReadInt32();var v=new Vector3[nv];for(int i=0;i<nv;i++){v[i]=new(r.ReadSingle(),r.ReadSingle(),r.ReadSingle());r.BaseStream.Position+=36;}var ix=new int[ni];for(int i=0;i<ni;i++)ix[i]=r.ReadInt32();arrays[id]=(v,ix);return(v,ix);
  }
  var rails=data.world.boxes.Where(EnvironmentLayout.IsHomeRail).ToArray();
  Need(rails.Length==2,"Exactly the home crossing rail boxes selected; buildings and far crossing excluded");
  Need(rails.All(b=>Math.Abs(EnvironmentLayout.MoveRail(b.z)-8)>1.3f&&Math.Abs(EnvironmentLayout.MoveRail(b.z)-8)<1.5f),"Both bridge rail collision/navigation offsets match relocated deck");
  Valley.HomeBridgeSourceZ=EnvironmentLayout.HomeBridge;
  var t=data.world.terrain;
  Need(Valley.OnBridge(-23,8)&&!Valley.OnBridge(-23,12)&&Valley.OnBridge(-23,-14),"Water guard moves to new crossing and retains distant bridge");
  float gap=float.PositiveInfinity;
  using(var obj=new StreamWriter(root+"/Review/bridge-relocation-geometry.obj"))
  {
   int offset=1;obj.WriteLine("mtllib bridge-relocation-geometry.mtl");
   void Mesh(Vector3[] v,int[] ix,string material){obj.WriteLine("usemtl "+material);foreach(var p in v)obj.WriteLine(FormattableString.Invariant($"v {p.x} {-p.z} {p.y}"));for(int i=0;i<ix.Length;i+=3)obj.WriteLine($"f {ix[i]+offset} {ix[i+1]+offset} {ix[i+2]+offset}");offset+=v.Length;}
   for(int id=795;id<=799;id++)
   {
    var(v,ix)=Read(id);v=v.Select(p=>p+new Vector3(0,0,4)).ToArray();
    foreach(var p in v)gap=Math.Min(gap,p.z+12);
    if(id==795)foreach(var p in v)NeedHeight(p);
    Mesh(v,ix,"cedar");
   }
   var(ground,gix)=Read(751);ground=ground.Select(p=>new Vector3(p.x,Valley.RenderHeight(t,p),p.z)).ToArray();var subset=new List<int>();for(int i=0;i<gix.Length;i+=3)if(new[]{ground[gix[i]],ground[gix[i+1]],ground[gix[i+2]]}.All(p=>p.x>-40&&p.x<-12&&p.z>-25&&p.z<1))subset.AddRange(new[]{gix[i],gix[i+1],gix[i+2]});Mesh(ground,subset.ToArray(),"ground");
   var(rv,ri)=Read(794);var water=new List<int>();for(int i=0;i<ri.Length;i+=3)if(new[]{rv[ri[i]],rv[ri[i+1]],rv[ri[i+2]]}.All(p=>p.z>-25&&p.z<1))water.AddRange(new[]{ri[i],ri[i+1],ri[i+2]});Mesh(rv,water.ToArray(),"water");
   // Include home shell for a measurable approach-clearance diagnostic, not a Unity render.
   for(int id=600;id<=610;id++){var(v,ix)=Read(id);Mesh(v,ix,"house");}
  }
  Need(gap>2.6f,"Bridge is clear of home north wall by "+gap+" metres");
  File.WriteAllText(root+"/Review/bridge-relocation-geometry.mtl","newmtl cedar\nKd 0.42 0.27 0.15\nnewmtl ground\nKd 0.30 0.40 0.20\nnewmtl water\nKd 0.20 0.40 0.40\nnewmtl house\nKd 0.70 0.60 0.43\n");
  var stoneBounds=new List<Bounds>();
  foreach(int id in new[]{371,779,780,781,782,783,788,789,792,793})
  {
   var(v,ix)=Read(id);foreach(var island in SurfaceIslands.Find(v,ix))
   {var b=new Bounds(v[island[0]],Vector3.zero);foreach(int k in island)b.Encapsulate(v[k]);bool dedicated=id==792||id==793||id==788||id==789;if(!dedicated&&!RockSeating.Suitable(data.world,b))continue;stoneBounds.Add(new Bounds(b.center,b.size+new Vector3(.10f,.10f,.10f)));}
  }
  bool Inside(Vector3 p)=>stoneBounds.Any(b=>p.x>=b.min.x&&p.x<=b.max.x&&p.y>=b.min.y&&p.y<=b.max.y&&p.z>=b.min.z&&p.z<=b.max.z);
  int removedInk=0;
  for(int id=0;id<records.Length;id++)if(data.materials[records[id].material].kind=="ink")
  {var(v,ix)=Read(id);for(int i=0;i<ix.Length;i+=3)if(Inside(v[ix[i]])&&Inside(v[ix[i+1]])&&Inside(v[ix[i+2]]))removedInk++;}
  Need(removedInk>1000,"Baked rock outline geometry identified from actual source faces: "+removedInk);
  int banners=0;foreach(int id in new[]{408,409}){var(v,ix)=Read(id);for(int i=0;i<ix.Length;i+=3)if(EnvironmentLayout.OldBanner(v[ix[i]])&&EnvironmentLayout.OldBanner(v[ix[i+1]])&&EnvironmentLayout.OldBanner(v[ix[i+2]]))banners++;}
  Need(banners>20,"Unsupported old red/blue banner faces selected: "+banners);
  int logs=0;float minimum=float.PositiveInfinity;
  for(int i=0;i<32;i++)
  {
   var p=EnvironmentLayout.ArenaPoint(i*Mathf.PI*2/32);var q=EnvironmentLayout.ArenaPoint((i+1)*Mathf.PI*2/32);
   if(EnvironmentLayout.GateOpening(p)||EnvironmentLayout.GateOpening(q))continue;
   for(int j=0;j<=20;j++){var v=Vector3.Lerp(p,q,j/20f);minimum=Math.Min(minimum,MathF.Sqrt((v.x-35)*(v.x-35)+v.z*v.z)-.235f);}logs++;
  }
  Need(logs>25&&minimum>18.3f,"Substantial timber stays outside combat/wolf boundary and preserves west gate");
  Need(EnvironmentLayout.Street(new Bounds(new Vector3(0,3,-12),new Vector3(4,6,4)))&&EnvironmentLayout.Street(new Bounds(new Vector3(0,3,14),new Vector3(4,6,4)))&&!EnvironmentLayout.Street(new Bounds(new Vector3(14,3,2),new Vector3(4,6,4))),"Tree cleanup covers both ends of the market and excludes distant trees");
  RevolvedGeometry.Build(RevolvedGeometry.LanternRoof,40,out var cv,out var cu,out var ci);var edges=new Dictionary<(int,int),int>();for(int i=0;i<ci.Length;i+=3)for(int j=0;j<3;j++){int a=ci[i+j],b=ci[i+(j+1)%3];var key=a<b?(a,b):(b,a);edges.TryGetValue(key,out int count);edges[key]=count+1;}Need(edges.Values.All(n=>n==2),"New 40-sided arena lantern roofs are actually closed");
  File.WriteAllText(root+"/Review/environment-validation.json",JsonSerializer.Serialize(new{home_bridge_source_z=8,home_wall_clearance=gap,selected_legacy_ink_faces=removedInk,selected_old_banner_faces=banners,arena_logs=logs,arena_log_minimum_radius=minimum,closed_lantern_roofs=true,unity_editor="NOT RUN",note="Source geometry and numerical C# rules tested. Does not verify Unity shaders, Play Mode, migration execution or native visual quality."},new JsonSerializerOptions{WriteIndented=true}));
  Valley.HomeBridgeSourceZ=12;
 }
 static void NeedHeight(Vector3 p){if(Math.Abs(p.y-Valley.BridgeHeight((p.x+27.8f)/9.6f))>.003f)throw new Exception("Bridge render/collision height mismatch");}
}
