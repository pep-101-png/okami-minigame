"""Run offline regression tests. These do not compile or play the Unity game."""
import argparse, os, subprocess, tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--dotnet',default='dotnet');args=p.parse_args()
root=Path(__file__).resolve().parents[2]
path='Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/OriginalWeaponCatalog.cs'
baseline=subprocess.check_output(['git','show','4dd2e730df2bc3fed3bf7d7998c81bca395c6fbe:'+path],cwd=root).decode().replace('class OriginalWeaponCatalog','class OriginalWeaponCatalogBaseline')
with tempfile.TemporaryDirectory(prefix='tundra-tests-') as tmp:
    catalog=Path(tmp)/'BaselineCatalog.cs';catalog.write_text(baseline)
    subprocess.run([args.dotnet,'run','--project',str(root/'tools/tundra-beads/tests/Tests.csproj'),'-p:BaselineCatalog='+str(catalog),'--',str(root/'Sunward-Unity/Assets')],cwd=root,check=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'))
