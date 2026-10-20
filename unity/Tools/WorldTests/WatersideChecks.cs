using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text.Json;
using UnityEngine;
using Sunward;
using Sunward.Editor;
static class WatersideChecks
{
 static void Need(bool value,string message){if(!value)throw new Exception(message);Console.WriteLine("PASS "+message);}
 public static void Run(string root,ValleyData data)
 {
  var world=data.world;world.terrain.exactSurface=world.terrain.gardenPondBasin=true;world.terrain.visualRelief=true;
  var t=world.terrain;int id=0,stones=0,samples=0,terrainSamples=0;float worst=0;
  var rockMeshes=new List<(Vector3[],int[])>();Vector3[] ground=null,river=null;int[] groundIx=null,riverIx=null;
  using var reader=new BinaryReader(File.OpenRead(root+"/Assets/Sunward/Data/Valley.bytes"));
  foreach(var asset in data.assets)foreach(var record in asset.meshes)
  {
   int n=id++;if(n!=751&&n!=794&&!RockSeating.Source(n))continue;reader.BaseStream.Position=record.offset;int nv=reader.ReadInt32(),ni=reader.ReadInt32();var v=new Vector3[nv];for(int k=0;k<nv;k++){v[k]=new(reader.ReadSingle(),reader.ReadSingle(),reader.ReadSingle());reader.BaseStream.Position+=36;}var ix=new int[ni];for(int k=0;k<ni;k++)ix[k]=reader.ReadInt32();
   if(n==794){river=v;riverIx=ix;continue;}
   if(n==751){for(int k=0;k<v.Length;k++)v[k].y=Valley.RenderHeight(t,v[k]);ground=v;groundIx=ix;continue;}
   foreach(var island in SurfaceIslands.Find(v,ix))
   {
    var b=new Bounds(v[island[0]],Vector3.zero);foreach(int k in island)b.Encapsulate(v[k]);bool dedicated=n==792||n==793||n==788||n==789;if(!dedicated&&!RockSeating.Suitable(world,b))continue;
    float bottom=RockSeating.Bottom(world,b),highest=float.NegativeInfinity;for(int z=0;z<=8;z++)for(int x=0;x<=8;x++)highest=Mathf.Max(highest,Valley.TerrainHeight(t,new Vector3(b.min.x+b.size.x*x/8,0,b.min.z+b.size.z*z/8)));
    float height=Mathf.Max(b.size.y,highest-bottom+b.size.y*.30f);SeatedStoneGeometry.Build((n+island[0])%4,out var sv,out var si);
    float minX=sv.Min(p=>p.x),maxX=sv.Max(p=>p.x),minZ=sv.Min(p=>p.z),maxZ=sv.Max(p=>p.z);
    for(int k=0;k<sv.Length;k++)sv[k]=new Vector3(b.center.x+sv[k].x*b.size.x/(maxX-minX),bottom+sv[k].y*height,b.center.z+sv[k].z*b.size.z/(maxZ-minZ));
    for(int k=0;k<si.Length;k+=3){var a=sv[si[k]];var c=sv[si[k+1]];var d=sv[si[k+2]];if(a.y>bottom+.0001f||c.y>bottom+.0001f||d.y>bottom+.0001f)continue;for(int u=0;u<=4;u++)for(int q=0;q<=4-u;q++){var p=a*(1-(u+q)/4f)+c*(u/4f)+d*(q/4f);float gap=p.y-Valley.TerrainHeight(t,p);NeedGap(gap,n);samples++;}}
    if(b.center.x>-32&&b.center.x<-9&&b.center.z>-31&&b.center.z<-14)rockMeshes.Add((sv,si));stones++;
   }
  }
  for(int i=0;i<groundIx.Length;i+=117){int k=i-i%3;var p=ground[groundIx[k]]*.2f+ground[groundIx[k+1]]*.35f+ground[groundIx[k+2]]*.45f;float error=Math.Abs(p.y-Valley.TerrainHeight(t,p));worst=Math.Max(worst,error);terrainSamples++;}
  Need(worst<.0005f,"Physical sampler matches actual exported terrain triangles, max error "+worst);
  var bridge=new Vector3(-23,0,-12);Need(Valley.SurfaceHeight(t,bridge)-Valley.TerrainHeight(t,bridge)>.3f,"Rock foundation distinguishes riverbed from bridge WALKING surface");
  for(int i=0;i<360;i++){float a=i*Mathf.PI/180;var p=new Vector3(GardenPond.X+Mathf.Cos(a)*GardenPond.RadiusX*1.15f,0,GardenPond.Z+Mathf.Sin(a)*GardenPond.RadiusZ*1.15f);NeedRim(Valley.TerrainHeight(t,p));}
  Need(GardenPond.Water-Valley.TerrainHeight(t,new Vector3(GardenPond.X,0,GardenPond.Z))>.35f,"Pond water sits inside a real excavated basin");
  SeatedStoneGeometry.Build(0,out var unit,out var unitIx);var edges=new Dictionary<(int,int),int>();double volume=0;for(int k=0;k<unitIx.Length;k+=3){var a=unit[unitIx[k]];var b=unit[unitIx[k+1]];var c=unit[unitIx[k+2]];volume+=(a.x*(b.y*c.z-b.z*c.y)+a.y*(b.z*c.x-b.x*c.z)+a.z*(b.x*c.y-b.y*c.x))/6;for(int j=0;j<3;j++){int u=unitIx[k+j],v=unitIx[k+(j+1)%3];var key=u<v?(u,v):(v,u);edges.TryGetValue(key,out int count);edges[key]=count+1;}}
  Need(edges.Values.All(n=>n==2)&&volume>0,"Replacement stones are fully closed with outward winding");
  using(var obj=new StreamWriter(root+"/Review/waterside-geometry.obj"))
  {
   int offset=1;obj.WriteLine("mtllib waterside-geometry.mtl");void Mesh(Vector3[] v,int[] ix,string mat){obj.WriteLine("usemtl "+mat);foreach(var p in v)obj.WriteLine(FormattableString.Invariant($"v {p.x} {-p.z} {p.y}"));for(int k=0;k<ix.Length;k+=3)obj.WriteLine($"f {ix[k]+offset} {ix[k+1]+offset} {ix[k+2]+offset}");offset+=v.Length;}
   var subset=new List<int>();for(int k=0;k<groundIx.Length;k+=3)if(new[]{ground[groundIx[k]],ground[groundIx[k+1]],ground[groundIx[k+2]]}.All(p=>p.x>-32&&p.x<-9&&p.z>-31&&p.z<-14))subset.AddRange(new[]{groundIx[k],groundIx[k+1],groundIx[k+2]});Mesh(ground,subset.ToArray(),"earth");foreach(var rock in rockMeshes)Mesh(rock.Item1,rock.Item2,"stone");
   var ri=new List<int>();for(int k=0;k<riverIx.Length;k+=3)if(new[]{river[riverIx[k]],river[riverIx[k+1]],river[riverIx[k+2]]}.All(p=>p.z>-31&&p.z<-14))ri.AddRange(new[]{riverIx[k],riverIx[k+1],riverIx[k+2]});Mesh(river,ri.ToArray(),"water");
   var water=new List<Vector3>{new(GardenPond.X,GardenPond.Water,GardenPond.Z)};var wi=new List<int>();for(int i=0;i<96;i++){float a=i*Mathf.PI*2/96;water.Add(new(GardenPond.X+Mathf.Cos(a)*GardenPond.RadiusX*1.15f,GardenPond.Water,GardenPond.Z+Mathf.Sin(a)*GardenPond.RadiusZ*1.15f));wi.AddRange(new[]{0,(i+1)%96+1,i+1});}Mesh(water.ToArray(),wi.ToArray(),"water");
  }
  File.WriteAllText(root+"/Review/waterside-geometry.mtl","newmtl earth\nKd 0.42 0.52 0.28\nnewmtl stone\nKd 0.42 0.46 0.40\nnewmtl water\nKd 0.19 0.39 0.36\nd 0.66\n");
  File.WriteAllText(root+"/Review/waterside-validation.json",JsonSerializer.Serialize(new{stones,base_triangle_support_samples=samples,terrain_triangle_samples=terrainSamples,maximum_terrain_error=worst,pond_rim_samples=360,closed_stone_geometry=true,blender_diagnostic="Geometry preview only, not Unity",unity_editor="NOT RUN"},new JsonSerializerOptions{WriteIndented=true}));
  Console.WriteLine($"PASS {stones} stones, {samples} actual underside support samples and 360 pond-rim samples");
 }
 static void NeedGap(float gap,int id){if(gap>.001f)throw new Exception("Unsupported underside on source "+id+" gap "+gap);}
 static void NeedRim(float h){if(h<GardenPond.Water+.07f)throw new Exception("Pond rim below water clearance: "+h);}
}
