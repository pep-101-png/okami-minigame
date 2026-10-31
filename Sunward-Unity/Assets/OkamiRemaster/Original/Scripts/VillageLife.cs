using System.Collections;
using UnityEngine;
namespace Sunward.Remaster
{
    public sealed class VillageLife : MonoBehaviour
    {
        public GameFlow game;
        public Transform[] restorationBeds;
        public Vector3 weaponsShop=new Vector3(-6,0,-27.5f),upgradeShop=new Vector3(5,0,-27.5f);
        FarmCrop[] crops;
        FarmCrop carried;
        GameObject carriedVisual;
        bool digging;
        int appliedStage=-1;
        void Start(){
            foreach(var obj in game.npcObjects)
            {
                if(!obj)continue;var resident=obj.GetComponent<VillageResident>();if(!resident || resident.stallkeeper || obj.GetComponent<NativeDailyRoutine>())continue;
                var routine=obj.AddComponent<NativeDailyRoutine>();routine.game=game;routine.seed=resident.index;routine.workplace=obj.transform.position;
            }
            crops=FindObjectsByType<FarmCrop>(FindObjectsSortMode.None);if(!game.Player.GetComponent<SpectralTendrils>())game.Player.gameObject.AddComponent<SpectralTendrils>();}
        public int Bloom(Vector3 point)
        {
            int n=0;foreach(var crop in crops)if(Vector3.Distance(crop.transform.position,point)<5 && crop.Bloom())n++;
            if(n>0){game.Profile.praise+=n;game.Save.Save();}return n;
        }
        void Update()
        {
            if(!game || !game.Player)return;
            if(appliedStage!=game.Profile.restorationStage)
            {appliedStage=game.Profile.restorationStage;for(int i=0;restorationBeds!=null && i<restorationBeds.Length;i++)if(restorationBeds[i])restorationBeds[i].gameObject.SetActive(i<appliedStage);}
            if(game.Health<=0 || game.Panel!="" || game.InTrial){if(carried && game.Health<=0)Drop();return;}
            if(game.Blocked || game.Player.Locked || game.Player.Swimming || digging)return;
            Vector3 p=game.Player.transform.position;float farmer=Vector3.Distance(p,VillageServices.Farmer);
            if(carried && !carriedVisual)CreateCarry();
            if(game.Player.input.Eat.WasPressedThisFrame())Eat();
            if(game.Player.input.Carry.WasPressedThisFrame())
            {
                if(carried)Drop();
                else if(game.Profile.vegetables>0)game.Notify("H · eat produce · E at farmer to sell / shop");
            }
            FarmCrop nearest=null;float best=1.8f;
            if(!carried)foreach(var crop in crops)if(!crop.Harvested){float d=Vector3.Distance(crop.transform.position,p);if(d<best){best=d;nearest=crop;}}
            if(nearest)
            {game.WorldPrompt("F · dig up vegetable · carry it to farmer or H to eat");if(game.Player.input.Dig.WasPressedThisFrame())StartCoroutine(Dig(nearest));}
            else if(carried)game.WorldPrompt(farmer<3?"E · farmer shop / sell carried vegetable":"Carrying produce · H eat (+1 health) · G stow in pouch");
            else if(Vector3.Distance(p,new Vector3(GardenPond.X+3.7f,.02f,GardenPond.Z))<2)
            {game.WorldPrompt("E · Rest beside the steaming pond");if(game.Player.input.Interact.WasPressedThisFrame())game.Services.RestAt(new Vector3(GardenPond.X+3.7f,.04f,GardenPond.Z),270);}
        }
        IEnumerator Dig(FarmCrop crop)
        {
            if(!game.Player.Grounded)yield break;
            Vector3 direction=crop.transform.position-game.Player.transform.position;direction.y=0;if(direction.sqrMagnitude>.01f)game.Player.transform.rotation=Quaternion.LookRotation(direction);
            digging=true;game.Player.Locked=true;game.Combat.Cancel();game.Player.animationView.Play("Dig",.15f,1.25f,true);
            yield return new WaitForSeconds(.65f);
            if(game.Health>0 && crop && !crop.Harvested)
            {crop.Harvest();carried=crop;game.Profile.vegetables++;game.Save.Save();CreateCarry();game.Audio.Cue("land");CelestialBrush.Burst("Leaf",crop.transform.position,8,.25f);}
            yield return new WaitForSeconds(.6f);game.Player.Locked=false;digging=false;game.Player.animationView.Play("Idle_Natural",.15f,0,true);
        }
        void CreateCarry()
        {
            if(!carried || carriedVisual)return;
            var body=game.Player.GetComponent<NativeAmaterasu>();if(!body || !body.Ready)return;
            carriedVisual=new GameObject("Original vegetable carried in mouth");carriedVisual.transform.SetParent(body.Head,false);carriedVisual.transform.localPosition=new Vector3(0,-.08f,.35f);
            if(!string.IsNullOrEmpty(carried.resource))carriedVisual.AddComponent<OriginalVisual>().Load(carried.resource,carried.carryOffset,Vector3.one*carried.carryScale);
        }
        void Drop(){if(carriedVisual)Destroy(carriedVisual);carriedVisual=null;carried=null;game.Notify("Produce stored in your pouch · H to eat or sell to farmer");}
        public void Eat()
        {
            if(game.Profile.vegetables<=0){game.Notify("Dig up vegetables at the farm first");return;}
            if(game.Health>=game.MaxHealth){game.Notify("Health is full · save the produce for later");return;}
            game.Player.animationView.Play("Eat",.12f,.8f,true);game.Profile.vegetables--;game.Health=Mathf.Min(game.MaxHealth,game.Health+1);Drop();game.Save.Save();game.Audio.Cue("collect");game.Notify("Vegetable eaten · +1 health");
        }
        public void Sell()
        {
            if(game.Profile.vegetables<=0){game.Notify("Bring harvested produce to sell");return;}
            int n=game.Profile.vegetables;game.Profile.coins+=n*5;game.Profile.cropsSold+=n;game.Profile.vegetables=0;Drop();game.Save.Save();game.Notify("Sold "+n+" vegetables · +"+(n*5)+" coins");
        }
        public void BuyMeal()
        {if(game.Profile.coins<5){game.Notify("A farm meal costs 5 coins");return;}if(game.Health>=game.MaxHealth){game.Notify("Health is already full");return;}game.Profile.coins-=5;game.Health=Mathf.Min(game.MaxHealth,game.Health+10);game.Save.Save();game.Notify("Fresh farm meal · +10 health");}
        public void BuyVitality()
        {int cost=25+game.Profile.farmVitality*10;if(game.Profile.farmVitality>=10 || game.Profile.coins<cost){game.Notify("Farm vitality complete or not enough coins");return;}game.Profile.coins-=cost;game.Profile.farmVitality++;game.Health=Mathf.Min(game.MaxHealth,game.Health+1);game.Save.Save();game.Notify("Farmer’s blessing · permanent maximum health +1");}
        public void Request()
        {
            int stage=game.Profile.restorationStage;
            if(stage>=3){game.Notify("Village restoration requests complete · thank you, Amaterasu");return;}
            bool ready=stage==0?game.Profile.vegetables>=3:stage==1?game.Profile.kills>=10:game.Profile.bossWins>=1;
            if(!ready){game.Notify(stage==0?"Village request: deliver 3 vegetables":stage==1?"Village request: defeat 10 arena enemies":"Village request: defeat Crimson Helm below the arena");return;}
            if(stage==0){game.Profile.vegetables-=3;Drop();}
            game.Profile.restorationStage++;game.Profile.praise+=25;game.Profile.coins+=30;game.Save.Save();game.Notify("Request complete · +25 Praise, +30 coins · village flowers restored");
        }
        void OnDestroy(){if(carriedVisual)Destroy(carriedVisual);}
    }
}
