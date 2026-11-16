from pathlib import Path
import xml.etree.ElementTree as ET,subprocess,os
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/village-adventures')
x=ET.parse(W/'FullCompile.csproj');g=x.getroot().find('ItemGroup')
for p in [R/'tools/village-adventures/UIContract.cs',R/'Sunward-Unity/Assets/Sunward/Scripts/ScrollUI.Adventures.cs']:g.append(ET.Element('Compile',Include=str(p)))
x.write(W/'UICompile.csproj');subprocess.run(['/workspace/work/tundra-beads/dotnet/dotnet','build',str(W/'UICompile.csproj'),'--nologo'],env=dict(os.environ,DOTNET_CLI_HOME='/workspace/work/tundra-beads/dotnet-home'),check=True)
