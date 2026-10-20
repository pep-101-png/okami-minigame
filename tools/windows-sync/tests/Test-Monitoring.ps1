#requires -Version 5.1
# Real local Git/LFS integration; no GitHub, real Unity assets, or scheduled tasks.
$ErrorActionPreference = 'Stop'
$GitExecutable = (Get-Command git -CommandType Application | Select-Object -First 1).Source
$root = Join-Path ([IO.Path]::GetTempPath()) ('Sunward monitoring ' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root | Out-Null
$Repository = $root
$state = Join-Path $root 'state'
New-Item -ItemType Directory -Path $state | Out-Null
$log = Join-Path $state 'sync.log'
$pauseFile = Join-Path $state 'PAUSED.txt'
$GitTimeoutSeconds = 15; $NetworkTimeoutSeconds = 15; $LfsTimeoutSeconds = 15
$ScanTimeoutSeconds = 15; $HeartbeatSeconds = 1
$QuietSeconds = 0; $PollSeconds = 0; $MinimumCommitMinutes = 10
$Apply = $true; $Watch = $true; $MaxCycles = 3
$tokens = $null; $errors = $null
$ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path (Split-Path $PSScriptRoot -Parent) 'Sync.ps1'),[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors -join '; ') }
foreach ($definition in $ast.FindAll({ param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] }, $false)) {
    . ([scriptblock]::Create($definition.Extent.Text))
}
function Assert([bool]$Condition,[string]$Message) { if (-not $Condition) { throw "ASSERT: $Message" } }
# No Unity process probes against the host: fixture controls this safety signal.
$script:busy = $false
function UnityBusy { return $script:busy }
# Real local remotes for all I/O. Only the URL identity check is substituted.
$nativeGit = ${function:Invoke-SunwardGit}
function Invoke-SunwardGit([string[]]$Arguments) {
    if (($Arguments -join ' ') -eq 'remote get-url origin') { return 'https://github.com/pep-101-png/okami-minigame.git' }
    & $nativeGit $Arguments
}
try {
    $bare = Join-Path $root 'remote.git'
    $working = Join-Path $root 'working tree'
    Invoke-SunwardGit @('init','--bare','--initial-branch=sunward-minigame',$bare) | Out-Null
    Invoke-SunwardGit @('clone',$bare,$working) | Out-Null
    $Repository = $working
    Invoke-SunwardGit @('config','user.name','Sync test') | Out-Null
    Invoke-SunwardGit @('config','user.email','sync-test@example.invalid') | Out-Null
    Invoke-SunwardGit @('config','filter.lfs.process','git-lfs filter-process') | Out-Null
    $settings = Join-Path $working 'Sunward-Unity/ProjectSettings'
    New-Item -ItemType Directory -Path $settings -Force | Out-Null
    Set-Content (Join-Path $settings 'ProjectVersion.txt') 'test fixture marker only'
    Set-Content (Join-Path $working 'note.txt') 'baseline'
    Invoke-SunwardGit @('add','--all') | Out-Null
    Invoke-SunwardGit @('commit','-m','fixture baseline') | Out-Null
    Invoke-SunwardGit @('push','origin','HEAD:refs/heads/sunward-minigame') | Out-Null
    $baseline = Invoke-SunwardGit @('rev-parse','HEAD')

    Assert ((Invoke-SyncMonitoring) -eq 0) 'three no-op watch cycles should complete'
    Assert ((Get-Content $log -Raw) -match 'CYCLE 3 END') 'watch loop did not reach cycle three'
    Assert ((Invoke-SunwardGit @('rev-parse','HEAD')) -eq $baseline) 'no-op loop created a commit'

    $Apply = $false
    Assert ((Invoke-SyncMonitoring) -eq 0) 'preview should complete without applying'
    Assert ((Invoke-SunwardGit @('rev-parse','HEAD')) -eq $baseline) 'preview changed HEAD'
    $Apply = $true

    Set-Content (Join-Path $working 'saved file.txt') 'saved change'
    Assert ((Invoke-SyncMonitoring) -eq 0) 'local save should upload and keep watching'
    Assert ((Invoke-SunwardGit @('rev-list','--count',"$baseline..HEAD")) -eq '1') 'sync loop made duplicate commits'
    Assert (-not (Invoke-SunwardGit @('status','--porcelain'))) 'upload left changes'
    Assert ((Invoke-SunwardGit @('rev-parse','HEAD')) -eq (Invoke-SunwardGit @('rev-parse','origin/sunward-minigame'))) 'remote did not receive commit'

    # A different clone supplies an incoming commit; only temporary fixture text is edited.
    $peer = Join-Path $root 'peer'
    Invoke-SunwardGit @('clone',$bare,$peer) | Out-Null
    $Repository = $peer
    Invoke-SunwardGit @('config','user.name','Peer test') | Out-Null
    Invoke-SunwardGit @('config','user.email','peer@example.invalid') | Out-Null
    Set-Content (Join-Path $peer 'remote-note.txt') 'incoming'
    Invoke-SunwardGit @('add','--all') | Out-Null
    Invoke-SunwardGit @('commit','-m','incoming fixture change') | Out-Null
    Invoke-SunwardGit @('push','origin','HEAD:refs/heads/sunward-minigame') | Out-Null
    $Repository = $working
    Assert ((Invoke-SyncMonitoring) -eq 0) 'remote update should fast-forward and keep watching'
    Assert ((Get-Content (Join-Path $working 'remote-note.txt') -Raw).Trim() -eq 'incoming') 'remote text not downloaded'

    $script:busy = $true
    $before = Invoke-SunwardGit @('rev-parse','HEAD')
    Assert ((Invoke-SyncMonitoring) -eq 0) 'Unity-busy cycles should wait, not fail'
    Assert ((Invoke-SunwardGit @('rev-parse','HEAD')) -eq $before) 'Unity-busy cycle changed HEAD'
    $script:busy = $false

    # Cooldown is retained: another save must remain uncommitted.
    Set-Content (Join-Path $working 'saved file.txt') 'another save'
    Assert ((Invoke-SyncMonitoring) -eq 0) 'cooldown cycle failed'
    Assert ((Invoke-SunwardGit @('rev-parse','HEAD')) -eq $before) 'cooldown was bypassed'

    # Dirty + remote ahead must pause, leaving the local edit and HEAD intact.
    $Repository = $peer
    Set-Content (Join-Path $peer 'remote-note.txt') 'next incoming'
    Invoke-SunwardGit @('add','--all') | Out-Null
    Invoke-SunwardGit @('commit','-m','second incoming fixture change') | Out-Null
    Invoke-SunwardGit @('push','origin','HEAD:refs/heads/sunward-minigame') | Out-Null
    $Repository = $working
    Assert ((Invoke-SyncMonitoring) -eq 1) 'dirty + remote-ahead was not paused'
    Assert ((Get-Content $pauseFile -Raw) -match 'Remote updates and local changes coexist') 'pause omitted reason'
    Assert ((Get-Content (Join-Path $working 'saved file.txt') -Raw).Trim() -eq 'another save') 'local save was overwritten'
    Assert ((Invoke-SunwardGit @('rev-parse','HEAD')) -eq $before) 'HEAD moved during unsafe incoming sync'
    Remove-Item $pauseFile

    # Existing staged work and divergent histories must remain for a human.
    Invoke-SunwardGit @('add','--','saved file.txt') | Out-Null
    Assert ((Invoke-SyncMonitoring) -eq 1) 'existing staging was not rejected'
    Assert ((Get-Content $pauseFile -Raw) -match 'Staged changes exist') 'staging guard reason missing'
    Assert ((Invoke-SunwardGit @('diff','--cached','--name-only')) -eq 'saved file.txt') 'staged work changed'
    Remove-Item $pauseFile
    Invoke-SunwardGit @('commit','-m','manual fixture local work') | Out-Null
    $divergentHead = Invoke-SunwardGit @('rev-parse','HEAD')
    Assert ((Invoke-SyncMonitoring) -eq 1) 'divergence was not paused'
    Assert ((Get-Content $pauseFile -Raw) -match 'Branches diverged') 'divergence reason missing'
    Assert ((Invoke-SunwardGit @('rev-parse','HEAD')) -eq $divergentHead) 'divergent local commit changed'
    Remove-Item $pauseFile
    Invoke-SunwardGit @('switch','-c','wrong-fixture-branch') | Out-Null
    Assert ((Invoke-SyncMonitoring) -eq 1) 'wrong branch was not rejected'
    Assert ((Get-Content $pauseFile -Raw) -match 'Expected branch sunward-minigame') 'branch guard reason missing'
    Remove-Item $pauseFile
    Invoke-SunwardGit @('switch','sunward-minigame') | Out-Null

    # Scan work has its own deadline, independent of per-command limits.
    $ScanTimeoutSeconds = 0
    $scanStopped = $false
    try { Fingerprint | Out-Null } catch { $scanStopped = $_.Exception.Message -match 'File scan timed out' }
    Assert $scanStopped 'file-scan deadline was not enforced'
    $ScanTimeoutSeconds = 15

    # Drain enough stdout AND stderr to exceed typical pipe buffers.
    Invoke-SunwardGit @('config','alias.watchdog-noise','!i=0; while [ "$i" -lt 6000 ]; do printf "stdout line abcdefghijklmnopqrstuvwxyz\n"; printf "stderr line abcdefghijklmnopqrstuvwxyz\n" >&2; i=$((i+1)); done') | Out-Null
    $noise = Invoke-SunwardGit @('watchdog-noise')
    Assert ($noise.Length -gt 200000 -and $noise -notmatch 'stderr') 'pipe draining mixed or lost stdout'

    # Real hung Git subprocess, exercised through the actual monitoring catch/pause.
    Invoke-SunwardGit @('config','alias.watchdog-hang','!sleep 30') | Out-Null
    $GitTimeoutSeconds = 1
    function Invoke-SyncCycle { Invoke-SunwardGit @('watchdog-hang') | Out-Null }
    $timer = [Diagnostics.Stopwatch]::StartNew()
    Assert ((Invoke-SyncMonitoring) -eq 1) 'hung subprocess did not pause monitoring'
    Assert ($timer.Elapsed.TotalSeconds -lt 12) 'timeout cleanup took too long'
    Assert ((Get-Content $pauseFile -Raw) -match 'timed out') 'timeout pause reason missing'
    Assert ((Get-Content $log -Raw) -match 'GIT TIMEOUT: git watchdog-hang') 'timeout stage was not logged'
    Remove-Item $pauseFile

    # Waits produce progress and honor an operator pause without replacing its reason.
    Wait-SyncInterval 2 'TEST OBSERVE'
    Assert ((Get-Content $log -Raw) -match 'TEST OBSERVE WAIT') 'observation heartbeat missing'
    Set-Content $pauseFile 'operator stop'
    function Invoke-SyncCycle { Wait-SyncInterval 2 'TEST STOP' }
    Assert ((Invoke-SyncMonitoring) -eq 1) 'stop request during wait was ignored'
    Assert ((Get-Content $pauseFile -Raw).Trim() -eq 'operator stop') 'operator pause reason was replaced'
    Write-Host 'PASS: repeated no-op/upload/download/busy/cooldown cycles; dirty/staged/diverged/wrong-branch guards; scan deadline; dual-pipe pressure; timeout/pause; wait heartbeat and stop.'
} finally {
    # Only disposable fixture data is removed, never the real project or its state.
    Remove-Item -LiteralPath $root -Recurse -Force
}
