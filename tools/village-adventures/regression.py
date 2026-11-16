"""Run the previous guardian integration scenarios against this update's sources."""
from pathlib import Path
import xml.etree.ElementTree as ET,subprocess,os
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/village-adventures');x=ET.parse(W/'Runtime.csproj');g=x.getroot().find('ItemGroup')
for e in list(g):
 if Path(e.get('Include')).name in ['AdventureTests.cs','ActivityDriverTests.cs']:g.remove(e)
g.append(ET.Element('Compile',Include=str(R/'tools/celestial-guardians/GuardianTests.cs')));x.write(W/'GuardianRegression.csproj');out=W/'guardian-regression';out.mkdir(exist_ok=True);env=dict(os.environ,DOTNET_CLI_HOME='/workspace/work/tundra-beads/dotnet-home');exe='/workspace/work/tundra-beads/dotnet/dotnet';subprocess.run([exe,'build',str(W/'GuardianRegression.csproj'),'--nologo'],env=env,check=True);subprocess.run([exe,str(W/'bin/Debug/net8.0/GuardianRegression.dll'),str(R/'Sunward-Unity/Assets'),str(out)],env=env,check=True)
