from pathlib import Path
import argparse,xml.etree.ElementTree as ET,subprocess,os,tempfile
p=argparse.ArgumentParser();p.add_argument('--dotnet',required=True);p.add_argument('--doubles',type=Path,required=True);a=p.parse_args();R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/village-complete/save-tests');W.mkdir(exist_ok=True)
s=a.doubles.read_text();start=s.index('public class SaveStore{');i=s.index('{',start)+1;level=1
while level:
 if s[i]=='{':level+=1
 elif s[i]=='}':level-=1
 i+=1
s=s[:start]+s[i:];s=s.replace('public static class JsonUtility{','public static class JsonUtility{public static string ToJson(object data,bool pretty=false)=>System.Text.Json.JsonSerializer.Serialize(data,new System.Text.Json.JsonSerializerOptions{IncludeFields=true,WriteIndented=pretty});')
s=s.replace('public static class Debug{','public static class Debug{public static void LogWarning(object message){}')
s+='\nnamespace UnityEngine{public static class Application{public static string persistentDataPath=>System.IO.Path.GetTempPath();}}'
(W/'Doubles.cs').write_text(s);project=ET.parse(R/'tools/spirit-charge-home/compile/Compile.csproj');root=project.getroot()
for group in root.findall('ItemGroup'):
 for item in list(group):
  path=item.get('Include','')
  if path.endswith('Tests.cs') or 'SemanticDoubles' in path:group.remove(item);continue
  path=path.replace('$(NativeBodySource)',str(R/'Sunward-Unity/Assets/OkamiRemaster/Player/NativeAmaterasu.cs')).replace('$(OrbitSource)',str(R/'Sunward-Unity/Assets/Sunward/Scripts/OrbitCamera.cs')).replace('$(StreetSource)',str(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/VillageStreetPlay.cs')).replace('$(WaterSource)',str(R/'Sunward-Unity/Assets/Sunward/Scripts/WaterContact.cs'))
  if not path.startswith('/'):path=str((R/'tools/spirit-charge-home/compile'/path).resolve())
  item.set('Include',path)
group=root.find('ItemGroup')
for path in [W/'Doubles.cs',R/'Sunward-Unity/Assets/Sunward/Scripts/SaveStore.cs',R/'tools/village-complete/SaveTests.cs']:ET.SubElement(group,'Compile',Include=str(path))
project.write(W/'Saves.csproj');result=subprocess.run([a.dotnet,'run','--project',str(W/'Saves.csproj'),'--',str(R/'Sunward-Unity/Assets')],capture_output=True,text=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'));print(result.stdout);print(result.stderr);result.check_returncode()
