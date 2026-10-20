#requires -Version 5.1
[CmdletBinding()]
param(
    [string]$Repository = 'C:\Users\giuse\Documents\okami-minigame',
    [switch]$Apply,
    [switch]$Watch,
    [ValidateRange(30,86400)][int]$QuietSeconds = 120,
    [ValidateRange(5,3600)][int]$PollSeconds = 30,
    [ValidateRange(1,1440)][int]$MinimumCommitMinutes = 10
)
$ErrorActionPreference = 'Stop'
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'Never'
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
function Git([string[]]$Arguments) {
    # Windows PowerShell 5.1 wraps native stderr even when Git succeeds.
    $savedPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $result = & git -C $Repository @Arguments 2>&1
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $savedPreference }
    if ($code -ne 0) { throw "git $($Arguments -join ' ') failed: $($result -join ' ')" }
    return ($result -join "`n")
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
    $names = ((Git @('ls-files','-z','--cached','--others','--exclude-standard')) + [char]0 +
        (Git @('ls-tree','-r','--name-only','-z','HEAD'))).Split([char]0) |
        Where-Object { $_ } | Sort-Object -Unique
    $lines = foreach ($name in $names) {
        $path = Join-Path $Repository $name
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $f = Get-Item -LiteralPath $path
            '{0}|{1}|{2}' -f $name,$f.Length,$f.LastWriteTimeUtc.Ticks
        } else { "$name|missing" }
    }
    $text = ($lines -join "`n")
    $sha = [Security.Cryptography.SHA256]::Create()
    try { return [BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes($text))) }
    finally { $sha.Dispose() }
}
function CheckRepository {
    if ((Git @('rev-parse','--show-toplevel')).Replace('/','\').TrimEnd('\') -ine $Repository.TrimEnd('\')) {
        throw 'Repository must be the repository root, not Sunward-Unity.'
    }
    if ((Git @('branch','--show-current')) -cne 'sunward-minigame') { throw 'Expected branch sunward-minigame. No branch switch was attempted.' }
    $url = Git @('remote','get-url','origin')
    if ($url -notmatch '^(https://github\.com/pep-101-png/okami-minigame(?:\.git)?/?|git@github\.com:pep-101-png/okami-minigame(?:\.git)?)$') {
        throw 'origin does not match pep-101-png/okami-minigame.'
    }
    if (-not (Test-Path (Join-Path $Repository 'Sunward-Unity\ProjectSettings\ProjectVersion.txt'))) { throw 'Unity project is missing.' }
    foreach ($marker in @('MERGE_HEAD','CHERRY_PICK_HEAD','REVERT_HEAD','rebase-merge','rebase-apply','index.lock')) {
        $path = Git @('rev-parse','--git-path',$marker)
        if (-not [IO.Path]::IsPathRooted($path)) { $path = Join-Path $Repository $path }
        if (Test-Path -LiteralPath $path) { throw "Git operation or lock present: $marker" }
    }
    if (Git @('ls-files','--unmerged')) { throw 'Unresolved conflicts present.' }
    Git @('lfs','version') | Out-Null
    if ((Git @('config','--get','filter.lfs.process')) -ne 'git-lfs filter-process') {
        throw 'Run Install.ps1 to configure the local Git LFS filter first.'
    }
    $generated = Git @('ls-files','--','Sunward-Unity/Library/*','Sunward-Unity/Temp/*','Sunward-Unity/Logs/*','Sunward-Unity/Obj/*','Sunward-Unity/UserSettings/*','Sunward-Unity/Build/*','Sunward-Unity/Builds/*')
    if ($generated) { throw 'Generated Unity files are already tracked. Review and untrack them manually before syncing.' }

    # Do not stage changes another human has already prepared.
    if (Git @('diff','--cached','--name-only')) { throw 'Staged changes exist; finish or unstage them manually first.' }
}
$mutex = New-Object Threading.Mutex($false, 'Local\SunwardGitSync')
$held = $false
try {
    $held = $mutex.WaitOne(0)
    if (-not $held) { throw 'Another sync instance is running.' }
    do {
        try {
            if (Test-Path $pauseFile) { throw "Paused. Read $pauseFile and resolve the cause before removing it." }
            CheckRepository
            if (UnityBusy) { Report 'Waiting: close Unity before syncing.' }
            else {
                $before = Fingerprint
                Report "Observing files for $QuietSeconds seconds. Apply=$Apply"
                Start-Sleep -Seconds $QuietSeconds
                if ((UnityBusy) -or ((Fingerprint) -ne $before)) { Report 'Waiting: project is active or files changed.' }
                else {
                    Git @('fetch','--no-tags','origin','refs/heads/sunward-minigame:refs/remotes/origin/sunward-minigame') | Out-Null
                    $counts = (Git @('rev-list','--left-right','--count','HEAD...refs/remotes/origin/sunward-minigame')) -split '\s+'
                    $ahead = [int]$counts[0]; $behind = [int]$counts[1]
                    $dirty = [bool](Git @('status','--porcelain=v1','--untracked-files=all'))
                    if ($ahead -gt 0 -and $behind -gt 0) { throw 'Branches diverged. Review and reconcile manually; no merge or rebase attempted.' }
                    if ($behind -gt 0 -and $dirty) { throw 'Remote updates and local changes coexist. Reconcile manually; no stash or merge attempted.' }
                    if (-not $Apply) {
                        Report "PREVIEW: local commits=$ahead remote commits=$behind uncommitted changes=$dirty. No commit, push, or checkout performed."
                    } else {
                        CheckRepository
                        if ((UnityBusy) -or ((Fingerprint) -ne $before)) { throw 'Files or editor state changed during fetch; retry after review.' }
                        if ($behind -gt 0) {
                            RequireIdle
                            Git @('merge','--ff-only','--no-autostash','refs/remotes/origin/sunward-minigame') | Out-Null
                            Git @('lfs','pull','--include=','--exclude=','origin') | Out-Null
                            Report 'Downloaded fast-forward update and LFS assets.'
                        } else {
                            $lastFile = Join-Path $state 'last-commit.txt'
                            $cooldown = (Test-Path $lastFile) -and ((Get-Date) -lt ([DateTime]::Parse((Get-Content $lastFile -Raw))).AddMinutes($MinimumCommitMinutes))
                            if ($dirty -and $cooldown) { Report 'Waiting: minimum commit interval has not elapsed.' }
                            elseif ($dirty) {
                                # Large files without an LFS rule must be explicitly reviewed.
                                $names = (Git @('ls-files','-z','--cached','--others','--exclude-standard')).Split([char]0) | Where-Object { $_ }
                                foreach ($name in $names) {
                                    $path = Join-Path $Repository $name
                                    if ((Test-Path -LiteralPath $path -PathType Leaf) -and ((Get-Item -LiteralPath $path).Length -ge 50MB)) {
                                        if ((Git @('check-attr','filter','--',$name)) -notmatch ': filter: lfs$') {
                                            throw "Large asset needs an explicit Git LFS rule: $name"
                                        }
                                    }
                                }
                                RequireIdle
                                Git @('add','--all','--','.') | Out-Null
                                if ((UnityBusy) -or ((Fingerprint) -ne $before)) {
                                    throw 'Files changed while staging. Review staged changes manually before resuming.'
                                }
                                if (Git @('diff','--cached','--name-only')) {
                                    RequireIdle
                                    Git @('commit','-m',('Sunward autosync {0:yyyy-MM-dd HH:mm:ss zzz}' -f (Get-Date))) | Out-Null
                                    (Get-Date).ToString('o') | Set-Content $lastFile
                                    Report 'Created snapshot commit.'
                                }
                            }
                            # Explicit LFS upload also protects installations with custom hooks.
                            if ([int](Git @('rev-list','--count','refs/remotes/origin/sunward-minigame..HEAD')) -gt 0) {
                                if (UnityBusy) { throw 'Unity opened before upload; waiting for manual review.' }
                                RequireIdle
                                Git @('lfs','push','origin','HEAD') | Out-Null
                                if (UnityBusy) { throw 'Unity opened during LFS upload; retry after review.' }
                                RequireIdle
                                Git @('push','origin','HEAD:refs/heads/sunward-minigame') | Out-Null
                                Report 'Uploaded commits and LFS assets.'
                            } else { Report 'No outgoing commits.' }
                        }
                    }
                }
            }
        } catch {
            $_.Exception.Message | Set-Content -LiteralPath $pauseFile
            Report "PAUSED: $($_.Exception.Message)"
            exit 1
        }
        if ((Test-Path $pauseFile) -or (-not $Apply)) { break }
        if ($Watch) { Start-Sleep -Seconds $PollSeconds }
    } while ($Watch)
} finally {
    if ($held) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
