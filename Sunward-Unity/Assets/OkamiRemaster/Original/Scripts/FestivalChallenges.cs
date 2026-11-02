using System.Collections.Generic;
using UnityEngine;
namespace Sunward.Remaster
{
    // Optional village games; no arena flags, health, upgrades or weapon unlocks.
    public sealed class FestivalChallenges : MonoBehaviour
    {
        public GameFlow game;
        public static readonly Vector3 Board=new Vector3(3.3f,0,-9);
        public bool Active=>mode!=0;
        int mode,checkpoint,delivered,decorated=-1;
        float remaining;
        readonly HashSet<int> freshCrops=new HashSet<int>();
        readonly List<GameObject> checkpoints=new List<GameObject>();
        GameObject rewards;
        static readonly Vector3[] Route={new Vector3(0,0,-10),new Vector3(2,0,-2),new Vector3(0,0,10),new Vector3(11,0,20),new Vector3(19,0,24),new Vector3(35,0,24)};
        static readonly string[] RewardResources={"Okami/vt99","Okami/vt77","Okami/vt55"};
        public static string RewardName(int index)=>index==0?"Decorative fan":index==1?"Beckoning cat":"Flower vase";
        public string Status=>mode==1?"LANTERN DASH · "+checkpoint+" / 6 · "+Mathf.CeilToInt(remaining)+"s":mode==2?"HARVEST RELAY · dug "+freshCrops.Count+" / 3 · delivered "+delivered+" / 3 · "+Mathf.CeilToInt(remaining)+"s":"Festival challenges · earn tokens at night";
        void Start()
        {
            if(!game)game=GetComponent<GameFlow>();
            var board=new GameObject("Original festival noticeboard");board.transform.SetParent(transform,false);board.transform.position=Ground(Board);
            VillageFestival.Place(board.transform,"Okami/vt11",Vector3.zero,new Vector3(.9f,1.8f,.15f),new Vector3(0,-90,0));
        }
        Vector3 Ground(Vector3 p){p.y=game.valley.Height(p)+.025f;return p;}
        public void Begin(int kind)
        {
            if(kind!=1 && kind!=2)return;
            if(!game.Profile.night){game.Notify("Festival games begin at night · sleep in Ammy’s bed first");return;}
            if(game.InTrial || game.Health<=0 || VillageInteriors.AnyRoom(game.Player.transform.position))return;
            Clear();mode=kind;remaining=kind==1?55:90;checkpoint=delivered=0;freshCrops.Clear();
            if(kind==1)
                for(int i=0;i<Route.Length;i++)
                {
                    var point=new GameObject("Festival route lantern "+(i+1));point.transform.SetParent(transform,false);point.transform.position=Ground(Route[i]);
                    VillageFestival.Place(point.transform,"Okami/vt32",Vector3.zero,new Vector3(.38f,.65f,.38f),Vector3.zero);
                    var light=point.AddComponent<Light>();light.type=LightType.Point;light.color=new Color(1,.7f,.3f);light.range=3;light.intensity=2;light.shadows=LightShadows.None;
                    checkpoints.Add(point);point.SetActive(i==0);
                }
            game.Close();game.Notify(kind==1?"Lantern dash · follow the glowing lanterns to the northeast farm":"Harvest relay · dig three different vegetables, then hand three to the farmer");
        }
        public void Harvest(int crop){if(mode==2 && freshCrops.Count<3)freshCrops.Add(crop);}
        public void Deliver(int count)
        {
            if(mode!=2)return;
            delivered+=Mathf.Min(Mathf.Max(0,count),Mathf.Max(0,freshCrops.Count-delivered));
            if(delivered>=3)Win();
        }
        public void Cancel(){Clear();game.Notify("Festival challenge cancelled · no tokens spent");}
        void Clear(){mode=0;foreach(var p in checkpoints)if(p)Destroy(p);checkpoints.Clear();}
        void Win()
        {
            Clear();game.Profile.festivalTokens=Mathf.Min(1000000,game.Profile.festivalTokens+3);game.Profile.festivalWins++;game.Save.Save();game.Notify("Festival challenge won · +3 tokens · visit the board for home decorations");
        }
        public void Buy(int index)
        {
            if(index<0 || index>2 || (game.Profile.festivalRewards&(1<<index))!=0)return;
            if(game.Profile.festivalTokens<3){game.Notify("Earn 3 festival tokens to buy this decoration");return;}
            game.Profile.festivalTokens-=3;game.Profile.festivalRewards|=1<<index;game.Save.Save();game.Notify(RewardName(index)+" placed inside Ammy’s house");
        }
        void Update()
        {
            if(!game || !game.Player || game.Save==null)return;
            if(decorated!=game.Profile.festivalRewards)
            {
                decorated=game.Profile.festivalRewards;if(rewards)Destroy(rewards);rewards=new GameObject("Earned original festival home decorations");rewards.transform.SetParent(transform,false);rewards.transform.position=VillageInteriors.HomeCentre;
                for(int i=0;i<3;i++)if((decorated&(1<<i))!=0)
                    VillageFestival.Place(rewards.transform,RewardResources[i],new Vector3(-4+i*1.8f,0,3),new Vector3(.6f,.7f,.5f),Vector3.zero);
            }
            if(!Active)return;
            if(!game.Profile.night || game.InTrial || game.Health<=0){Clear();return;}
            if(game.Blocked || game.CinematicActive)return;
            remaining-=Time.deltaTime;if(remaining<=0){Clear();game.Notify("Time’s up · try another festival challenge at the board");return;}
            if(mode==1 && Vector3.Distance(game.Player.transform.position,Ground(Route[checkpoint]))<1.35f)
            {
                checkpoints[checkpoint].SetActive(false);checkpoint++;
                if(checkpoint==Route.Length)Win();else checkpoints[checkpoint].SetActive(true);
            }
        }
        void OnDestroy(){Clear();if(rewards)Destroy(rewards);}
    }
}
