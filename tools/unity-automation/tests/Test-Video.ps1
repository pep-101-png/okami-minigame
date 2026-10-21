#requires -Version 5.1
# Real encoder tests with synthetic frames; does not launch Unity or touch game assets.
$ErrorActionPreference='Stop'
$tools=Split-Path $PSScriptRoot -Parent
. (Join-Path $tools 'Common.ps1')
. (Join-Path $tools 'Video.ps1')
$AutomationState=Join-Path ([IO.Path]::GetTempPath()) ('sunward-video-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $AutomationState | Out-Null
function Assert([bool]$Condition,[string]$Message) { if (-not $Condition) { throw $Message } }
function Reject([scriptblock]$Action,[string]$Message) { $rejected=$false;try { & $Action | Out-Null } catch { $rejected=$true };Assert $rejected $Message }
try {
    $source=Join-Path $tools '../../Sunward-Unity/Assets/Sunward/Automation/VideoCapturePlan.cs'
    # Windows PowerShell 5.1 uses the legacy C# compiler. Enforce the same language
    # ceiling on modern PowerShell so its newer compiler cannot mask regressions.
    $compile=@{TypeDefinition=((Get-Content $source -Raw).Replace('#if UNITY_EDITOR','').Replace('#endif',''));ErrorAction='Stop'}
    if ((Get-Command Add-Type -CommandType Cmdlet).Parameters.ContainsKey('CompilerOptions')) {
        $compile.CompilerOptions=@('/langversion:5')
    }
    Add-Type @compile
    Write-Host 'PASS: shared video plan compiles with C# 5 compatible syntax.'
    $plan=[Sunward.Editor.Automation.VideoCapturePlan]::Build()
    Assert ($plan.Count -eq 14) '14 clip recipes'
    Assert (($plan.name -join ',') -ceq ((Get-ExpectedVideoNames) -join ',')) 'Unity and encoder recipe lists drifted'
    $gate=New-Object Sunward.Editor.Automation.VideoSceneLoadGate
    Assert (-not $gate.CanBind(10,$false,$true)) 'bound old player before load completed'
    Assert (-not $gate.CanBind(11,$true,$false)) 'bound wrong scene'
    Assert (-not $gate.CanBind(12,$true,$true)) 'bound before new scene Start settled'
    Assert ($gate.CanBind(13,$true,$true)) 'new scene did not become bindable'
    Assert (-not $gate.CanBind(14,$false,$true)) 'reload gate failed to reset'
    Assert (($plan | Measure-Object seconds -Sum).Sum -eq 70) '70 seconds / 2100 frames'
    foreach ($gait in @('walk','jog','sprint')) { foreach ($angle in @('side','front','rear-quarter')) { Assert (@($plan | Where-Object name -eq "$gait-$angle").Count -eq 1) 'gait/angle matrix' } }
    foreach ($clip in $plan) { for ($frame=0;$frame -lt $clip.seconds*30;$frame++) {
        $a=[Sunward.Editor.Automation.VideoCapturePlan]::Command($clip,$frame,30)
        $b=[Sunward.Editor.Automation.VideoCapturePlan]::Command($clip,$frame,30)
        Assert (($a | ConvertTo-Json -Compress) -ceq ($b | ConvertTo-Json -Compress)) 'repeatable inputs'
    } }
    $jump=$plan | Where-Object category -eq jump
    Assert ([Sunward.Editor.Automation.VideoCapturePlan]::Command($jump,30,30).jump) 'jump pulse'
    Assert (-not [Sunward.Editor.Automation.VideoCapturePlan]::Command($jump,32,30).jump) 'jump released'
    $settings=Get-VideoConfig ([pscustomobject]@{Video=[pscustomobject]@{KeepEncodedFrames=$true}})
    $frames=Join-Path $AutomationState 'frames';New-Item -ItemType Directory $frames | Out-Null
    $ffmpeg=Find-VideoTool '' 'ffmpeg';$probe=Find-VideoTool '' 'ffprobe'
    Assert ([bool]$ffmpeg -and [bool]$probe) 'Install ffmpeg and ffprobe to run encoder tests'
    $r=Invoke-AutomationProcess $ffmpeg @('-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=12','-frames:v','12','-threads','1','-start_number','0',(Join-Path $frames 'frame_%06d.png')) -Stage 'synthetic fixture'
    Assert ($r.ExitCode -eq 0) 'fixture creation'
    $clip=[pscustomobject]@{name='fixture';status='frames_captured_unreviewed';expectedFrames=12;frames=12;fps=12;width=320;height=180;framesDirectory='frames';telemetryFile='';recorderCandidate=''}
    @{status='frames_captured_unreviewed';clips=@($clip)} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $AutomationState 'video-capture.json')
    $result=Complete-GameplayVideos $AutomationState $settings @('fixture')
    Assert ($result.status -eq 'encoded_verified_unreviewed') 'real MP4 count/duration/resolution validation'
    Assert (Test-Path (Join-Path $AutomationState 'videos/fixture-contact.png')) 'contact sheet'
    $cached=[pscustomobject]@{fingerprint='fixture';runDirectory=$AutomationState;status='encoded_verified_unreviewed'}
    Assert (Test-VideoCache $cached 'fixture') 'reuse existing verified artifacts'
    Assert (-not (Test-VideoCache $cached 'changed')) 'changed source/settings recaptures'
    $clip.expectedFrames=13
    Reject { Test-EncodedVideo (Join-Path $AutomationState 'videos/fixture.mp4') $clip $probe } 'reject wrong video frame count'
    Reject { Get-FrameInfo $AutomationState $clip } 'reject incomplete capture'
    $clip.expectedFrames=12;$clip.width=322
    Reject { Get-FrameInfo $AutomationState $clip } 'reject wrong PNG dimensions'
    $clip.width=320
    Reject { Resolve-VideoPath $AutomationState '../escape' } 'reject escaped artifact'
    # Prefer a compatible Recorder candidate without re-encoding.
    Copy-Item (Join-Path $AutomationState 'videos/fixture.mp4') (Join-Path $AutomationState 'candidate.mp4')
    Remove-Item (Join-Path $AutomationState 'videos/fixture.mp4')
    $clip.recorderCandidate='candidate.mp4'
    @{status='frames_captured_unreviewed';clips=@($clip)} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $AutomationState 'video-capture.json')
    $result=Complete-GameplayVideos $AutomationState $settings @('fixture')
    Assert ($result.clips[0].encoder -eq 'unity_recorder') 'verified Recorder preference'
    Remove-Item (Join-Path $AutomationState 'videos/fixture.mp4')
    $clip.recorderCandidate=''
    @{status='frames_captured_unreviewed';clips=@($clip)} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $AutomationState 'video-capture.json')
    $settings.FFmpegPath=Join-Path $AutomationState 'missing-ffmpeg';$settings.FFprobePath=Join-Path $AutomationState 'missing-probe'
    $result=Complete-GameplayVideos $AutomationState $settings @('fixture')
    Assert ($result.clips[0].status -eq 'frames_only_missing_ffmpeg') 'explicit missing dependencies'
    Assert (@(Get-ChildItem $frames -Filter '*.png').Count -eq 12) 'preserve numbered frames'
    Assert (Test-Path (Join-Path $AutomationState 'videos/fixture-frames.zip')) 'bounded fallback frame archive'
    Set-Content (Join-Path $AutomationState 'videos/fixture-partial-test.mp4') 'partial'
    $payload=Join-Path $AutomationState 'payload';New-Item -ItemType Directory $payload | Out-Null
    Copy-VideoFeedback $AutomationState $payload $settings
    Assert (-not (Test-Path (Join-Path $payload 'videos/fixture-partial-test.mp4'))) 'never publish partial MP4'
    # Cleanup requires an ownership marker AND a verified MP4.
    $settings.FFmpegPath=$ffmpeg;$settings.FFprobePath=$probe;$settings.KeepEncodedFrames=$false
    $result=Complete-GameplayVideos $AutomationState $settings @('fixture')
    Assert (@(Get-ChildItem $frames -Filter '*.png').Count -eq 12) 'unmarked files must remain'
    Set-Content (Join-Path $frames '.sunward-owned-frames') 'fixture'
    $result=Complete-GameplayVideos $AutomationState $settings @('fixture')
    Assert ($result.clips[0].status -eq 'encoded_verified_unreviewed') 'recheck existing MP4'
    Assert (@(Get-ChildItem $frames -Filter '*.png').Count -eq 0) 'verified owned frames cleaned'
    # Regression fixture from the real failure: one zero-frame clip must retain
    # its Unity cause and explicitly report the other thirteen as not captured.
    $failure=Join-Path $AutomationState 'failed-campaign';New-Item -ItemType Directory $failure | Out-Null
    @{status='failed';error='Gameplay scene/player disappeared.';clips=@(@{name='walk-side';status='failed';error='Gameplay scene/player disappeared.';expectedFrames=120;frames=0;fps=30;width=960;height=540;framesDirectory='video-frames/walk-side'})} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $failure 'video-capture.json')
    $bad=Complete-GameplayVideos $failure $settings
    Assert ($bad.clips.Count -eq 14) 'aborted campaign hid other clips'
    Assert (($bad.clips[0].errors -join ' ') -match 'Gameplay scene/player disappeared') 'metadata error hid the Unity cause'
    Assert (@($bad.clips | Where-Object status -eq 'not_captured').Count -eq 13) 'unstarted thirteen clips were claimed captured'
    # Exercise encoding/probing of every actual recipe name with SYNTHETIC frames.
    $matrix=Join-Path $AutomationState 'matrix';$matrixFrames=Join-Path $matrix 'frames'
    New-Item -ItemType Directory $matrixFrames -Force | Out-Null
    $r=Invoke-AutomationProcess $ffmpeg @('-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=12','-frames:v','12','-threads','1','-start_number','0',(Join-Path $matrixFrames 'frame_%06d.png')) -Stage '14-clip synthetic fixture'
    Assert ($r.ExitCode -eq 0) 'matrix fixture generation'
    $clips=@(foreach ($name in Get-ExpectedVideoNames) { @{name=$name;status='frames_captured_unreviewed';error='';expectedFrames=12;frames=12;fps=12;width=320;height=180;framesDirectory='frames';telemetryFile='';recorderCandidate=''} })
    @{status='frames_captured_unreviewed';clips=$clips} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $matrix 'video-capture.json')
    $settings.KeepEncodedFrames=$true
    $all=Complete-GameplayVideos $matrix $settings
    Assert ($all.status -eq 'encoded_verified_unreviewed' -and $all.clips.Count -eq 14) 'not all fourteen recipe names encode/probe successfully'
    Assert (@(Get-ChildItem (Join-Path $matrix 'videos') -Filter '*.mp4').Count -eq 14) 'missing named matrix MP4'
    $clips=$clips | Select-Object -First 13
    @{status='frames_captured_unreviewed';clips=$clips} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $matrix 'video-capture.json')
    $missing=Complete-GameplayVideos $matrix $settings
    Assert ($missing.status -ne 'encoded_verified_unreviewed' -and $missing.clips.Count -eq 14) 'missing one recipe falsely passed campaign'
    # Partial frames can be inspected, but can never pass the complete campaign.
    $clips[0].expectedFrames=24
    @{status='failed';clips=@($clips[0])} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $matrix 'video-capture.json')
    $partial=Complete-GameplayVideos $matrix $settings @('walk-side')
    Assert ($partial.clips[0].status -eq 'partial_encoded_unreviewed' -and $partial.status -ne 'encoded_verified_unreviewed') 'partial recording masqueraded as complete'
    Write-Host 'PASS: deterministic 14-clip plan, real FFmpeg/ffprobe encoding, contact sheets, Recorder preference, rejection checks, missing dependencies, frame retention and feedback delivery.'
} finally { Remove-Item -LiteralPath $AutomationState -Recurse -Force }
