#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Repository = 'C:\Users\giuse\Documents\okami-minigame',
    [switch]$Apply,
    [switch]$Watch,
    [ValidateRange(30,86400)][int]$QuietSeconds = 120,
    [ValidateRange(5,3600)][int]$PollSeconds = 30,
    [ValidateRange(1,1440)][int]$MinimumCommitMinutes = 10,
    [ValidateRange(1,3600)][int]$GitTimeoutSeconds = 120,
    [ValidateRange(1,7200)][int]$NetworkTimeoutSeconds = 900,
    [ValidateRange(1,14400)][int]$LfsTimeoutSeconds = 1800,
    [ValidateRange(1,3600)][int]$ScanTimeoutSeconds = 120,
    [ValidateRange(1,60)][int]$HeartbeatSeconds = 10,
    [ValidateRange(0,100000)][int]$MaxCycles = 0
)
$ErrorActionPreference = 'Stop'
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'Never'
# Application-only lookup bypasses aliases/functions named Git (case-insensitive).
$GitExecutable = (Get-Command -Name git -CommandType Application -ErrorAction Stop |
    Select-Object -First 1).Source
$Repository = (Resolve-Path -LiteralPath $Repository).Path
$state = Join-Path $env:LOCALAPPDATA 'SunwardGitSync'
New-Item -ItemType Directory -Force -Path $state | Out-Null
$pauseFile = Join-Path $state 'PAUSED.txt'
$log = Join-Path $state 'sync.log'
function Report([string]$message) {
    $line = '{0:o} {1}' -f (Get-Date), $message
    Write-Host $line
    if ((Test-Path $log) -and (Get-Item $log).Length -gt 5MB) {
        Move-Item $log "$log.previous" -Force
    }
    Add-Content -LiteralPath $log -Value $line
}
function ConvertTo-NativeArgument([string]$Value) {
    # Windows CRT quoting; also accepted by ProcessStartInfo on PowerShell 7.
    # Preserve spaces, quotes, empty strings, and trailing backslashes; no shell.
    '"' + (($Value -replace '(\\*)"', '$1$1\"') -replace '(\\+)$', '$1$1') + '"'
}
function Stop-GitProcess([Diagnostics.Process]$Process) {
    # Terminate only this invocation and its descendants, never unrelated Git/Unity.
    # Interrupted writes may leave locks or staging: pause, never delete/roll back.
    if ($env:OS -eq 'Windows_NT') {
        $killInfo = New-Object Diagnostics.ProcessStartInfo
        $killInfo.FileName = Join-Path $env:SystemRoot 'System32\taskkill.exe'
        $killInfo.Arguments = "/PID $($Process.Id) /T /F"
        $killInfo.UseShellExecute = $false
        $killInfo.CreateNoWindow = $true
        $killer = [Diagnostics.Process]::Start($killInfo)
        try {
            if (-not $killer.WaitForExit(5000)) { $killer.Kill() }
        } finally { $killer.Dispose() }
    } else {
        # Linux PowerShell test runtime supports the process-tree overload.
        try { $Process.Kill($true) } catch { if (-not $Process.HasExited) { $Process.Kill() } }
    }
    if (-not $Process.WaitForExit(5000)) { throw 'Timed-out Git could not be stopped; inspect its process tree manually.' }
}
function Invoke-SunwardGit([string[]]$Arguments) {
    $timeout = $GitTimeoutSeconds
    if ($Arguments[0] -in @('fetch','push','merge')) { $timeout = $NetworkTimeoutSeconds }
    # add/status/commit/merge can invoke LFS filters or hooks, not just `git lfs`.
    if ($Arguments[0] -eq 'lfs' -and $Arguments[1] -in @('pull','push','fetch')) { $timeout = $LfsTimeoutSeconds }
    $operation = 'git ' + ($Arguments -join ' ')
    Report "GIT START: $operation (timeout=${timeout}s)"
    $info = New-Object Diagnostics.ProcessStartInfo
    $info.FileName = $GitExecutable
    $nativeArguments = @('-c','gc.auto=0','-c','maintenance.auto=false','-C',$Repository) + $Arguments
    $info.Arguments = ($nativeArguments | ForEach-Object { ConvertTo-NativeArgument $_ }) -join ' '
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.RedirectStandardInput = $true
    $info.StandardOutputEncoding = New-Object Text.UTF8Encoding($false)
    $info.StandardErrorEncoding = New-Object Text.UTF8Encoding($false)
    $info.EnvironmentVariables['GIT_TERMINAL_PROMPT'] = '0'
    $info.EnvironmentVariables['GCM_INTERACTIVE'] = 'Never'
    $info.EnvironmentVariables['GIT_PAGER'] = 'cat'
    $process = New-Object Diagnostics.Process
    $process.StartInfo = $info
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $nextHeartbeat = $HeartbeatSeconds
    $started = $false
    try {
        $started = $process.Start()
        $process.StandardInput.Close()
        # Drain BOTH pipes concurrently. Waiting for process exit before reading
        # can deadlock when either pipe fills (or a child inherits a pipe handle).
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        while (-not ($process.HasExited -and $stdout.IsCompleted -and $stderr.IsCompleted)) {
            if ($timer.Elapsed.TotalSeconds -ge $timeout) {
                Report "GIT TIMEOUT: $operation; stopping its process tree and pausing; inspect Git status/locks before resuming."
                Stop-GitProcess $process
                throw "$operation timed out after ${timeout}s. No rollback or lock removal was attempted."
            }
            if ($timer.Elapsed.TotalSeconds -ge $nextHeartbeat) {
                Report ("GIT WAIT: {0}; elapsed={1:n0}s limit={2}s" -f $operation,$timer.Elapsed.TotalSeconds,$timeout)
                $nextHeartbeat = $timer.Elapsed.TotalSeconds + $HeartbeatSeconds
            }
            Start-Sleep -Milliseconds 50
        }
        $output = $stdout.GetAwaiter().GetResult()
        $errorOutput = $stderr.GetAwaiter().GetResult()
        $code = $process.ExitCode
        Report ("GIT END: {0}; exit={1}; elapsed={2:n1}s" -f $operation,$code,$timer.Elapsed.TotalSeconds)
        if ($errorOutput) { Report ('GIT STDERR: ' + $errorOutput.Substring(0, [Math]::Min(4096,$errorOutput.Length)).Trim()) }
        if ($code -ne 0) {
            $detail = ($errorOutput + $output)
            throw "$operation failed: exit=$code $($detail.Substring(0,[Math]::Min(4096,$detail.Length)))"
        }
        return $output.TrimEnd([char[]]"`r`n")
    } catch {
        Report "GIT ERROR: $operation; $($_.Exception.Message)"
        if ($started -and -not $process.HasExited) {
            try { Stop-GitProcess $process } catch { Report "GIT STOP ERROR: $($_.Exception.Message)" }
        }
        throw
    } finally { $process.Dispose() }
}
function Wait-SyncInterval([int]$Seconds, [string]$Stage) {
    Report "$Stage START: ${Seconds}s"
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $nextHeartbeat = $HeartbeatSeconds
    while ($timer.Elapsed.TotalSeconds -lt $Seconds) {
        if (Test-Path -LiteralPath $pauseFile) { throw "Stop/pause requested during $Stage." }
        if ($timer.Elapsed.TotalSeconds -ge $nextHeartbeat) {
            Report ("{0} WAIT: elapsed={1:n0}s of {2}s" -f $Stage,$timer.Elapsed.TotalSeconds,$Seconds)
            $nextHeartbeat = $timer.Elapsed.TotalSeconds + $HeartbeatSeconds
        }
        Start-Sleep -Milliseconds 200
    }
    Report "$Stage END"
}
function RequireIdle {
    if (Test-Path $pauseFile) { throw 'Stop/pause requested; no next Git operation will start.' }
    if (UnityBusy) { throw 'Unity is active; review before resuming.' }
}
function UnityBusy {
    # Conservatively pause for ANY Unity editor, plus the project's editor lock.
    return [bool]((Get-Process -Name Unity -ErrorAction SilentlyContinue) -or
        (Test-Path (Join-Path $Repository 'Sunward-Unity\Temp\UnityLockfile')))
}
function Fingerprint {
    Report 'SCAN START: listing project files'
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $nextHeartbeat = $HeartbeatSeconds
    $count = 0
    $names = ((Invoke-SunwardGit @('ls-files','-z','--cached','--others','--exclude-standard')) + [char]0 +
        (Invoke-SunwardGit @('ls-tree','-r','--name-only','-z','HEAD'))).Split([char]0) |
        Where-Object { $_ } | Sort-Object -Unique
    $lines = foreach ($name in $names) {
        if ($timer.Elapsed.TotalSeconds -ge $ScanTimeoutSeconds) { throw "File scan timed out after ${ScanTimeoutSeconds}s." }
        if (Test-Path -LiteralPath $pauseFile) { throw 'Stop/pause requested during file scan.' }
        if ($timer.Elapsed.TotalSeconds -ge $nextHeartbeat) {
            Report "SCAN WAIT: inspected $count files"
            $nextHeartbeat = $timer.Elapsed.TotalSeconds + $HeartbeatSeconds
        }
        $count++
        $path = Join-Path $Repository $name
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $f = Get-Item -LiteralPath $path
            '{0}|{1}|{2}' -f $name,$f.Length,$f.LastWriteTimeUtc.Ticks
        } else { "$name|missing" }
    }
    Report ("SCAN END: {0} files; elapsed={1:n1}s" -f $count,$timer.Elapsed.TotalSeconds)
    $text = ($lines -join "`n")
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($text))) }
    finally { $sha.Dispose() }
}
function CheckLargeAssets {
    Report 'ASSET CHECK START: large files must have LFS rules'
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $nextHeartbeat = $HeartbeatSeconds
    # Large files without an LFS rule must be explicitly reviewed.
    $names = (Invoke-SunwardGit @('ls-files','-z','--cached','--others','--exclude-standard')).Split([char]0) | Where-Object { $_ }
    foreach ($name in $names) {
        if ($timer.Elapsed.TotalSeconds -ge $ScanTimeoutSeconds) { throw "Large-asset scan timed out after ${ScanTimeoutSeconds}s." }
        if (Test-Path -LiteralPath $pauseFile) { throw 'Stop/pause requested during large-asset scan.' }
        if ($timer.Elapsed.TotalSeconds -ge $nextHeartbeat) {
            Report 'ASSET CHECK WAIT: inspecting LFS rules for large files'
            $nextHeartbeat = $timer.Elapsed.TotalSeconds + $HeartbeatSeconds
        }
        $path = Join-Path $Repository $name
        if ((Test-Path -LiteralPath $path -PathType Leaf) -and ((Get-Item -LiteralPath $path).Length -ge 50MB)) {
            if ((Invoke-SunwardGit @('check-attr','filter','--',$name)) -notmatch ': filter: lfs$') {
                throw "Large asset needs an explicit Git LFS rule: $name"
            }
        }
    }
    Report 'ASSET CHECK END'
}
function CheckRepository {
    Report 'CHECK START: branch, remote, LFS, staging and Git locks'
    if ([IO.Path]::GetFullPath((Invoke-SunwardGit @('rev-parse','--show-toplevel'))).TrimEnd('\','/') -ine [IO.Path]::GetFullPath($Repository).TrimEnd('\','/')) {
        throw 'Repository must be the repository root, not Sunward-Unity.'
    }
    if ((Invoke-SunwardGit @('branch','--show-current')) -cne 'sunward-minigame') { throw 'Expected branch sunward-minigame. No branch switch was attempted.' }
    $url = Invoke-SunwardGit @('remote','get-url','origin')
    if ($url -notmatch '^(https://github\.com/pep-101-png/okami-minigame(?:\.git)?/?|git@github\.com:pep-101-png/okami-minigame(?:\.git)?)$') {
        throw 'origin does not match pep-101-png/okami-minigame.'
    }
    if (-not (Test-Path (Join-Path $Repository 'Sunward-Unity\ProjectSettings\ProjectVersion.txt'))) { throw 'Unity project is missing.' }
    foreach ($marker in @('MERGE_HEAD','CHERRY_PICK_HEAD','REVERT_HEAD','rebase-merge','rebase-apply','index.lock')) {
        $path = Invoke-SunwardGit @('rev-parse','--git-path',$marker)
        if (-not [IO.Path]::IsPathRooted($path)) { $path = Join-Path $Repository $path }
        if (Test-Path -LiteralPath $path) { throw "Git operation or lock present: $marker" }
    }
    if (Invoke-SunwardGit @('ls-files','--unmerged')) { throw 'Unresolved conflicts present.' }
    Invoke-SunwardGit @('lfs','version') | Out-Null
    if ((Invoke-SunwardGit @('config','--get','filter.lfs.process')) -ne 'git-lfs filter-process') {
        throw 'Run Install.ps1 to configure the local Git LFS filter first.'
    }
    $generated = Invoke-SunwardGit @('ls-files','--','Sunward-Unity/Library/*','Sunward-Unity/Temp/*','Sunward-Unity/Logs/*','Sunward-Unity/Obj/*','Sunward-Unity/UserSettings/*','Sunward-Unity/Build/*','Sunward-Unity/Builds/*')
    if ($generated) { throw 'Generated Unity files are already tracked. Review and untrack them manually before syncing.' }

    # Do not stage changes another human has already prepared.
    if (Invoke-SunwardGit @('diff','--cached','--name-only')) { throw 'Staged changes exist; finish or unstage them manually first.' }
    Report 'CHECK END: repository checks passed'
}
function Invoke-SyncCycle {
    if (Test-Path $pauseFile) { throw "Paused. Read $pauseFile and resolve the cause before removing it." }
    CheckRepository
    if (UnityBusy) { Report 'Waiting: close Unity before syncing.' }
    else {
        $before = Fingerprint
        Report "Observing files for $QuietSeconds seconds. Apply=$Apply"
        Wait-SyncInterval $QuietSeconds 'OBSERVE'
        if ((UnityBusy) -or ((Fingerprint) -ne $before)) { Report 'Waiting: project is active or files changed.' }
        else {
            Invoke-SunwardGit @('fetch','--no-tags','origin','refs/heads/sunward-minigame:refs/remotes/origin/sunward-minigame') | Out-Null
            $counts = (Invoke-SunwardGit @('rev-list','--left-right','--count','HEAD...refs/remotes/origin/sunward-minigame')) -split '\s+'
            $ahead = [int]$counts[0]; $behind = [int]$counts[1]
            $dirty = [bool](Invoke-SunwardGit @('status','--porcelain=v1','--untracked-files=all'))
            Report "COMPARE: local commits=$ahead remote commits=$behind uncommitted changes=$dirty"
            if ($ahead -gt 0 -and $behind -gt 0) { throw 'Branches diverged. Review and reconcile manually; no merge or rebase attempted.' }
            if ($behind -gt 0 -and $dirty) { throw 'Remote updates and local changes coexist. Reconcile manually; no stash or merge attempted.' }
            if (-not $Apply) {
                Report "PREVIEW: local commits=$ahead remote commits=$behind uncommitted changes=$dirty. No commit, push, or checkout performed."
            } else {
                CheckRepository
                if ((UnityBusy) -or ((Fingerprint) -ne $before)) { throw 'Files or editor state changed during fetch; retry after review.' }
                if ($behind -gt 0) {
                    RequireIdle
                    Invoke-SunwardGit @('merge','--ff-only','--no-autostash','refs/remotes/origin/sunward-minigame') | Out-Null
                    RequireIdle
                    Invoke-SunwardGit @('lfs','pull','--include=','--exclude=','origin') | Out-Null
                    Report 'Downloaded fast-forward update and LFS assets.'
                } else {
                    $lastFile = Join-Path $state 'last-commit.txt'
                    $cooldown = (Test-Path $lastFile) -and ((Get-Date) -lt ([DateTime]::Parse((Get-Content $lastFile -Raw))).AddMinutes($MinimumCommitMinutes))
                    if ($dirty -and $cooldown) { Report 'Waiting: minimum commit interval has not elapsed.' }
                    elseif ($dirty) {
                        CheckLargeAssets
                        RequireIdle
                        Invoke-SunwardGit @('add','--all','--','.') | Out-Null
                        if ((UnityBusy) -or ((Fingerprint) -ne $before)) {
                            throw 'Files changed while staging. Review staged changes manually before resuming.'
                        }
                        if (Invoke-SunwardGit @('diff','--cached','--name-only')) {
                            RequireIdle
                            Invoke-SunwardGit @('commit','-m',('Sunward autosync {0:yyyy-MM-dd HH:mm:ss zzz}' -f (Get-Date))) | Out-Null
                            (Get-Date).ToString('o') | Set-Content $lastFile
                            Report 'Created snapshot commit.'
                        }
                    }
                    # Explicit LFS upload also protects installations with custom hooks.
                    if ([int](Invoke-SunwardGit @('rev-list','--count','refs/remotes/origin/sunward-minigame..HEAD')) -gt 0) {
                        if (UnityBusy) { throw 'Unity opened before upload; waiting for manual review.' }
                        RequireIdle
                        Invoke-SunwardGit @('lfs','push','origin','HEAD') | Out-Null
                        if (UnityBusy) { throw 'Unity opened during LFS upload; retry after review.' }
                        RequireIdle
                        Invoke-SunwardGit @('push','origin','HEAD:refs/heads/sunward-minigame') | Out-Null
                        Report 'Uploaded commits and LFS assets.'
                    } else { Report 'No outgoing commits.' }
                }
            }
        }
    }
}
function Invoke-SyncMonitoring {
    $cycle = 0
    do {
        $cycle++
        Report "CYCLE $cycle START: Apply=$Apply Watch=$Watch"
        try {
            Invoke-SyncCycle
            Report "CYCLE $cycle END"
            if ((Test-Path $pauseFile) -or (-not $Watch) -or (-not $Apply) -or ($MaxCycles -gt 0 -and $cycle -ge $MaxCycles)) { break }
            Wait-SyncInterval $PollSeconds 'POLL'
        } catch {
            $detail = "$($_.Exception.Message)`nAt: $($_.InvocationInfo.PositionMessage)`n$($_.ScriptStackTrace)"
            # Preserve an operator's existing stop reason; no repeated auto-resume.
            if (-not (Test-Path $pauseFile)) { Set-Content -LiteralPath $pauseFile -Value $detail }
            Report "PAUSED: $detail"
            return 1
        }
    } while ($Watch)
    Report "MONITOR END: completed $cycle cycle(s); no task was enabled or started by this script."
    return 0
}
$mutex = New-Object Threading.Mutex($false, 'Local\SunwardGitSync')
$held = $false
try {
    $held = $mutex.WaitOne(0)
    if (-not $held) { throw 'Another sync instance is running.' }
    Report "START: runner=watchdog-v1 script=$PSCommandPath PID=$PID PowerShell=$($PSVersionTable.PSVersion) repository=$Repository; local=${GitTimeoutSeconds}s network=${NetworkTimeoutSeconds}s LFS=${LfsTimeoutSeconds}s"
    $result = Invoke-SyncMonitoring
    exit $result
} finally {
    if ($held) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
