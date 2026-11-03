"""Compile the actual trailer Escape condition against a property-only button API.
This is a focused CS1955 regression check, not Unity Editor compilation.
"""
from pathlib import Path
import argparse,subprocess,tempfile,re,os
p=argparse.ArgumentParser();p.add_argument('--dotnet',default='dotnet');args=p.parse_args();root=Path(__file__).resolve().parents[2]
source=(root/'Sunward-Unity/Assets/Sunward/Automation/TrailerPlayback.cs').read_text();condition=re.search(r'if\((Keyboard.current!=null && Keyboard.current.escapeKey[^)]*)(?:\))',source)[1]
assert condition=='Keyboard.current!=null && Keyboard.current.escapeKey.wasPressedThisFrame',condition
for f in (root/'Sunward-Unity/Assets').rglob('*.cs'):
 assert not re.search(r'\.wasPressedThisFrame\s*\(',f.read_text()),'Property called as a method: '+str(f)
with tempfile.TemporaryDirectory(prefix='sunward-button-api-',dir='/tmp') as d:
 d=Path(d);(d/'Check.csproj').write_text('<Project Sdk="Microsoft.NET.Sdk"><PropertyGroup><TargetFramework>net8.0</TargetFramework></PropertyGroup></Project>')
 template='public class ButtonControl{public bool wasPressedThisFrame=>true;}public class Keyboard{public static Keyboard current;public ButtonControl escapeKey=new ButtonControl();}public static class Probe{public static bool Escape()=>EXPR;}'
 for broken in [False,True]:
  expr=condition+('()' if broken else '');(d/'Probe.cs').write_text(template.replace('EXPR',expr));r=subprocess.run([args.dotnet,'build',str(d/'Check.csproj'),'--nologo'],capture_output=True,text=True,env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1'))
  assert (r.returncode!=0 and 'CS1955' in r.stdout) if broken else r.returncode==0,r.stdout+r.stderr
print('PASS actual Escape expression compiles as a property read; negative control reproduces CS1955; no other button-property calls found. Not Unity compilation.')
