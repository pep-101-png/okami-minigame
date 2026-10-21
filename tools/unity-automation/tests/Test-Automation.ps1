#requires -Version 5.1
# No real Unity, scheduled tasks, GitHub writes, or real game files are used.
$ErrorActionPreference='Stop'
$tools=Split-Path $PSScriptRoot -Parent
$root=Join-Path ([IO.Path]::GetTempPath()) ('Sunward automation test '+[Guid]::NewGuid().ToString('N'))
$Repository=Join-Path $root 'repository with spaces'
$AutomationState=Join-Path $root 'state'
New-Item -ItemType Directory -Path $Repository,$AutomationState -Force | Out-Null
. (Join-Path $tools 'Common.ps1')
. (Join-Path $tools 'Video.ps1')
. (Join-Path $tools 'Feedback.ps1')
function Assert([bool]$Condition,[string]$Message) { if (-not $Condition) { throw "ASSERT: $Message" } }
$GitExecutable=(Get-Command git -CommandType Application | Select-Object -First 1).Source
try {
    foreach ($p in Get-ChildItem $tools -Filter '*.ps1' -Recurse) {
        $tokens=$null; $errors=$null
        $ast=[Management.Automation.Language.Parser]::ParseFile($p.FullName,[ref]$tokens,[ref]$errors)
        Assert ($errors.Count -eq 0) "parse $($p.Name): $errors"
    }
    $tokens=$null; $errors=$null
    $runAst=[Management.Automation.Language.Parser]::ParseFile((Join-Path $tools 'Run.ps1'),[ref]$tokens,[ref]$errors)
    foreach ($definition in $runAst.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$false)) { . ([scriptblock]::Create($definition.Extent.Text)) }
    Invoke-ReadGit @('init','--initial-branch=sunward-minigame') | Out-Null
    Invoke-ReadGit @('config','user.name','Automation fixture') | Out-Null
    Invoke-ReadGit @('config','user.email','fixture@example.invalid') | Out-Null
    Invoke-ReadGit @('remote','add','origin','https://github.com/pep-101-png/okami-minigame.git') | Out-Null
    foreach ($dir in @('Assets/Sunward/Scenes','Assets/Sunward/Models','Assets/Sunward/Generated/Animations','ProjectSettings','Packages')) { New-Item -ItemType Directory -Path (Join-Path $Repository "Sunward-Unity/$dir") -Force | Out-Null }
    Set-Content (Join-Path $Repository 'Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity') 'fixture scene - no actual game content'
    Set-Content (Join-Path $Repository 'Sunward-Unity/Assets/Sunward/Models/Amaterasu.fbx') 'fixture model'
    Set-Content (Join-Path $Repository 'Sunward-Unity/ProjectSettings/ProjectVersion.txt') 'm_EditorVersion: 6000.6.6f1'
    Set-Content (Join-Path $Repository 'Sunward-Unity/Packages/manifest.json') '{"dependencies":{}}'
    $payload=[Text.Encoding]::UTF8.GetBytes('existing fixture LFS animation data')
    $sha=[Security.Cryptography.SHA256]::Create()
    try { $oid=([BitConverter]::ToString($sha.ComputeHash($payload))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
    $pointer="version https://git-lfs.github.com/spec/v1`noid sha256:$oid`nsize $($payload.Length)`n"
    $liveAsset=Join-Path $Repository 'Sunward-Unity/Assets/Sunward/Generated/Animations/Idle_Natural.anim'
    [IO.File]::WriteAllText($liveAsset,$pointer)
    $cache=Join-Path $Repository ('.git/lfs/objects/'+$oid.Substring(0,2)+'/'+$oid.Substring(2,2))
    New-Item -ItemType Directory -Path $cache -Force | Out-Null
    [IO.File]::WriteAllBytes((Join-Path $cache $oid),$payload)
    Invoke-ReadGit @('add','--all') | Out-Null
    Invoke-ReadGit @('commit','-m','isolated fixture') | Out-Null
    $commit=Invoke-ReadGit @('rev-parse','HEAD')
    Invoke-ReadGit @('update-ref','refs/remotes/origin/sunward-minigame',$commit) | Out-Null
    function Test-OtherUnity([int]$OwnedPid=0) { return $false }
    function Test-OtherGit { return $false }
    Assert (Test-RepositoryReady) 'clean synced fixture should be eligible'
    function Test-OtherUnity([int]$OwnedPid=0) { return $true }
    Assert (-not (Test-RepositoryReady)) 'active Unity was not deferred'
    function Test-OtherUnity([int]$OwnedPid=0) { return $false }
    function Test-OtherGit { return $true }
    Assert (-not (Test-RepositoryReady)) 'active Git was not deferred'
    function Test-OtherGit { return $false }
    Set-Content (Join-Path $Repository '.git/index.lock') 'fixture lock'
    Assert (-not (Test-RepositoryReady)) 'Git lock was not deferred'
    Remove-Item (Join-Path $Repository '.git/index.lock')
    Invoke-ReadGit @('switch','-c','wrong-test-branch') | Out-Null
    $wrongRejected=$false
    try { Test-RepositoryReady | Out-Null } catch { $wrongRejected=$_.Exception.Message -match 'Expected sunward-minigame' }
    Assert $wrongRejected 'wrong branch was accepted'
    Invoke-ReadGit @('switch','sunward-minigame') | Out-Null

    Set-Content (Join-Path $Repository 'unsaved-work.txt') 'preserve'
    Assert (-not (Test-RepositoryReady)) 'dirty repository should defer'
    Remove-Item (Join-Path $Repository 'unsaved-work.txt')
    $run=Join-Path $root 'snapshot test'; New-Item -ItemType Directory $run | Out-Null
    $snapshot=New-ProjectSnapshot $commit $run
    Assert ((Get-FileHash (Join-Path $snapshot 'Assets/Sunward/Generated/Animations/Idle_Natural.anim')).Hash -ieq $oid) 'LFS object was not materialized exactly'
    Assert ([IO.File]::ReadAllText($liveAsset) -ceq $pointer) 'live pointer was overwritten'
    $hashes=Get-ProtectedHashes $snapshot
    Assert (Test-ProtectedHashes $hashes $snapshot) 'unchanged snapshot failed preservation'
    Set-Content (Join-Path $snapshot 'Assets/Sunward/Models/Amaterasu.fbx') 'modified fixture'
    Assert (-not (Test-ProtectedHashes $hashes $snapshot)) 'model mutation not detected'
    $missingRun=Join-Path $root 'missing LFS'; New-Item -ItemType Directory $missingRun | Out-Null
    Move-Item (Join-Path $cache $oid) (Join-Path $cache 'held')
    $rejected=$false
    try { New-ProjectSnapshot $commit $missingRun | Out-Null } catch { $rejected=$_.Exception.Message -match 'Missing cached LFS' }
    Assert $rejected 'missing LFS object was accepted'
    Move-Item (Join-Path $cache 'held') (Join-Path $cache $oid)
    $Config=[pscustomobject]@{Video=[pscustomobject]@{Enabled=$false};UnityTimeoutSeconds=60;PublishReports=$false;CaptureScreenshots=$true;CapturePlayMode=$false;BuildWindowsPlayer=$false;AllowVisibleCapture=$false;KeepSuccessfulSnapshots=$false}
    $script:unityCalls=0
    function Invoke-UnityStage([string]$Snapshot,[string]$RunDirectory,[string]$Method,[string]$Stage,[bool]$Graphics=$false,[bool]$Visible=$false) {
        $script:unityCalls++
        if ($Stage -eq 'validation') { Set-Content (Join-Path $RunDirectory 'validation.json') '{"status":"passed"}'; return [pscustomobject]@{ExitCode=0} }
        Set-Content (Join-Path $RunDirectory 'capture.json') '{"status":"unavailable_or_failed"}'
        return [pscustomobject]@{ExitCode=2}
    }
    $result=Invoke-ValidationJob $commit
    Assert ($result.status -eq 'passed_validation_visual_incomplete') 'unsupported render was falsely treated as fully verified'
    Assert ($result.tests -eq 'skipped_framework_not_installed') 'missing Test Framework was not reported'
    Assert ($result.preservation -eq 'passed') 'job changed protected snapshot data'
    Assert ($script:unityCalls -eq 2) 'job stage ordering changed'
    Assert ((Get-Content (Join-Path $AutomationState 'last-run.json') -Raw | ConvertFrom-Json).commit -eq $commit) 'commit checkpoint missing'
    Assert ([IO.File]::ReadAllText($liveAsset) -ceq $pointer) 'validation changed live asset'
    $checkpointPath=Join-Path $AutomationState 'last-run.json'
    $savedCheckpoint=Get-Content $checkpointPath -Raw
    $deferred=$savedCheckpoint | ConvertFrom-Json
    $deferred.status='deferred';$deferred.attempts=1;$deferred.nextAttemptUtc=(Get-Date).ToUniversalTime().AddMinutes(5).ToString('o')
    $deferred | ConvertTo-Json | Set-Content $checkpointPath
    Assert (-not (Test-CommitPending $commit)) 'deferred retry ignored five-minute backoff'
    $deferred.nextAttemptUtc=(Get-Date).ToUniversalTime().AddMinutes(-1).ToString('o');$deferred.attempts=2
    $deferred | ConvertTo-Json | Set-Content $checkpointPath
    Assert (Test-CommitPending $commit) 'eligible deferred retry was skipped'
    $deferred.attempts=3;$deferred | ConvertTo-Json | Set-Content $checkpointPath
    Assert (-not (Test-CommitPending $commit)) 'deferred retry cap ignored'
    Set-Content $checkpointPath $savedCheckpoint
    foreach ($cycle in 1..3) { Assert (-not (Test-CommitPending $commit)) 'repeated polls retriggered a completed commit' }
    Assert (Test-CommitPending $commit $true) 'explicit Retry was ignored'
    Assert (Test-CommitPending ('f'*40)) 'new commit was skipped'
    $Watch=$true; $Retry=$false
    $Config | Add-Member PollSeconds 0
    $Config | Add-Member StableSeconds 0
    $callsBefore=$script:unityCalls
    Assert ((Invoke-ValidationMonitoring 3) -eq 0) 'three monitoring polls did not complete'
    Assert ($script:unityCalls -eq $callsBefore) 'monitoring loop reran the same completed commit'
    $Watch=$false

    # Video is independent of screenshot configuration; missing capture stays incomplete.
    $Config.Video.Enabled=$true; $Config.CaptureScreenshots=$false
    $callsBefore=$script:unityCalls
    $result=Invoke-ValidationJob $commit
    Assert ($script:unityCalls -eq $callsBefore+2) 'video did not run independently of screenshots'
    Assert ($result.video -eq 'capture_failed_or_incomplete') 'missing video was accepted'
    Assert (Test-Path (Join-Path $result.runDirectory 'video-report.json')) 'missing-video report absent'
    $Config.Video.Enabled=$false
    $script:deferredDeliveries=0
    function Invoke-UnityStage { throw 'Cancelled capture: synthetic process conflict' }
    function Invoke-FeedbackPublish([string]$RunDirectory,[object]$Report) {
        if ($Report.status -eq 'deferred') { $script:deferredDeliveries++ }
        return $false
    }
    $result=Invoke-ValidationJob $commit
    Assert ($result.status -eq 'deferred' -and $script:deferredDeliveries -eq 1) 'deferred failure diagnostics bypassed publisher'
    . (Join-Path $tools 'Feedback.ps1')
    function Invoke-UnityStage { return [pscustomobject]@{ExitCode=1} }
    $result=Invoke-ValidationJob $commit
    Assert ($result.status -eq 'failed') 'compilation/startup failure was accepted'
    Assert ($result.compilation -eq 'failed_or_editor_startup_incomplete') 'missing execute-method report mislabeled compilation'
    # Actual native process behavior, including quotes/empty values and cancellation.
    foreach ($expected in @('', 'spaces and "quotes"','trailing slash \','café')) {
        $r=Invoke-AutomationProcess $GitExecutable @('-c',"automation.test=$expected",'config','--get','automation.test')
        Assert ($r.ExitCode -eq 0 -and $r.Stdout.TrimEnd([char[]]"`r`n") -ceq $expected) 'native quoting changed arguments'
    }
    Invoke-ReadGit @('config','alias.automation-hang','!sleep 30') | Out-Null
    $timer=[Diagnostics.Stopwatch]::StartNew();$stopped=$false
    try { Invoke-AutomationProcess $GitExecutable @('-C',$Repository,'automation-hang') -TimeoutSeconds 1 | Out-Null } catch { $stopped=$_.Exception.Message -match 'Timeout' }
    Assert ($stopped -and $timer.Elapsed.TotalSeconds -lt 12) 'timeout watchdog failed'
    $cancelled=$false
    try { Invoke-AutomationProcess $GitExecutable @('-C',$Repository,'automation-hang') -CancelCheck {param($OwnedPid) $true} | Out-Null } catch { $cancelled=$_.Exception.Message -match 'Cancelled' }
    Assert $cancelled 'active-user/disable cancellation was not honored'
    Invoke-ReadGit @('config','alias.automation-noise','!i=0; while [ "$i" -lt 4000 ]; do printf "stdout abcdefghijklmnopqrstuvwxyz\n"; printf "stderr abcdefghijklmnopqrstuvwxyz\n" >&2; i=$((i+1)); done') | Out-Null
    $r=Invoke-AutomationProcess $GitExecutable @('-C',$Repository,'automation-noise') -TimeoutSeconds 15
    Assert ($r.ExitCode -eq 0 -and $r.Stdout.Length -gt 100000 -and $r.Stderr.Length -gt 100000) 'dual-pipe draining failed'
    if (Get-Command gh -CommandType Application -ErrorAction SilentlyContinue) {
        $Config.PublishReports=$true
        $script:uploaded=@()
        function Invoke-AutomationProcess {
            param([string]$Executable,[string[]]$Arguments,[int]$TimeoutSeconds,[string]$Stage)
            if ($Arguments[0] -eq 'release' -and $Arguments[1] -eq 'view') {
                $assets=@($script:uploaded | ForEach-Object { @{name=$_} })
                return [pscustomobject]@{ExitCode=0;Stdout=(@{assets=$assets}|ConvertTo-Json -Depth 5);Stderr=''}
            }
            if ($Arguments[0] -ne 'release' -or $Arguments[1] -ne 'upload' -or $Arguments[2] -ne 'sunward-unity-feedback') { throw 'Unexpected publishing command' }
            $script:uploaded+= [IO.Path]::GetFileName($Arguments[3])
            return [pscustomobject]@{ExitCode=0;Stdout='';Stderr=''}
        }
        Assert (Publish-Feedback $result.runDirectory $result) 'mock upload failed'
        Assert (Publish-Feedback $result.runDirectory $result) 'idempotent upload retry failed'
        Assert ($script:uploaded.Count -eq 2) 'upload retry duplicated or overwrote assets'
    }
    Write-Host 'PASS: syntax, native process quoting/timeout/cancellation/pipe pressure, synced-state/dirty guards, immutable LFS snapshot, protected hashes, mocked Unity success/failure, honest render/test skips and checkpointing.'
} finally { Remove-Item -LiteralPath $root -Recurse -Force }
