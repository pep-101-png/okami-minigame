$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Add-Type -Path (Join-Path $repo 'Sunward-Unity/Assets/Sunward/Scripts/ShieldPresentationRules.cs')
Add-Type -Path (Join-Path $repo 'Sunward-Unity/Assets/Sunward/Scripts/SwimmingRules.cs')
foreach ($trial in @($false,$true)) {
    foreach ($rest in @($false,$true)) {
        foreach ($locked in @($false,$true)) {
            foreach ($result in @($false,$true)) {
                $expected = $trial -and -not $rest -and -not $locked -and -not $result
                if ([Sunward.ShieldPresentationRules]::Visible($trial,$rest,$locked,$result) -ne $expected) {
                    throw 'Weapon visibility violates arena/rest/lock/result policy'
                }
            }
        }
    }
}
if ([Sunward.SwimmingRules]::FloatRoot -ge -.9) { throw 'Swim immersion was not lowered' }
# Conservative any-orientation bound: mesh radius plus flame depth and chest dip.
$lowest = [Sunward.ShieldPresentationRules]::MountHeight - [Sunward.ShieldPresentationRules]::ChestMotionLimit - .80 - .18
if ($lowest -le .30) { throw 'Shield can touch the ground under bounded chest motion' }
Write-Output 'PASS: 16 weapon visibility combinations, deeper swim root and conservative shield ground clearance. Not Unity rendering.'
