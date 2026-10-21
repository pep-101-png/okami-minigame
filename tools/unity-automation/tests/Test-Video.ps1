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
    $result=Complete-GameplayVideos $AutomationState $settings
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
    $result=Complete-GameplayVideos $AutomationState $settings
    Assert ($result.clips[0].encoder -eq 'unity_recorder') 'verified Recorder preference'
    Remove-Item (Join-Path $AutomationState 'videos/fixture.mp4')
    $clip.recorderCandidate=''
    @{status='frames_captured_unreviewed';clips=@($clip)} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $AutomationState 'video-capture.json')
    $settings.FFmpegPath=Join-Path $AutomationState 'missing-ffmpeg';$settings.FFprobePath=Join-Path $AutomationState 'missing-probe'
    $result=Complete-GameplayVideos $AutomationState $settings
    Assert ($result.clips[0].status -eq 'frames_only_missing_ffmpeg') 'explicit missing dependencies'
    Assert (@(Get-ChildItem $frames -Filter '*.png').Count -eq 12) 'preserve numbered frames'
    Assert (Test-Path (Join-Path $AutomationState 'videos/fixture-frames.zip')) 'bounded fallback frame archive'
    Set-Content (Join-Path $AutomationState 'videos/fixture-partial-test.mp4') 'partial'
    $payload=Join-Path $AutomationState 'payload';New-Item -ItemType Directory $payload | Out-Null
    Copy-VideoFeedback $AutomationState $payload $settings
    Assert (-not (Test-Path (Join-Path $payload 'videos/fixture-partial-test.mp4'))) 'never publish partial MP4'
    # Cleanup requires an ownership marker AND a verified MP4.
    $settings.FFmpegPath=$ffmpeg;$settings.FFprobePath=$probe;$settings.KeepEncodedFrames=$false
    $result=Complete-GameplayVideos $AutomationState $settings
    Assert (@(Get-ChildItem $frames -Filter '*.png').Count -eq 12) 'unmarked files must remain'
    Set-Content (Join-Path $frames '.sunward-owned-frames') 'fixture'
    $result=Complete-GameplayVideos $AutomationState $settings
    Assert ($result.clips[0].status -eq 'encoded_verified_unreviewed') 'recheck existing MP4'
    Assert (@(Get-ChildItem $frames -Filter '*.png').Count -eq 0) 'verified owned frames cleaned'
    Write-Host 'PASS: deterministic 14-clip plan, real FFmpeg/ffprobe encoding, contact sheets, Recorder preference, rejection checks, missing dependencies, frame retention and feedback delivery.'
} finally { Remove-Item -LiteralPath $AutomationState -Recurse -Force }
