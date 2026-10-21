#requires -Version 5.1
$ErrorActionPreference = 'Stop'
function Write-AutomationLog([string]$Message) {
    $line = '{0:o} {1}' -f (Get-Date),$Message
    Write-Host $line
    $path = Join-Path $AutomationState 'runner.log'
    if ((Test-Path $path) -and (Get-Item $path).Length -gt 5MB) { Move-Item $path "$path.previous" -Force }
    Add-Content -LiteralPath $path -Value $line
}
function ConvertTo-AutomationArgument([string]$Value) {
    '"' + (($Value -replace '(\\*)"','$1$1\"') -replace '(\\+)$','$1$1') + '"'
}
function Stop-OwnedProcess([Diagnostics.Process]$Process) {
    if ($Process.HasExited) { return }
    if ($env:OS -eq 'Windows_NT') {
        $info = New-Object Diagnostics.ProcessStartInfo
        $info.FileName = Join-Path $env:SystemRoot 'System32\taskkill.exe'
        $info.Arguments = "/PID $($Process.Id) /T /F"
        $info.UseShellExecute = $false; $info.CreateNoWindow = $true
        $killer = [Diagnostics.Process]::Start($info)
        try { if (-not $killer.WaitForExit(5000)) { $killer.Kill() } } finally { $killer.Dispose() }
    } else { $Process.Kill($true) }
    if (-not $Process.WaitForExit(5000)) { throw 'Owned process did not stop; inspect it manually before resuming.' }
}
function Invoke-AutomationProcess {
    param([string]$Executable,[string[]]$Arguments,[int]$TimeoutSeconds=120,
        [hashtable]$Environment=@{},[scriptblock]$CancelCheck,[string]$Stage='process',[string]$WorkingDirectory)
    Write-AutomationLog "START $Stage (limit=${TimeoutSeconds}s)"
    $info = New-Object Diagnostics.ProcessStartInfo
    if ($WorkingDirectory) { $info.WorkingDirectory=$WorkingDirectory }
    $info.FileName=$Executable; $info.Arguments=($Arguments | ForEach-Object { ConvertTo-AutomationArgument $_ }) -join ' '
    $info.UseShellExecute=$false; $info.CreateNoWindow=$true
    $info.RedirectStandardInput=$true; $info.RedirectStandardOutput=$true; $info.RedirectStandardError=$true
    $info.StandardOutputEncoding=New-Object Text.UTF8Encoding($false)
    $info.StandardErrorEncoding=New-Object Text.UTF8Encoding($false)
    $info.EnvironmentVariables['GIT_TERMINAL_PROMPT']='0'; $info.EnvironmentVariables['GCM_INTERACTIVE']='Never'
    $info.EnvironmentVariables['GH_PROMPT_DISABLED']='1'
    foreach ($key in $Environment.Keys) { $info.EnvironmentVariables[$key]=[string]$Environment[$key] }
    $process=New-Object Diagnostics.Process; $process.StartInfo=$info
    $timer=[Diagnostics.Stopwatch]::StartNew(); $next=10; $started=$false
    try {
        $started=$process.Start(); $process.StandardInput.Close()
        $out=$process.StandardOutput.ReadToEndAsync(); $err=$process.StandardError.ReadToEndAsync()
        while (-not ($process.HasExited -and $out.IsCompleted -and $err.IsCompleted)) {
            if ($CancelCheck) {
                $reason=& $CancelCheck $process.Id
                if ($reason) {
                    if ($reason -isnot [string]) { $reason='cancellation requested by callback' }
                    throw "Cancelled ${Stage}: $reason"
                }
            }
            if ($timer.Elapsed.TotalSeconds -ge $TimeoutSeconds) { throw "Timeout in $Stage after ${TimeoutSeconds}s." }
            if ($timer.Elapsed.TotalSeconds -ge $next) {
                Write-AutomationLog "WAIT $Stage elapsed=$([int]$timer.Elapsed.TotalSeconds)s PID=$($process.Id)"
                $next=$timer.Elapsed.TotalSeconds+10
            }
            Start-Sleep -Milliseconds 200
        }
        $result=[pscustomobject]@{ExitCode=$process.ExitCode; Stdout=$out.GetAwaiter().GetResult(); Stderr=$err.GetAwaiter().GetResult()}
        Write-AutomationLog "END $Stage exit=$($result.ExitCode) elapsed=$([int]$timer.Elapsed.TotalSeconds)s"
        return $result
    } catch {
        if ($started -and -not $process.HasExited) { Stop-OwnedProcess $process }
        Write-AutomationLog "ERROR $Stage $($_.Exception.Message)"
        throw
    } finally { $process.Dispose() }
}
function Invoke-ReadGit([string[]]$Arguments) {
    $r=Invoke-AutomationProcess -Executable $GitExecutable -Arguments (@('-c','gc.auto=0','-c','maintenance.auto=false','-C',$Repository)+$Arguments) -Stage ('git '+($Arguments -join ' '))
    if ($r.ExitCode -ne 0) { throw "Read-only Git failed: $($r.Stderr)" }
    $r.Stdout.TrimEnd([char[]]"`r`n")
}
function Get-AutomationProcessTable {
    # Query ancestry only when another Unity PID exists; never trust batchmode/name alone.
    Get-CimInstance -ClassName Win32_Process -Property ProcessId,ParentProcessId,CreationDate -OperationTimeoutSec 5 -ErrorAction Stop
}
function Get-OtherUnityProcess([int]$OwnedPid=0) {
    $candidates=@(Get-Process -Name Unity -ErrorAction SilentlyContinue | Where-Object { $_.Id -ne $OwnedPid })
    if ($OwnedPid -eq 0 -or $candidates.Count -eq 0) { return $candidates }
    try {
        $table=@{}
        foreach ($entry in Get-AutomationProcessTable) { $table[[int]$entry.ProcessId]=$entry }
    } catch {
        Write-AutomationLog "SAFETY: process ancestry unavailable; treating additional Unity PIDs as external. $($_.Exception.Message)"
        return $candidates
    }
    foreach ($candidate in $candidates) {
        $current=$table[[int]$candidate.Id]; $seen=@{}; $owned=$false
        while ($current -and -not $seen.ContainsKey([int]$current.ProcessId)) {
            $seen[[int]$current.ProcessId]=$true
            if ([int]$current.ProcessId -eq $OwnedPid) { $owned=$true; break }
            $parent=$table[[int]$current.ParentProcessId]
            # Missing/reused parents or cycles cannot establish ownership: fail closed.
            if (-not $parent -or -not $current.CreationDate -or -not $parent.CreationDate -or $parent.CreationDate -gt $current.CreationDate) { break }
            $current=$parent
        }
        if (-not $owned) { $candidate }
    }
}
function Test-OtherUnity([int]$OwnedPid=0) {
    return @(Get-OtherUnityProcess $OwnedPid).Count -gt 0
}
function Get-UnityCancellationReason([int]$OwnedPid) {
    $marker=Join-Path $AutomationState 'DISABLED'
    if (Test-Path -LiteralPath $marker) { return "stop marker present: $marker (owned PID=$OwnedPid)" }
    $others=@(Get-OtherUnityProcess $OwnedPid)
    if ($others.Count -gt 0) {
        return "Unity outside owned process tree: owned PID=$OwnedPid; other PIDs=$((@($others | ForEach-Object { $_.Id }) -join ','))"
    }
    return $null
}
function Test-OtherGit { return [bool](Get-Process -Name git,git-lfs -ErrorAction SilentlyContinue) }
function Test-RepositoryReady {
    if (Test-OtherUnity) { Write-AutomationLog 'WAIT: Unity is open; no validation started.'; return $false }
    if (Test-OtherGit) { Write-AutomationLog 'WAIT: Git is active.'; return $false }
    if (Test-Path (Join-Path $Repository 'Sunward-Unity/Temp/UnityLockfile')) { Write-AutomationLog 'WAIT: Unity project lock exists.'; return $false }
    if ((Invoke-ReadGit @('branch','--show-current')) -cne 'sunward-minigame') { throw 'Expected sunward-minigame; no branch switch attempted.' }
    $url=Invoke-ReadGit @('remote','get-url','origin')
    if ($url -notmatch '^(https://github\.com/pep-101-png/okami-minigame(?:\.git)?/?|git@github\.com:pep-101-png/okami-minigame(?:\.git)?)$') { throw 'Unexpected origin.' }
    foreach ($marker in @('index.lock','MERGE_HEAD','CHERRY_PICK_HEAD','REVERT_HEAD','rebase-merge','rebase-apply')) {
        $p=Invoke-ReadGit @('rev-parse','--git-path',$marker)
        if (-not [IO.Path]::IsPathRooted($p)) { $p=Join-Path $Repository $p }
        if (Test-Path $p) { Write-AutomationLog "WAIT: $marker exists; no cleanup attempted."; return $false }
    }
    if (Invoke-ReadGit @('status','--porcelain=v1','--untracked-files=all')) { Write-AutomationLog 'WAIT: repository has uncommitted work.'; return $false }
    $head=Invoke-ReadGit @('rev-parse','HEAD')
    if ($head -ne (Invoke-ReadGit @('rev-parse','refs/remotes/origin/sunward-minigame'))) { Write-AutomationLog 'WAIT: HEAD does not match the synced origin branch.'; return $false }
    return $true
}
function Find-UnityEditor([string]$ExplicitPath) {
    $candidates=@()
    if ($ExplicitPath) { $candidates+= $ExplicitPath }
    else {
        foreach ($base in @($env:ProgramFiles,${env:ProgramFiles(x86)})) {
            if ($base) { $candidates+=Join-Path $base 'Unity/Hub/Editor/6000.6.6f1/Editor/Unity.exe'; $candidates+=Join-Path $base 'Unity/Editor/Unity.exe' }
        }
        $command=Get-Command Unity.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($command) { $candidates+=$command.Source }
    }
    foreach ($p in $candidates) {
        if (Test-Path -LiteralPath $p -PathType Leaf) {
            $version=(Get-Item -LiteralPath $p).VersionInfo.ProductVersion
            if ($version -notmatch '^6000\.6\.6(?:f1|\.|\s|$)') { throw "Unity at $p reports $version, expected 6000.6.6f1. Supply the exact editor path." }
            return (Resolve-Path -LiteralPath $p).Path
        }
    }
    throw 'Unity 6000.6.6f1 not found. Set UnityEditor in config.json to its Unity.exe path (custom Hub locations are supported explicitly).'
}
function New-ProjectSnapshot([string]$Commit,[string]$RunDirectory) {
    $zip=Join-Path $RunDirectory 'project.zip'; $snapshot=Join-Path $RunDirectory 'project'
    $names=(Invoke-ReadGit @('ls-tree','-r','--name-only',"${Commit}:Sunward-Unity")) -split "`n"
    if ($names | Where-Object { $_ -match '^(Library|Temp|Logs|Obj|UserSettings|Builds?)/' }) { throw 'Generated Unity directories are tracked; review manually.' }
    Invoke-ReadGit @('archive','--format=zip',"--output=$zip","${Commit}:Sunward-Unity") | Out-Null
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($zip,$snapshot)
    # Immutable snapshot only. Never smudge/pull/checkout or write into the live repository.
    $envResult=Invoke-ReadGit @('lfs','env')
    $match=[regex]::Match($envResult,'(?m)^LocalMediaDir=(.+)\r?$')
    if (-not $match.Success) { throw 'Cannot locate the local LFS cache.' }
    $cache=$match.Groups[1].Value.Trim()
    foreach ($file in Get-ChildItem -LiteralPath $snapshot -File -Recurse) {
        if ($file.Length -gt 1024) { continue }
        $text=[IO.File]::ReadAllText($file.FullName)
        if ($text -notmatch '^version https://git-lfs.github.com/spec/v1\r?\n') { continue }
        $oid=[regex]::Match($text,'(?m)^oid sha256:([a-f0-9]{64})\r?$').Groups[1].Value
        $size=[regex]::Match($text,'(?m)^size (\d+)\r?$').Groups[1].Value
        if (-not $oid -or -not $size) { throw "Malformed LFS pointer: $($file.Name)" }
        $object=Join-Path $cache ($oid.Substring(0,2)+'/'+$oid.Substring(2,2)+'/'+$oid)
        if (-not (Test-Path $object)) { throw "Missing cached LFS object for $($file.Name). Let sync finish or retrieve it manually; live files were not touched." }
        if ((Get-Item $object).Length -ne [long]$size) { throw 'Cached LFS size mismatch.' }
        Copy-Item -LiteralPath $object -Destination $file.FullName
        if ((Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash -ine $oid) { throw 'Snapshot LFS SHA-256 mismatch.' }
    }
    Set-Content (Join-Path $snapshot '.sunward-automation-snapshot') $Commit
    Remove-Item -LiteralPath $zip # only this runner-created archive
    return $snapshot
}
function Get-ProtectedHashes([string]$Snapshot) {
    $result=@{}
    foreach ($relative in @('Assets/Sunward/Scenes','Assets/Sunward/Models','Assets/Sunward/Generated/Animations')) {
        foreach ($p in Get-ChildItem -LiteralPath (Join-Path $Snapshot $relative) -Recurse -File) {
            $result[$p.FullName.Substring($Snapshot.Length)]=(Get-FileHash -LiteralPath $p.FullName -Algorithm SHA256).Hash
        }
    }
    return $result
}
function Test-ProtectedHashes([hashtable]$Before,[string]$Snapshot) {
    $after=Get-ProtectedHashes $Snapshot
    if ($Before.Count -ne $after.Count) { return $false }
    foreach ($key in $Before.Keys) { if ($Before[$key] -ne $after[$key]) { return $false } }
    return $true
}

function Remove-OwnedSnapshot([string]$Snapshot,[string]$RunDirectory) {
    if ([IO.Path]::GetFullPath($Snapshot) -ne [IO.Path]::GetFullPath((Join-Path $RunDirectory 'project'))) { throw 'Refusing unexpected cleanup path.' }
    if (-not (Test-Path (Join-Path $Snapshot '.sunward-automation-snapshot'))) { throw 'Snapshot ownership marker missing; no cleanup performed.' }
    if ((Test-OtherUnity) -or ((Get-Item $Snapshot).Attributes -band [IO.FileAttributes]::ReparsePoint) -or
        (Get-ChildItem -LiteralPath $Snapshot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })) {
        Write-AutomationLog 'Snapshot retained: another Unity is open or a link/junction requires manual review.'; return
    }
    Write-AutomationLog 'Removing only the completed owned snapshot; reports remain.'
    Remove-Item -LiteralPath $Snapshot -Recurse -Force
}
