"""Semantic check of the actual GameFlow integration as well as guardian scripts."""
exec(open(__file__.replace('full_compile.py','runtime.py')).read().split("(W/'RuntimeDoubles.cs').write_text(s)")[0])
while 'public sealed partial class GameFlow' in s:s=remove(s,'public sealed partial class GameFlow')
s=s.replace('public class SaveStore{','public class SaveStore{public ProfileData Data=new ProfileData();')
s=s.replace('public static class Cursor{','public enum CursorLockMode{None}public static class Cursor{public static CursorLockMode lockState;')
s=s.replace('public static class Application{','public static class Application{public static int targetFrameRate;')
s=s.replace('public class WolfInput{','public class WolfInput{public UnityEngine.InputSystem.InputAction Journal=new UnityEngine.InputSystem.InputAction();')
s=s.replace('public void Recover(Vector3 p)', 'public float Invulnerable;public void Push(Vector3 p){}public void Recover(Vector3 p)')
s=s.replace('public class VisualFx{','public class VisualFx:UnityEngine.MonoBehaviour{public void Impact(UnityEngine.Vector3 p,UnityEngine.Color c){}public void AttachProjectile(UnityEngine.GameObject o){}')
s=s.replace('public class Valley:UnityEngine.Object','public class Valley:UnityEngine.MonoBehaviour')
s+='\nnamespace UnityEngine{public static class Application{public static int targetFrameRate;}public static class QualitySettings{public static int vSyncCount;}}\nnamespace Sunward{public class PaintedEffects:VisualFx{}public class NpcData{public string name;public string[] lines;}}'
s=s.replace('public partial class VillageServices:Object{','public partial class VillageServices:Object{public static string Label(object p,object s)=>"";public void Interact(string s){}public static UnityEngine.Vector3 Mat=>UnityEngine.Vector3.zero;')
s=s.replace('public class InkProjectile:UnityEngine.MonoBehaviour{}','public class InkProjectile:UnityEngine.MonoBehaviour{public Sunward.GameFlow game;public UnityEngine.Vector3 direction;public float damage;}')
(W/'FullDoubles.cs').write_text(s)
x=ET.parse(W/'Runtime.csproj').getroot()
for group in x.findall('ItemGroup'):
 for el in list(group):
  path=el.get('Include','')
  if path.endswith('GuardianTests.cs') or path.endswith('RuntimeDoubles.cs'):group.remove(el)
 group.append(ET.Element('Compile',Include=str(W/'FullDoubles.cs')));group.append(ET.Element('Compile',Include=str(R/'Sunward-Unity/Assets/Sunward/Scripts/GameFlow.cs')))
x.find('PropertyGroup/OutputType').text='Library';ET.ElementTree(x).write(W/'FullCompile.csproj')
subprocess.run([exe if 'exe' in globals() else '/workspace/work/tundra-beads/dotnet/dotnet','build',str(W/'FullCompile.csproj'),'--nologo'],env=dict(os.environ,DOTNET_CLI_HOME='/workspace/work/tundra-beads/dotnet-home'),check=True)
