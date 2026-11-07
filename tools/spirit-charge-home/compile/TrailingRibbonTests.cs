using System;using System.Linq;using System.Reflection;using Sunward.Remaster;using UnityEngine;
static class TrailingRibbonTests
{
 static int n;static BindingFlags flags=BindingFlags.NonPublic|BindingFlags.Instance;
 static void Check(bool b,string s){n++;if(!b)throw new Exception(s);}
 static T Get<T>(object o,string name)=>(T)o.GetType().GetField(name,flags).GetValue(o);
 static void Set(object o,string name,object value)=>o.GetType().GetField(name,flags).SetValue(o,value);
 static void Call(object o,string name)=>o.GetType().GetMethod(name,flags).Invoke(o,null);
 public static void Run()
 {
  foreach(int fps in new[]{15,30,60,120})
  {
   var body=new NativeAmaterasu();Call(body,"Awake");body.ApplyPowerForm(2);var effect=new SpectralTendrils();Set(effect,"native",body);Time.unscaledDeltaTime=1f/fps;Time.deltaTime=0;Call(effect,"LateUpdate");var rigs=Get<NativePaintedRig[]>(effect,"rigs");var mounts=Get<Vector3[]>(effect,"mounts");var scales=rigs.Select(r=>r.Root.transform.localScale).ToArray();var bind=rigs.Select(r=>r.Bones.Select(b=>b.localPosition).ToArray()).ToArray();
   foreach(string field in new[]{"lengths","rates","phases","headings","gains","rolls","bows"})Check(Get<float[]>(effect,field).Distinct().Count()==6,"Paired ribbon profile restored: "+field);
   float maximum=0;
   for(int frame=0;frame<fps*6;frame++)
   {
    body.Torso.position=new Vector3(frame*.003f,1,0);Call(effect,"LateUpdate");
    for(int i=0;i<rigs.Length;i++)
    {
     Check(Vector3.Distance(rigs[i].Root.transform.position,body.Torso.position+mounts[i])<.0001f,"Ribbon root elastically lags torso");Check(Vector3.Distance(rigs[i].Root.transform.localScale,scales[i])<.0001f,"Ribbon length pulses");
     foreach(var bone in rigs[i].Bones){var q=bone.localRotation;double norm=Math.Sqrt(q.x*q.x+q.y*q.y+q.z*q.z+q.w*q.w);float degrees=(float)(2*Math.Acos(Math.Min(1,Math.Abs(q.w)/norm))*180/Math.PI);maximum=Math.Max(maximum,degrees);Check(degrees<12,"Joint bend "+degrees+" at "+fps+"fps, frame "+frame+", stream "+i);Check(Vector3.Distance(bone.localScale,Vector3.one)<.0001f,"Wind stretches original bones");}
     for(int b=0;b<rigs[i].Bones.Length;b++)Check(Vector3.Distance(rigs[i].Bones[b].localPosition,bind[i][b])<.0001f,"Wind lengthens the bind chain");
    }
   }
   Check(maximum>.2f,"Wind motion disappeared");Console.WriteLine("Maximum normalized local ribbon bend at "+fps+"fps: "+maximum);body.ApplyPowerForm(1);Call(effect,"LateUpdate");Check(rigs.All(r=>!r.Root.activeSelf),"Second form displays full-power trails");
  }
  Console.WriteLine("PASS "+n+" actual independent-profile, small-angle native wind, pinned-root and fixed-length ribbon checks at 15/30/60/120fps; engine doubles, not Unity");
 }
}
