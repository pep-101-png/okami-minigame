#requires -Version 5.1
[CmdletBinding()]
param([string]$Repository='C:\Users\giuse\Documents\okami-minigame',
    [string]$ConfigPath=(Join-Path $PSScriptRoot 'config.json'),[switch]$Watch,[switch]$Retry,
    [string]$StateDirectory=(Join-Path $env:LOCALAPPDATA 'SunwardUnityAutomation'))
$ErrorActionPreference='Stop'
$AutomationState=[IO.Path]::GetFullPath($StateDirectory)
New-Item -ItemType Directory -Path $AutomationState -Force | Out-Null
. (Join-Path $PSScriptRoot 'Common.ps1')
function Invoke-UnityStage([string]$Snapshot,[string]$RunDirectory,[string]$Method,[string]$Stage,[bool]$Graphics=$false,[bool]$Visible=$false) {
    if (Test-OtherUnity) { throw 'Unity opened before launch; validation deferred.' }
    $argsList=@('-projectPath',$Snapshot,'-executeMethod',$Method,'-logFile',(Join-Path $RunDirectory "$Stage-editor.log"))
    if (-not $Visible) { $argsList=@('-batchmode')+$argsList }
    if ($Stage -in @('validation','build')) { $argsList=@('-quit')+$argsList }
    if (-not $Graphics) { $argsList=@('-nographics')+$argsList }
    $environment=@{SUNWARD_AUTOMATION_READONLY='1';SUNWARD_AUTOMATION_OUTPUT=$RunDirectory;SUNWARD_AUTOMATION_STAGE=$Stage;SUNWARD_AUTOMATION_DATA=(Join-Path $RunDirectory 'save-data')}
    $cancel={ param($OwnedPid) (Test-Path (Join-Path $AutomationState 'DISABLED')) -or (Test-OtherUnity $OwnedPid) }
    Invoke-AutomationProcess -Executable $UnityPath -Arguments $argsList -TimeoutSeconds $Config.UnityTimeoutSeconds -Environment $environment -CancelCheck $cancel -Stage $Stage -WorkingDirectory $Snapshot
}
function Publish-Feedback([string]$RunDirectory,[object]$Report) {
    $reportPath=Join-Path $RunDirectory 'report.json'
    $Report | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $reportPath -Encoding UTF8
    if (-not $Config.PublishReports) { Write-AutomationLog 'UPLOAD skipped: PublishReports=false'; return $false }
    $gh=(Get-Command gh -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
    $assetName=$Report.commit+'-'+$Report.runId
    $payload=Join-Path $RunDirectory 'feedback'
    $payload=$payload+'-'+[Guid]::NewGuid().ToString('N')
    New-Item -ItemType Directory -Path $payload | Out-Null
    foreach ($p in Get-ChildItem -LiteralPath $RunDirectory -File | Where-Object { $_.Extension -in @('.json','.xml','.log') -and $_.Name -notlike '*-report.json' }) { Copy-Item -LiteralPath $p.FullName -Destination $payload }
    if (Test-Path (Join-Path $RunDirectory 'screenshots')) { Copy-Item (Join-Path $RunDirectory 'screenshots') $payload -Recurse }
    $archive=Join-Path $RunDirectory ($assetName+'.zip')
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    if (-not (Test-Path $archive)) { [IO.Compression.ZipFile]::CreateFromDirectory($payload,$archive) }
    $summary=Join-Path $RunDirectory ($assetName+'-report.json')
    Copy-Item $reportPath $summary -Force
    $existing=Invoke-AutomationProcess -Executable $gh -Arguments @('release','view','sunward-unity-feedback','--repo','pep-101-png/okami-minigame','--json','assets') -Stage 'check reporting release'
    if ($existing.ExitCode -ne 0) { throw 'Reporting release is unavailable. Create it manually as documented; reports remain local.' }
    $assetNames=@(($existing.Stdout | ConvertFrom-Json).assets | ForEach-Object { $_.name })
    foreach ($asset in @($archive,$summary)) {
        if ([IO.Path]::GetFileName($asset) -in $assetNames) { continue }
        $result=Invoke-AutomationProcess -Executable $gh -Arguments @('release','upload','sunward-unity-feedback',$asset,'--repo','pep-101-png/okami-minigame') -TimeoutSeconds 300 -Stage 'upload feedback'
        if ($result.ExitCode -ne 0) { throw "Upload failed; local reports remain in $RunDirectory. $($result.Stderr)" }
    }
    return $true
}
function Test-CommitPending([string]$Commit,[bool]$Force=$false) {
    if ($Force) { return $true }
    $path=Join-Path $AutomationState 'last-run.json'
    if (-not (Test-Path $path)) { return $true }
    $last=Get-Content $path -Raw | ConvertFrom-Json
    return $last.commit -ne $Commit -or $last.status -eq 'deferred'
}
function Invoke-ValidationJob([string]$Commit) {
    $runId=(Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')+'-'+[Guid]::NewGuid().ToString('N').Substring(0,6)
    $runDirectory=Join-Path (Join-Path $AutomationState 'runs') $runId
    New-Item -ItemType Directory -Path $runDirectory -Force | Out-Null
    $report=[ordered]@{schemaVersion=1;commit=$Commit;runId=$runId;startedUtc=(Get-Date).ToUniversalTime().ToString('o');
        status='running';compilation='not_run';validation='not_run';tests='not_run';visual='not_run';preservation='not_run';build='not_requested';errors=@();runDirectory=$runDirectory}
    $snapshot=$null
    try {
        $snapshot=New-ProjectSnapshot $Commit $runDirectory
        $projectVersion=Get-Content (Join-Path $snapshot 'ProjectSettings/ProjectVersion.txt') -Raw
        if ($projectVersion -notmatch '(?m)^m_EditorVersion: 6000\.6\.6f1\s*$') { throw 'Snapshot Unity version differs from 6000.6.6f1.' }
        $before=Get-ProtectedHashes $snapshot
        if (-not (Test-RepositoryReady) -or (Invoke-ReadGit @('rev-parse','HEAD')) -ne $Commit) { throw 'Live state changed during snapshot creation; no Unity launched.' }
        $r=Invoke-UnityStage $snapshot $runDirectory 'Sunward.Editor.Automation.BatchValidation.Run' 'validation'
        if (-not (Test-Path (Join-Path $runDirectory 'validation.json'))) { $report.compilation='failed_or_editor_startup_incomplete'; throw "No Unity validation report; inspect validation-editor.log for compilation/import/license errors (exit=$($r.ExitCode))." }
        $validation=Get-Content (Join-Path $runDirectory 'validation.json') -Raw | ConvertFrom-Json
        $report.compilation='passed_execute_method_reached'
        $report.validation=$validation.status
        if ($r.ExitCode -ne 0 -or $validation.status -ne 'passed') { throw 'Unity validation failed; see validation.json and editor log.' }
        $manifest=Get-Content (Join-Path $snapshot 'Packages/manifest.json') -Raw | ConvertFrom-Json
        if ($manifest.dependencies.PSObject.Properties.Name -contains 'com.unity.test-framework') {
            foreach ($platform in @('EditMode')) {
                if (Test-OtherUnity) { throw 'Unity opened before test launch.' }
                $xml=Join-Path $runDirectory "$platform-results.xml"
                $r=Invoke-AutomationProcess -Executable $UnityPath -Arguments @('-batchmode','-nographics','-projectPath',$snapshot,'-runTests','-testPlatform',$platform,'-testResults',$xml,'-logFile',(Join-Path $runDirectory "$platform-editor.log")) -TimeoutSeconds $Config.UnityTimeoutSeconds -Environment @{SUNWARD_AUTOMATION_READONLY='1';SUNWARD_AUTOMATION_DATA=(Join-Path $runDirectory 'save-data')} -CancelCheck {param($OwnedPid) (Test-Path (Join-Path $AutomationState 'DISABLED')) -or (Test-OtherUnity $OwnedPid)} -Stage $platform -WorkingDirectory $snapshot
                if ($r.ExitCode -ne 0 -or -not (Test-Path $xml)) { throw 'Unity Test Framework did not return successful results.' }
                [xml]$testXml=Get-Content $xml -Raw
                if (-not $testXml.'test-run' -or -not $testXml.'test-run'.result) { throw 'Malformed or incomplete test result XML.' }
                if ($testXml.'test-run'.result -ne 'Passed' -or [int]$testXml.'test-run'.failed -gt 0) { throw 'EditMode tests failed.' }
                $report.tests=if ([int]$testXml.'test-run'.total -gt 0) { 'passed_editmode' } else { 'skipped_no_discovered_tests' }
            }
        } else { $report.tests='skipped_framework_not_installed' }
        if ($Config.CaptureScreenshots) {
            $r=Invoke-UnityStage $snapshot $runDirectory 'Sunward.Editor.Automation.SceneCapture.Run' 'capture' $true
            $capturePath=Join-Path $runDirectory 'capture.json'
            $capture=if (Test-Path $capturePath) { Get-Content $capturePath -Raw | ConvertFrom-Json } else { $null }
            if (($r.ExitCode -ne 0 -or -not $capture -or $capture.status -ne 'passed') -and $Config.AllowVisibleCapture) {
                $r=Invoke-UnityStage $snapshot $runDirectory 'Sunward.Editor.Automation.SceneCapture.Run' 'capture-visible' $true $true
                $capture=if (Test-Path $capturePath) { Get-Content $capturePath -Raw | ConvertFrom-Json } else { $null }
            }
            $report.visual=if ($capture -and $r.ExitCode -eq 0) { $capture.status } else { 'unavailable_or_failed' }
        } else { $report.visual='skipped_configuration' }
        if ($Config.CaptureScreenshots -and $Config.CapturePlayMode) {
            $r=Invoke-UnityStage $snapshot $runDirectory 'Sunward.Editor.Automation.GameplayCapture.Run' 'gameplay-capture' $true
            $livePath=Join-Path $runDirectory 'gameplay-capture.json'
            $report.gameplayCapture=if (Test-Path $livePath) { (Get-Content $livePath -Raw | ConvertFrom-Json).status } else { 'unavailable_or_failed' }
            if ($r.ExitCode -ne 0 -or $report.gameplayCapture -ne 'rendered_unreviewed') { $report.visual='incomplete' }
        }
        if ($Config.BuildWindowsPlayer) {
            $r=Invoke-UnityStage $snapshot $runDirectory 'Sunward.Editor.Automation.BatchValidation.Build' 'build'
            $buildPath=Join-Path $runDirectory 'build-summary.json'
            $report.build=if (Test-Path $buildPath) { (Get-Content $buildPath -Raw | ConvertFrom-Json).status } else { 'failed_no_summary' }
            if ($r.ExitCode -ne 0 -or $report.build -ne 'passed') { throw 'Windows build failed; see build-summary.json and build-editor.log.' }
        }
        $report.preservation=if (Test-ProtectedHashes $before $snapshot) { 'passed' } else { 'failed_snapshot_assets_changed' }
        if ($report.preservation -ne 'passed') { throw 'Protected source assets changed inside the snapshot. No live files were changed.' }
        if ($report.visual -eq 'passed' -and -not (Get-ChildItem (Join-Path $runDirectory 'screenshots') -Filter '*.png' -ErrorAction SilentlyContinue | Where-Object { $_.Length -gt 128 })) { $report.visual='incomplete_no_images' }
        $report.status=if ($report.visual -eq 'passed') { 'passed_technical_checks_visual_review_required' } else { 'passed_validation_visual_incomplete' }
    } catch {
        $report.status=if ($_.Exception.Message -match 'Unity opened|Live state changed|Cancelled') { 'deferred' } else { 'failed' }
        $report.errors+= $_.Exception.Message; Write-AutomationLog "JOB $($report.status): $($_.Exception.Message)"
    }
    @{status=$report.compilation;editorLog='validation-editor.log';scope='Execute-method reachability, not complete shader variant coverage'} | ConvertTo-Json | Set-Content (Join-Path $runDirectory 'compilation.json') -Encoding UTF8
    $report.finishedUtc=(Get-Date).ToUniversalTime().ToString('o')
    $report | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $runDirectory 'report.json') -Encoding UTF8
    $published=$false
    if ($report.status -ne 'deferred') { try { $published=Publish-Feedback $runDirectory $report } catch { Write-AutomationLog $_.Exception.Message } }
    $checkpoint=[ordered]@{commit=$Commit;runDirectory=$runDirectory;status=$report.status;published=$published;finishedUtc=$report.finishedUtc}
    $checkpoint | ConvertTo-Json | Set-Content (Join-Path $AutomationState 'last-run.json') -Encoding UTF8
    # Only successful, completed runner-created snapshots are disposable; reports remain.
    if ($snapshot -and $report.status -like 'passed*' -and -not $Config.KeepSuccessfulSnapshots) { try { Remove-OwnedSnapshot $snapshot $runDirectory } catch { Write-AutomationLog $_.Exception.Message } }
    Write-AutomationLog "JOB END: $($report.status) published=$published"
    return $report
}
function Invoke-ValidationMonitoring([int]$MaxPolls=0) {
    $candidate=$null; $stable=[Diagnostics.Stopwatch]::StartNew()
    $polls=0
    do {
        $polls++
        if (Test-Path (Join-Path $AutomationState 'DISABLED')) { break }
        if (Test-RepositoryReady) {
            $head=Invoke-ReadGit @('rev-parse','HEAD')
            if ($head -ne $candidate) { $candidate=$head; $stable.Restart(); Write-AutomationLog "Candidate $head; waiting $($Config.StableSeconds)s for stable sync." }
            if ($stable.Elapsed.TotalSeconds -ge $Config.StableSeconds) {
                if (Test-CommitPending $head ([bool]$Retry)) { $job=Invoke-ValidationJob $head; $Retry=$false; if (-not $Watch -and $job.status -eq 'failed') { return 1 } }
                else { Write-AutomationLog "Already attempted $head; no repeat validation or report upload." }
                if (-not $Watch) { break }
            }
        } else { $candidate=$null; $stable.Restart(); if (-not $Watch) { break } }
        if ($MaxPolls -gt 0 -and $polls -ge $MaxPolls) { break }
        $remaining=$Config.PollSeconds
        while ($remaining-- -gt 0 -and -not (Test-Path (Join-Path $AutomationState 'DISABLED'))) { Start-Sleep -Seconds 1 }
    } while ($true)
    return 0
}
$mutex=$null; $held=$false
try {
    if (Test-Path (Join-Path $AutomationState 'DISABLED')) { throw 'Automation is disabled. Review before removing DISABLED or using Enable.ps1.' }
    if (-not (Test-Path $ConfigPath)) { throw 'Copy config.example.json to config.json and review it before running.' }
    $Config=Get-Content $ConfigPath -Raw | ConvertFrom-Json
    foreach ($name in @('CaptureScreenshots','CapturePlayMode','AllowVisibleCapture','PublishReports','BuildWindowsPlayer','KeepSuccessfulSnapshots')) { if ($Config.$name -isnot [bool]) { throw "Config $name must be a JSON boolean." } }
    if ($Config.PollSeconds -lt 10 -or $Config.StableSeconds -lt 10 -or $Config.UnityTimeoutSeconds -lt 60) { throw 'Unsafe timing configuration.' }
    $Repository=(Resolve-Path -LiteralPath $Repository).Path
    if ($AutomationState.StartsWith($Repository.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase) -or $AutomationState -eq $Repository) { throw 'State directory must be outside the source repository.' }
    $GitExecutable=(Get-Command git -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
    $UnityPath=Find-UnityEditor $Config.UnityEditor
    $mutex=New-Object Threading.Mutex($false,'Local\SunwardUnityAutomation')
    $held=$mutex.WaitOne(0)
    if (-not $held) { throw 'Another automation runner owns the mutex.' }
    $exitCode=Invoke-ValidationMonitoring
    exit $exitCode
} catch { Write-AutomationLog "RUNNER ERROR: $($_.Exception.Message)"; exit 1 }
finally { if ($held) { $mutex.ReleaseMutex() }; if ($mutex) { $mutex.Dispose() } }
