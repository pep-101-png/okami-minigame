$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$legacyCalls = @(Get-ChildItem (Join-Path $repo 'Sunward-Unity/Assets') -Recurse -Filter '*.cs' | Select-String -Pattern '\bGetInstanceID\s*\(')
if ($legacyCalls.Count) { throw "Unity 6000.6 compilation blocker: $($legacyCalls -join '; ')" }
Add-Type -Path (Join-Path $repo 'Sunward-Unity/Assets/Sunward/Scripts/ResidentStepClock.cs')
Add-Type -Path (Join-Path $repo 'Sunward-Unity/Assets/Sunward/Scripts/ShieldPresentationRules.cs')
foreach ($fps in @(30,60,144)) {
    $clock = New-Object Sunward.ResidentStepClock
    $steps = 0
    for ($frame=0; $frame -lt $fps*60; $frame++) {
        if ($clock.Advance(0.7/$fps,1.0/$fps,$true)) { $steps++ }
    }
    if ($steps -lt 125 -or $steps -gt 132) { throw "Bad real-step count at ${fps}fps: $steps" }
    for ($frame=0; $frame -lt $fps*20; $frame++) {
        if ($clock.Advance(0,1.0/$fps,$false)) { throw 'A stationary resident produced a step' }
        if ($clock.Advance(0.00001,1.0/$fps,$true)) { throw 'IK jitter produced a step' }
    }
    if ($clock.Advance(4,1.0/$fps,$true)) { throw 'Teleport produced a step' }
}
$budget = New-Object Sunward.ResidentSoundBudget
$clocks = @(1..20 | ForEach-Object { New-Object Sunward.ResidentStepClock })
$heard = 0
for ($frame=0; $frame -lt 3600; $frame++) {
    foreach ($clock in $clocks) {
        if ($clock.Advance(0.7/60,1.0/60,$true) -and $budget.Allow($frame/60.0)) { $heard++ }
    }
}
if ($heard -lt 100 -or $heard -gt 300) { throw "Village-wide sound budget failed: $heard" }
$budget.Reset()
if (-not $budget.Allow(0)) { throw 'Sound budget failed to reset for a new play session' }
if ([Sunward.ShieldPresentationRules]::TiltDegrees -ne 90) { throw 'Shield face is not horizontal and upward' }
foreach ($trial in @($false,$true)) {
    if ([Sunward.ShieldPresentationRules]::Visible($trial,$false,$false,$false) -ne $trial) { throw 'Arena-only weapon visibility changed' }
}
Write-Output 'PASS: 60-second step simulations at 30/60/144 FPS; stationary, jitter, teleport suppression; flat up-facing shield; arena-only policy. Not Unity runtime validation.'
