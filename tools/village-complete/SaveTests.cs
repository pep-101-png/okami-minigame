using System;
using System.IO;
using Sunward;
class SaveTests
{
    static int count;static void Check(bool b,string s){count++;if(!b)throw new Exception(s);}
    static void Main(string[] args)
    {
        UnityEngine.Resources.Root=args[0];string folder=System.IO.Path.Combine(System.IO.Path.GetTempPath(),"Sunward-slot-test-"+Guid.NewGuid());Directory.CreateDirectory(folder);Environment.SetEnvironmentVariable("SUNWARD_AUTOMATION_READONLY","1");Environment.SetEnvironmentVariable("SUNWARD_AUTOMATION_DATA",folder);
        try
        {
            var store=new SaveStore();store.Data.coins=7;Check(store.Save(),"Initial legacy save failed");Check(store.ReadSlot(0).coins==7,"Existing single save not available in first slot");
            for(int i=0;i<4;i++){store.Data.coins=10+i*10;store.Data.bedBlessingUntil=12345;store.Data.dayElapsed=456;store.Data.night=true;Check(store.SaveSlot(i),"Slot save failed");}
            store.Data.coins=999;Check(store.Save(),"Autosave failed");for(int i=0;i<4;i++)Check(store.ReadSlot(i).coins==10+i*10,"Autosave overwrote a manual slot");
            Check(store.LoadSlot(2)&&store.Data.coins==30&&store.Data.night&&store.Data.dayElapsed==456&&store.Data.bedBlessingUntil==12345,"Loading loses saved progress, clock or buff expiry");
            Check(File.Exists(store.Path+".backup"),"Primary backup missing after loading");
            store.Data.coins=51;Check(store.SaveSlot(1),"Slot overwrite failed");Check(File.Exists(store.Path+".slot2.json.backup"),"Overwritten slot has no backup");File.WriteAllText(store.Path+".slot2.json","broken");Check(store.ReadSlot(1).coins==20,"Corrupt slot cannot recover its own valid backup");Check(store.LoadSlot(1)&&store.Data.coins==20,"Recovered slot cannot be loaded");
            File.WriteAllText(store.Path+".slot4.json","broken");int kept=store.Data.coins;Check(!store.LoadSlot(3)&&store.Data.coins==kept,"Damaged slot discards active progress");Check(!store.SaveSlot(-1)&&!store.SaveSlot(4),"Invalid slot accepted");
            string legacy=System.IO.Path.Combine(folder,"legacy");Directory.CreateDirectory(legacy);Environment.SetEnvironmentVariable("SUNWARD_AUTOMATION_DATA",legacy);File.WriteAllText(System.IO.Path.Combine(legacy,"Sunward-Unity-v1.json"),"{\"version\":2,\"revision\":4,\"coins\":75,\"xp\":200,\"equipped\":\"spear\",\"owned\":[\"spear\"],\"upgrades\":{},\"milestones\":{}}");var old=new SaveStore();Check(old.Data.coins==75&&old.Data.revision==4&&old.Data.dayElapsed==0&&old.Data.bedBlessingUntil==0,"Older save schema no longer loads");
            Console.WriteLine("PASS "+count+" real SaveStore file/slot/backup/corruption/legacy-profile checks in an isolated temporary directory; JsonUtility uses a .NET test adapter, not Unity");
        }
        finally{Directory.Delete(folder,true);}
    }
}
