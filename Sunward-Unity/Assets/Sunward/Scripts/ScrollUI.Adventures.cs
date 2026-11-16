using UnityEngine;
namespace Sunward
{
    public sealed partial class ScrollUI
    {
        int masteryWeapon;
        void AdventureHUD(float w,float h)
        {
            if(!game.Adventures)return;var mastery=game.Adventures.Mastery;var fishing=game.Adventures.Fishing;
            if(mastery && mastery.Active)
            {string text=mastery.Status+"\n"+mastery.Objective;float width=Mathf.Min(620,w*.55f);float height=Sunward.Remaster.InkText.MeasureHeight(text,width-48,25)+30;DrawPaper(new Rect((w-width)*.5f,85,width,height));Sunward.Remaster.InkText.Draw(text,new Rect((w-width)*.5f+24,99,width-48,height-20),25,new Color(.1f,.06f,.03f,1));}
            if(fishing && fishing.Active)
            {float width=Mathf.Min(650,w-60);float height=Sunward.Remaster.InkText.MeasureHeight(fishing.Status,width-48,27)+42;DrawPaper(new Rect((w-width)*.5f,h-height-35,width,height));Sunward.Remaster.InkText.Draw(fishing.Status,new Rect((w-width)*.5f+24,h-height-20,width-48,height-15),27,new Color(.1f,.06f,.03f,1));if(fishing.Hooked && hintInk){var old=GUI.color;GUI.color=Color.Lerp(new Color(.3f,.65f,.45f),new Color(.9f,.15f,.07f),fishing.Tension);GUI.DrawTexture(new Rect((w-width)*.5f+24,h-49,(width-48)*fishing.Tension,10),hintInk);GUI.color=old;}}
        }
        void AdventureJournal()
        {
            Label("Windflower · village journal",title);
            Label("Weapon mastery",body);Label("Read the scroll on the dojo's eastern side. Owned weapons have an introductory lesson; awakened weapons open two further mastery stages. First completions award coins and XP.",small);
            Label("The living pond",body);Label("Visit the north bank of the pond near Ammy's house. The angler teaches brush-assisted fishing. Feed one vegetable to attract koi and rare night visitors.",small);
            Label("Village projects",body);Label("The noticeboard accepts coins, produce and fish for four permanent improvements. Praise records your help and is not spent.",small);
            Label("The moonlit trail",body);Label(Sunward.Remaster.VillageAdventureRules.VillageHint(game.Profile),small);
            if(game.Profile.adventures.moonCharm)Label("Moon charm · peaceful Ink recovery +3 per second",small);
            if(Button("WEAPON LESSONS · view progress",button))game.SetPanel("mastery");
            if(Button("POND COLLECTION",button))game.SetPanel("fishing");
            if(Button("RESTORATION PROJECTS",button))game.SetPanel("projects");
        }
        void MasteryMenu()
        {
            Label("Dojo · instrument mastery",title);var all=Sunward.Remaster.OriginalWeaponCatalog.All;masteryWeapon=Mathf.Clamp(masteryWeapon,0,all.Length-1);var entry=Sunward.Remaster.OriginalWeaponCatalog.Display(game.Profile,all[masteryWeapon]);
            Label(entry.title,body);Label(Sunward.Remaster.AwakeningProgress.Ability(entry.resource),small);Label("Completed stages: "+game.Profile.adventures.mastery[masteryWeapon]+" / 3",small);
            for(int tier=1;tier<=3;tier++)
            {
                string name=tier==1?"LEARN · hits, charges & brush":tier==2?"APPLY · use the awakened ability":"MASTER · ability, brush & careful dodges";
                bool done=game.Profile.adventures.mastery[masteryWeapon]>=tier;
                if(Button(name+(done?" · completed":" · first reward "+(tier==1?150:tier==2?300:600)+" coins"),button))
                {
                    if(!Sunward.Remaster.VillageServices.InDojo(game.Player.transform.position))game.Notify("Visit the weapon scroll inside the dojo to start");
                    else if(!game.Adventures.Mastery.Begin(masteryWeapon,tier))game.Notify("Own this instrument, complete the previous stage, and awaken it for Apply / Master");
                }
            }
            Label("Learn advances the existing awakening objectives. Apply and Master require the awakened weapon. Replays award no repeat coins or XP. Master allows at most five damage contacts. U is reserved for real arena battles.",small);
            if(Button("PREVIOUS WEAPON",button))masteryWeapon=(masteryWeapon+all.Length-1)%all.Length;
            if(Button("NEXT WEAPON",button))masteryWeapon=(masteryWeapon+1)%all.Length;
        }
        void FishingMenu()
        {
            Label("The village pond",title);var fishing=game.Adventures.Fishing;
            if(Button("SPEAK WITH THE ANGLER",button)){if(fishing.Near)fishing.Teach();else game.Notify("The angler waits by the pond's north bank");}
            if(Button("SIT AT THE BANK · begin fishing",button)){if(!fishing.Begin())game.Notify("Stand by the north bank of the pond to begin");}
            if(Button("FEED THE POND · 1 vegetable",button)){if(!fishing.Feed())game.Notify("Visit the north bank with a vegetable in your pouch");}
            Label(fishing.Fed?"Food is drawing fish closer.":"Food attracts koi. Night and restoration bring rarer visitors.",small);
            for(int i=0;i<6;i++)
            {
                int total=game.Profile.adventures.caught[i],kept=game.Profile.adventures.fish[i];Label(Sunward.Remaster.VillageAdventureRules.FishNames[i]+" · caught "+total+" · pouch "+kept,body);Label(Sunward.Remaster.VillageAdventureRules.FishHint(i),small);
                if(kept>0 && Button("SELL POUCH · "+(kept*Sunward.Remaster.VillageAdventureRules.FishValue[i])+" coins",button))
                {if(!fishing.Near)game.Notify("Return to the angler to sell your catch");else{Sunward.Remaster.VillageAdventureRules.SellFish(game.Profile,i);game.Save.Save();game.Audio.Cue("collect");}}
            }
            Label("Selling or donating fish keeps your lifetime collection record.",small);
        }
        void ProjectMenu()
        {
            Label("Village restoration",title);Label(game.Profile.coins+" coins · "+game.Profile.vegetables+" produce · "+Sunward.Remaster.VillageAdventureRules.FishInPouch(game.Profile)+" fish in pouch",small);
            for(int i=0;i<4;i++)
            {
                Label(Sunward.Remaster.VillageAdventureRules.ProjectNames[i],body);
                string desc=i==0?"A planted riverside tea gathering, furnished table and visiting pilgrims.":i==1?"An open pig-yard shelter, bedding, feeding bowl and farm lantern.":i==2?"Flowers and stone lanterns along the first bridge's river walk.":"A pond-side resting area; rare green char visit after dark.";Label(desc,small);
                if(Sunward.Remaster.VillageAdventureRules.Project(game.Profile,i)){Label("RESTORED · +25 Praise recorded",small);continue;}
                Label(Sunward.Remaster.VillageAdventureRules.ProjectCoins[i]+" coins · "+Sunward.Remaster.VillageAdventureRules.ProjectProduce[i]+" produce · "+Sunward.Remaster.VillageAdventureRules.ProjectFish[i]+" fish",small);
                if(Button("CONTRIBUTE & RESTORE",button))if(!game.Adventures.Projects.Build(i))game.Notify("Contribute at the noticeboard with the listed supplies");
            }
        }
    }
}
