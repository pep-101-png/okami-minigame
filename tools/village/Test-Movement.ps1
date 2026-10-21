# Works in Windows PowerShell 5.1 and PowerShell 7; no Unity/Pester requirement.
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Add-Type -Path (Join-Path $repo 'Sunward-Unity/Assets/Sunward/Scripts/LocomotionTuning.cs')
function Assert-Equal($actual, $expected) {
    if ($actual -ne $expected) { throw "Expected $expected, received $actual" }
}
Assert-Equal ([Sunward.LocomotionTuning]::Gait(0, 0, 'Idle_Natural')) 'Idle_Natural'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(1.1, 0, 'Idle_Natural')) 'Walk_Natural'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(3.6, 0, 'Walk_Natural')) 'Jog_Natural'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(7.2, 0, 'Jog_Natural')) 'Sprint_Fluid'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(5.3, 0, 'Sprint_Fluid')) 'Sprint_Fluid'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(5.3, 0, 'Jog_Natural')) 'Jog_Natural'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(1.5, 0, 'Walk_Natural')) 'Walk_Natural'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(1.5, 0, 'Jog_Natural')) 'Jog_Natural'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(3.6, 0.8, 'Jog_Natural')) 'Jog_Natural'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(3.6, -1.3, 'Jog_Natural')) 'Jog_Turn_L'
Assert-Equal ([Sunward.LocomotionTuning]::Gait(0.05, 0, 'Walk_Natural')) 'Idle_Natural'
if ([Sunward.LocomotionTuning]::WalkSpeed -le 0.57 -or [Sunward.LocomotionTuning]::JogSpeed -le 2.45 -or [Sunward.LocomotionTuning]::SprintSpeed -le 5.3) { throw 'Requested movement gains missing' }
Write-Host 'PASS: movement gains, gait selection, steering and boundary hysteresis. Motion appearance NOT verified.'
