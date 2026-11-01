using System;
using System.Linq;
using Sunward;
using Sunward.Remaster;
using UnityEngine;
static class Program
{
    static int checks;
    static void Check(bool x,string message){checks++;if(!x)throw new Exception(message);}
    static string Signature(Strike s)=>string.Join("|",s.clip,s.duration,s.damage,s.range,s.arc,s.start,s.end,s.lunge,s.stagger);
    static Strike[] Strikes(WeaponDefinition d)=>d.light.Concat(d.heavy).Concat(new[]{d.charged,d.chargedHeavy,d.air}).ToArray();
    static void Main(string[] args)
    {
        Resources.Root=args[0];var pl=new NativePoseBank("NativePlayer/pl00/Poses");var wp=new NativePoseBank("Okami/wp2e/Poses");
        var tundra=OriginalWeaponCatalog.Definition(OriginalWeaponCatalog.Find("wp2e"),new WeaponDefinition(),new WeaponDefinition());
        Check(tundra.light.Length==8,"Incomplete eight-stage chain");
        for(int i=0;i<8;i++)
        {
            string state=tundra.light[i].clip;int index=TundraAttackRules.WeaponClip(state);Check(index==i+1,"Wrong bead action");
            var body=pl.Find("pl00_"+(0x544+i).ToString("x3"));var beads=wp.Find("wp2e_"+index.ToString("x3"));
            Check(body!=null && beads!=null && Math.Abs(body.Duration-beads.Duration)<1e-6,"Mismatched body/bead durations");
            Check(body.Samples==beads.Samples,"Mismatched source frame grids");
            bool moving=false;for(int k=pl.BoneCount;k<body.Position.Length;k++)
            {var a=body.Position[k];var b=body.Position[k%pl.BoneCount];if(Math.Abs(a.x-b.x)+Math.Abs(a.y-b.y)+Math.Abs(a.z-b.z)>.01f)moving=true;}
            Check(moving,"Static body pose in primary chain");
        }
        Check(TundraAttackRules.WeaponClip("NativeAttack_540")==-1,"Old static attack silently remapped");
        Check(TundraAttackRules.VisibleBeads(tundra.charged.clip)==6,"Collapsed cast beads remain visible");
        Check(TundraAttackRules.WeaponClip(tundra.air.clip)==15,"Wrong airborne bead action");
        var sequence=new AttackSequence();for(int i=0;i<24;i++)Check(sequence.Select(false,true,8,1)==i%8,"Combo loses stages or fails wrap");
        sequence.Reset();Check(sequence.Select(true,true,8,1)==0 && sequence.Select(false,true,8,1)==0,"Heavy/light cancellation leaks combo history");
        // Execute the real native sampler at varied frame rates and both forms.
        foreach(int fps in new[]{30,60,120})foreach(float speed in new[]{1f,2f})foreach(var strike in Strikes(tundra))
        {
            int index=TundraAttackRules.WeaponClip(strike.clip);var wc=wp.Find("wp2e_"+index.ToString("x3"));
            var bc=pl.Find(strike.clip==TundraAttackRules.Cast?"pl00_542":"pl00_"+strike.clip.Substring(7));
            var recovery=pl.Find("pl00_543");float duration=Math.Max(bc.Duration,wc.Duration)/speed;
            var bones=Enumerable.Range(0,pl.BoneCount).Select(_=>new Transform()).ToArray();var positions=new Vector3[pl.BoneCount];var scales=new Vector3[pl.BoneCount];var rotations=new Quaternion[pl.BoneCount];
            for(int frame=0;frame<=Math.Ceiling(duration*fps);frame++)
            {
                float phase=Math.Min(1,frame/(duration*fps));var selected=bc;float time=phase*bc.Duration;bool loop=false;
                if(strike.clip==TundraAttackRules.Cast){time=TundraAttackRules.CastTime(phase,wc.Duration,recovery.Duration,bc.Duration,out bool ending);selected=ending?recovery:bc;loop=!ending;}
                pl.Sample(selected,time,bones,positions,rotations,scales,1,loop);
                Check(bones.All(b=>float.IsFinite(b.localPosition.x)&&float.IsFinite(b.localPosition.y)&&float.IsFinite(b.localPosition.z)&&float.IsFinite(b.localRotation.w)),"Non-finite pose");
                if(phase==1 && strike.clip==TundraAttackRules.Cast)Check(selected==recovery && Math.Abs(time-recovery.Duration)<1e-5,"Cast fails to finish recovery");
            }
        }
        MonoBehaviour.Combat=new WolfCombat();var controller=MonoBehaviour.Combat;
        var view=new OriginalWeaponView();view.Load("wp2e","rosary");var rig=NativePaintedRig.Last;
        var tick=typeof(OriginalWeaponView).GetMethod("LateUpdate",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
        float Distance(Vector3 a,Vector3 b)=>MathF.Sqrt((a.x-b.x)*(a.x-b.x)+(a.y-b.y)*(a.y-b.y)+(a.z-b.z)*(a.z-b.z));
        foreach(int fps in new[]{30,60,120})
        {
            Time.deltaTime=1f/fps;
            foreach(var attack in Strikes(tundra))
            {
                view.BeginAttack(attack.clip);view.AttackPhase(.4f);tick.Invoke(view,null);
                Check(controller.lastCount==TundraAttackRules.VisibleBeads(attack.clip),"Wrong visible contact count");
                if(attack.clip==TundraAttackRules.Cast)Check(!rig.Root.renderers[2].enabled && !rig.Root.renderers[3].enabled,"Cast origin pile-up is visible");
                var frozen=rig.Bones.Select(b=>b.localPosition).ToArray();int calls=controller.callbacks;controller.game.Blocked=true;
                for(int k=0;k<5;k++)tick.Invoke(view,null);
                Check(rig.Bones.Select((b,k)=>Distance(b.localPosition,frozen[k])).All(d=>d<1e-7) && calls==controller.callbacks,"Paused beads/contacts continue moving");
                controller.game.Blocked=false;view.EndAttack();
                Check(rig.Bones.Select((b,k)=>Distance(b.localPosition,frozen[k])).All(d=>d<1e-7),"Attack end snaps directly to rest");
                for(int k=0;k<Math.Ceiling(TundraAttackRules.ReturnBlend*fps)+2;k++)tick.Invoke(view,null);
                Check(rig.Root.renderers.All(r=>r.enabled),"Rest never restores full bead set");
                Check(controller.callbacks==calls,"Cancelled/returning beads still resolve contacts");
            }
            view.BeginAttack(TundraAttackRules.Cast);view.AttackPhase(.5f);tick.Invoke(view,null);view.EndAttack();view.BeginAttack(TundraAttackRules.Primary(0));
            Check(rig.Root.renderers.All(r=>r.enabled),"Cast-to-combo transition loses beads");
            Check(rig.Bones.Skip(8).Take(6).All(b=>Distance(b.localPosition,Vector3.zero)>.1f),"Hidden beads reappear collapsed at origin");
            view.EndAttack();
        }
        // Exercise actual charge clearance at different player elevations; this
        // test checks the offset driver, not Unity's hierarchy/skinned rendering.
        var clearance=typeof(OriginalWeaponView).GetMethod("ChargeClearance",System.Reflection.BindingFlags.Instance|System.Reflection.BindingFlags.NonPublic);
        foreach(float playerY in new[]{0f,3f,-110f})
        {
            controller.transform.position=new Vector3(0,playerY,0);controller.HoldingCharge=true;
            foreach(var bone in rig.Bones)bone.position=new Vector3(0,playerY-.4f,0);
            clearance.Invoke(view,null);Check(Math.Abs(view.ChargeLift-1.1f)<.0001f,"Held beads remain below safe body height");
            float lift=rig.Root.transform.position.y;clearance.Invoke(view,null);Check(Math.Abs(rig.Root.transform.position.y-lift)<.0001f,"Charge height accumulates every frame");
            controller.HoldingCharge=false;clearance.Invoke(view,null);Check(view.ChargeLift>0&&view.ChargeLift<1.1f,"Charge release snaps its clearance");
            for(int i=0;i<120;i++)clearance.Invoke(view,null);Check(view.ChargeLift==0&&rig.Root.transform.position.y==0,"Charge lift persists after release");
        }
        var legacy=new OriginalWeaponView();legacy.Load("wp2d","rosary");legacy.BeginAttack("NativeAttack_540");legacy.AttackPhase(.5f);var legacyRig=NativePaintedRig.Last;
        Check(legacyRig.Bones.Any(b=>Distance(b.localPosition,Vector3.zero)>1),"Legacy rosary path was changed");
        foreach(var e in OriginalWeaponCatalog.All.Where(e=>e.id!="wp2e"))
        {
            var baseline=OriginalWeaponCatalogBaseline.Find(e.id);var old=OriginalWeaponCatalogBaseline.Definition(baseline,new WeaponDefinition(),new WeaponDefinition());var current=OriginalWeaponCatalog.Definition(e,new WeaponDefinition(),new WeaponDefinition());
            Check(Strikes(old).Select(Signature).SequenceEqual(Strikes(current).Select(Signature)),"Unrelated weapon changed: "+e.id);
        }
        Console.WriteLine("PASS "+checks+" checks: actual rules/catalogue/sequence/native sampler/weapon-view controller; 30/60/120 fps, both forms, all actions, 14 other weapons unchanged. Unity math/resource test doubles; not a Unity build.");
    }
}
