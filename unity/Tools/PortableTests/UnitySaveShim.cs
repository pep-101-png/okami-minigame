// Test-only adapters, outside Assets. These are never compiled into the Unity game.
using System;using System.IO;using System.Text.Json;
namespace UnityEngine {
 public static class Application {public static string persistentDataPath=Path.Combine(Path.GetTempPath(),"Sunward-PortableTests-"+Guid.NewGuid());}
 public static class Debug {public static void LogWarning(string s)=>Console.WriteLine("TEST WARNING: "+s);}
 public static class JsonUtility {static readonly JsonSerializerOptions Options=new JsonSerializerOptions{IncludeFields=true,WriteIndented=true};public static T FromJson<T>(string s)=>JsonSerializer.Deserialize<T>(s,Options);public static string ToJson(object o,bool pretty)=>JsonSerializer.Serialize(o,Options);}
}
