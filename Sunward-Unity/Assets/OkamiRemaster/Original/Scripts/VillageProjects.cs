using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    [DefaultExecutionOrder(85)]
    public sealed class VillageProjects:MonoBehaviour
    {
        public GameFlow game;public bool Playing{get;private set;}GameObject[] roots=new GameObject[4];int applied=-1,showing;float clock;OrbitCamera camera;readonly List<GameObject> visitors=new List<GameObject>();
        public static readonly Vector3 Tea=new Vector3(-13,0,6),Farm=new Vector3(39.8f,0,37),Bridge=new Vector3(-23,0,-12),Pond=VillageFishing.Bank+new Vector3(3.8f,0,1.8f);
        Vector3 Centre(int i)=>i==0?Tea:i==1?Farm:i==2?Bridge:Pond;
        Vector3 Ground(Vector3 p){p.y=game.valley.Height(p)+.025f;return p;}
        GameObject Put(Transform root,string resource,Vector3 at,Vector3 size,float yaw=0,float lift=0)
        {at=Ground(at);at.y+=lift;var obj=VillageAdventures.Prop(root,resource,Vector3.zero,size,yaw);if(obj)obj.transform.position=at;return obj;}
        public bool Build(int i)
        {
            var festival=game.GetComponent<FestivalChallenges>();if(festival && festival.Active)return false;
            if(Playing || game.CinematicActive || game.Health<=0 || game.InTrial || i<0 || i>3 || Vector3.Distance(game.Player.transform.position,FestivalChallenges.Board)>4 || !VillageAdventureRules.BuildProject(game.Profile,i))return false;
            game.Save.Save();Apply();game.Close();showing=i;clock=0;Playing=true;game.Combat.Cancel();game.Player.StopMotion();game.Player.Locked=true;camera=FindFirstObjectByType<OrbitCamera>();if(camera)camera.BeginCinematic();game.Audio.Cue("collect");return true;
        }
        void Start(){Apply();}
        void Apply()
        {
            applied=game.Profile.adventures.projects;
            for(int i=0;i<4;i++)if(VillageAdventureRules.Project(game.Profile,i) && !roots[i])
            {
                var root=new GameObject("Village restoration · "+VillageAdventureRules.ProjectNames[i]);root.transform.SetParent(transform,false);roots[i]=root;
                if(i==0)
                {
                    var c=Ground(Tea);Put(root.transform,"dr0d",c,new Vector3(1.8f,.09f,1.2f),0,.56f);
                    foreach(int x in new[]{-1,1})foreach(int z in new[]{-1,1})Put(root.transform,"farm-post",c+new Vector3(x*.7f,0,z*.43f),new Vector3(.12f,.56f,.12f));
                    foreach(int side in new[]{-1,1})
                    {var seat=c+Vector3.right*side*1.45f;Put(root.transform,"heaven-tea-seat",seat,new Vector3(.9f,.27f,.9f));Put(root.transform,"heaven-tea-tray",c+Vector3.right*side*.52f,new Vector3(.4f,.15f,.28f),side<0?90:270,.65f);TeaVisitor(root.transform,Ground(seat)+Vector3.up*.25f,side<0?90:270,side);}
                    foreach(var at in new[]{new Vector3(-3,0,2),new Vector3(3,0,2)}){var tree=Put(root.transform,"vt17",c+at,new Vector3(3,4,3));if(tree)tree.AddComponent<OriginalBillboard>();}
                    foreach(int n in new[]{-1,1})Put(root.transform,"vt35",c+new Vector3(n*3,0,-1),new Vector3(.8f,1.6f,.8f));
                    Flowers(root.transform,c,3.3f);
                }
                else if(i==1)
                {
                    var c=Ground(Farm);Put(root.transform,"farm-pitched-roof",c,new Vector3(3.7f,1.4f,3.5f),0,1.5f);
                    foreach(int x in new[]{-1,1})foreach(int z in new[]{-1,1})Put(root.transform,"farm-post",c+new Vector3(x*1.2f,0,z*1.1f),new Vector3(.2f,1.5f,.2f));
                    Put(root.transform,"vt5e",c+new Vector3(0,0,.8f),new Vector3(1.8f,.25f,.9f));Put(root.transform,"vt49",c+new Vector3(-1,0,-.9f),new Vector3(.6f,.3f,.6f));
                    Put(root.transform,"vt35",new Vector3(43.8f,0,28),new Vector3(.8f,1.6f,.8f));
                }
                else if(i==2)
                {
                    foreach(float x in new[]{-29f,-17f})foreach(float z in new[]{-14f,-10f}){Put(root.transform,"vt35",new Vector3(x,0,z),new Vector3(.8f,1.6f,.8f));Put(root.transform,"vt46",new Vector3(x+.8f,0,z),new Vector3(1.1f,1,1.1f));}
                }
                else
                {
                    var c=Ground(Pond);Put(root.transform,"heaven-tea-seat",c,new Vector3(1.2f,.35f,.8f));Put(root.transform,"heaven-tea-seat",c+Vector3.forward*1.5f,new Vector3(1.2f,.35f,.8f));Put(root.transform,"vt35",c+new Vector3(1.5f,0,.7f),new Vector3(.8f,1.7f,.8f));Flowers(root.transform,c,2.4f);
                    TeaVisitor(root.transform,c+Vector3.up*.33f,220,3);
                }
            }
        }
        void Flowers(Transform root,Vector3 c,float radius)
        {for(int i=0;i<8;i++){float a=i*Mathf.PI*.25f;Put(root,i%2==0?"vt46":"vt47",c+new Vector3(Mathf.Sin(a)*radius,0,Mathf.Cos(a)*radius),new Vector3(1.1f,1,1.1f),i*37);}}
        void TeaVisitor(Transform root,Vector3 at,float yaw,int phase)
        {
            var person=new GameObject("Travelling pilgrim · using the restored village garden");person.SetActive(false);person.transform.SetParent(root,false);person.transform.position=at;person.transform.rotation=Quaternion.Euler(0,yaw,0);var a=person.AddComponent<OriginalActor>();a.game=game;a.resource="Okami/heaven-tea-hm50";a.idle=a.walk=a.run=a.windup=a.strike=a.recover=a.death="hm05_003";a.modelScale=.82f;var tea=person.AddComponent<HeavenTeaGuest>();tea.actor=a;tea.phase=phase*.23f;person.SetActive(true);visitors.Add(person);
        }
        void Update()
        {
            if(!game)return;if(applied!=game.Profile.adventures.projects)Apply();
            foreach(var v in visitors)if(v)v.SetActive(!game.Profile.night);
            if(Playing){clock+=Time.unscaledDeltaTime;if(camera)camera.CinematicFrame(Ground(Centre(showing))+Vector3.up,Mathf.Lerp(25,65,Mathf.Clamp01(clock/3.2f)),28,showing==2?16:9,47);if(clock>=3.2f)Skip();return;}
        }
        public void Skip(){if(!Playing)return;Playing=false;if(camera)camera.EndCinematic();if(game && game.Player)game.Player.Locked=game.Health<=0;game.Notify(VillageAdventureRules.ProjectNames[showing]+" restored · +25 Praise · saved");}
        public void Cancel(){if(Playing){Playing=false;if(camera)camera.EndCinematic();if(game && game.Player)game.Player.Locked=game.Health<=0;}}
        void OnDisable(){Cancel();}
    }
}
