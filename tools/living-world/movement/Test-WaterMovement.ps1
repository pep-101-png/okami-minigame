# Pure policy tests; compatible with Windows PowerShell 5.1 as well as PS7.
$ErrorActionPreference = 'Stop'
$repo = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
Add-Type -Path (Join-Path $repo 'Sunward-Unity/Assets/Sunward/Scripts/SwimmingRules.cs')
function Assert($condition, $name) { if (-not $condition) { throw $name } }
Assert ([Sunward.SwimmingRules]::ShouldSwim($false, 1.2, -.4, -4, $false)) 'Entering deep water must start swimming'
Assert (-not [Sunward.SwimmingRules]::ShouldSwim($false, .15, -.4, -1, $false)) 'Shallow water must remain wading'
Assert ([Sunward.SwimmingRules]::ShouldSwim($true, .35, -.75, .5, $false)) 'Depth hysteresis prevents edge flicker'
Assert ([Sunward.SwimmingRules]::ShouldSwim($true, 1.2, -.9, 2.8, $false)) 'Upward buoyancy must not cancel swimming'
Assert (-not [Sunward.SwimmingRules]::ShouldSwim($true, .2, -.55, 0, $false)) 'Leaving the deep channel must exit swimming'
Assert (-not [Sunward.SwimmingRules]::ShouldSwim($false, 1.2, .5, -3, $true)) 'Bridge deck must not become swimmable'
Assert ([Sunward.SwimmingRules]::ShouldSwim($false, 1.2, -.8, 0, $false)) 'Water below bridge must remain swimmable'
Assert (-not [Sunward.SwimmingRules]::ShouldSwim($false, 1.2, -.6, 7.2, $false)) 'Jumping from water must not instantly re-enter swimming'
Assert ([Sunward.SwimmingRules]::CanJump(.1, $false, $false)) 'Ground jump available'
Assert ([Sunward.SwimmingRules]::CanJump(0, $true, $true)) 'A swimming jump is a first jump'
Assert ([Sunward.SwimmingRules]::CanJump(0, $false, $false)) 'Double jump available without an upgrade'
Assert (-not [Sunward.SwimmingRules]::CanJump(0, $false, $true)) 'Third jump must be rejected'
Assert ([Sunward.SwimmingRules]::FloatRoot -lt [Sunward.SwimmingRules]::WaterLevel) 'Paws need to paddle below the water'
# Integrate the actual buoyancy policy for three minutes at multiple frame rates.
foreach ($fps in @(30, 60, 144)) {
    [single]$y = -.4; [single]$velocity = -6
    for ($i = 0; $i -lt $fps * 180; $i++) {
        $velocity = [Sunward.SwimmingRules]::BuoyancyVelocity($y, $velocity, (1.0 / $fps))
        $y += $velocity / $fps
        Assert (($y -gt -3) -and ($y -lt .04)) 'Swimmer must not fall away or pop above the river'
    }
    Assert ([Math]::Abs($y - [Sunward.SwimmingRules]::FloatRoot) -lt .001) 'Buoyancy should settle at the swim line'
}
Assert ([Sunward.SwimmingRules]::BuoyancyVelocity(-1, 0, 0) -eq 0) 'Zero elapsed time must not accelerate'
Write-Host 'PASS: 13 swimming/double-jump policy cases and three-minute buoyancy at 30/60/144 FPS. Unity physics and animation appearance NOT verified.'
