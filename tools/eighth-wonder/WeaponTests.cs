using System;using System.Reflection;using Sunward;using Sunward.Remaster;using UnityEngine;
static class WeaponTests
{
 static int checks;static BindingFlags f=BindingFlags.Instance|BindingFlags.NonPublic;
 static void Check(bool b,string s){checks++;if(!b)throw new Exception(s);}
 static void Call(object o,string m)=>o.GetType().GetMethod(m,f).Invoke(o,null);
 static T Get<T>(object o,string n)=>(T)o.GetType().GetField(n,f).GetValue(o);
 static float Difference(Quaternion a,Quaternion b)=>Math.Abs(a.x-b.x)+Math.Abs(a.y-b.y)+Math.Abs(a.z-b.z)+Math.Abs(a.w-b.w);
 static void Main(string[] args)
 {
  Resources.Root=args[0];
  foreach(int fps in new[]{15,30,60,120})
  {
   var view=new OriginalWeaponView();view.Load("wp28","glaive");Check(Get<NativePoseBank.Clip>(view,"idle").Name=="wp28_000","Eighth Wonder selects static carrier instead of native wheel idle");var rig=Get<NativePaintedRig>(view,"rig");var before=rig.Bones[2].localRotation;Time.deltaTime=1f/fps;for(int i=0;i<fps;i++)Call(view,"LateUpdate");Check(Difference(before,rig.Bones[2].localRotation)>.1f,"Equipped wheel is frozen");
   foreach(string clip in new[]{"NativeAttack_520","NativeAttack_521","NativeAttack_522","NativeAttack_523","NativeAttack_524","NativeAttack_525"}){before=rig.Bones[2].localRotation;view.BeginAttack(clip);for(int i=0;i<fps/2;i++){view.AttackPhase(i/(float)fps);Call(view,"LateUpdate");}var reference=new Transform();new NativePoseBank("Okami/wp28/Poses").SampleBone(Get<NativePoseBank.Clip>(view,"idle"),Get<float>(view,"idleTime"),reference,2);Check(Difference(reference.localRotation,rig.Bones[2].localRotation)<.001f,"Attack interrupts original wheel sampling: "+clip);view.EndAttack();}
   var prop=VillageFestival.Place(new GameObject().transform,"Okami/wp28",Vector3.zero,new Vector3(2.5f,.7f,8),new Vector3(-90,0,0));var motion=prop.GetComponent<EighthWonderMotion>();Check(motion!=null&&motion.visual!=null,"Display/falling blade has no wheel component");var visual=prop.GetComponent<OriginalVisual>();var propRig=Get<NativePaintedRig>(visual,"rig");var carrier=propRig.Bones[1].localRotation;var parentRotation=prop.transform.rotation;before=propRig.Bones[2].localRotation;for(int i=0;i<fps;i++)Call(motion,"Update");Check(Difference(before,propRig.Bones[2].localRotation)>.1f,"Displayed wheel is frozen");Check(Difference(carrier,propRig.Bones[1].localRotation)<.0001f&&Difference(parentRotation,prop.transform.rotation)<.0001f,"Wheel animation tips the falling sword sideways");Check(Math.Abs(propRig.Bones[2].localPosition.z-.285f)<.0001f,"Wheel/hilt is collapsed into blade");
  }
  var bank=new NativePoseBank("Okami/wp28/Poses");var bone=new Transform();bank.SampleBone(bank.Find("wp28_000"),2,bone,2);var at=bone.localRotation;bank.SampleBone(bank.Find("wp28_000"),10,bone,2);Check(Difference(at,bone.localRotation)<.001f,"Native wheel loop snaps across its cycle");
  var thunder=new OriginalWeaponView();thunder.Load("wp29","glaive");Check(Get<NativePoseBank.Clip>(thunder,"idle").Name=="wp29_001","Unrequested Thunder carrier was changed");
  Console.WriteLine("PASS "+checks+" real native equipped/displayed wheel motion, attack continuity, fixed falling orientation and original loop cases. Engine doubles; Unity playback unverified.");
 }
}
