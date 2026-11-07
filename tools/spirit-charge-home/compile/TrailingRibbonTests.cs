using System;using System.Linq;using System.Reflection;using Sunward.Remaster;using UnityEngine;
static class TrailingRibbonTests
{
 static int n;static BindingFlags f=BindingFlags.NonPublic|BindingFlags.Instance;
 static void Check(bool b,string s){n++;if(!b)throw new Exception(s);}
 static T Get<T>(object o,string k)=>(T)o.GetType().GetField(k,f).GetValue(o);
 static void Set(object o,string k,object v)=>o.GetType().GetField(k,f).SetValue(o,v);
 static void Call(object o,string m)=>o.GetType().GetMethod(m,f).Invoke(o,null);
 static Vector3 V(Vector4 v)=>new Vector3(v.x,v.y,v.z);
 public static void Run()
 {
  foreach(int fps in new[]{15,30,60,120})
  {
   var body=new NativeAmaterasu();Call(body,"Awake");body.ApplyPowerForm(2);var effect=new SpectralTendrils();Set(effect,"native",body);Time.unscaledDeltaTime=1f/fps;Time.deltaTime=0;Call(effect,"LateUpdate");var rigs=Get<NativePaintedRig[]>(effect,"rigs");var mounts=Get<Vector3[]>(effect,"mounts");var scales=rigs.Select(r=>r.Root.transform.localScale).ToArray();
   foreach(string k in new[]{"lengths","rates","phases","headings","breadth"})Check(Get<float[]>(effect,k).Distinct().Count()==6,"Paired wisp profile "+k);
   bool moving=false;var before=Get<Vector4[][]>(effect,"curves").Select(row=>row.Select(V).ToArray()).ToArray();
   for(int frame=0;frame<fps*6;frame++)
   {
    body.Torso.position=new Vector3(frame*.003f,1,0);Call(effect,"LateUpdate");var curves=Get<Vector4[][]>(effect,"curves");
    for(int i=0;i<6;i++)
    {
     Check(Vector3.Distance(rigs[i].Root.transform.position,body.Torso.position+mounts[i])<.0001f,"Wisp root elastically lags");Check(Vector3.Distance(scales[i],rigs[i].Root.transform.localScale)<.0001f,"Wisp stretches");
     for(int j=1;j<curves[i].Length;j++)
     {
      var a=V(curves[i][j-1]);var b=V(curves[i][j]);var d=b-a;Check(Math.Abs(d.magnitude-3.8271732f/40)<.00001f,"Arc length pulses");Check(d.z>0 && d.z/d.magnitude>.74f,"Wisp turns sideways into a fan");if(Vector3.Distance(b,before[i][j])>.01f)moving=true;
     }
    }
   }
   Check(moving,"Continuous wind freezes with timeScale zero");body.ApplyPowerForm(1);Call(effect,"LateUpdate");Check(rigs.All(r=>!r.Root.activeSelf),"Second form displays wisps");
  }
  Console.WriteLine("PASS "+n+" actual continuous-curve wind, fixed arc length, independent profiles, pinned roots and third-form visibility contracts; engine doubles, not Unity");
 }
}
