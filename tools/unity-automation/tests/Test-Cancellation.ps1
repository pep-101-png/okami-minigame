#requires -Version 5.1
# No Unity, scheduled tasks, GitHub, or real project files are used.
$ErrorActionPreference='Stop'
$tools=Split-Path $PSScriptRoot -Parent
$AutomationState=Join-Path ([IO.Path]::GetTempPath()) ('sunward-cancel-test-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $AutomationState | Out-Null
. (Join-Path $tools 'Common.ps1')
function Assert([bool]$Condition,[string]$Message) { if (-not $Condition) { throw "ASSERT: $Message" } }
$nativeShell=(Get-Process -Id $PID).Path
$baseTime=(Get-Date).AddMinutes(-5)
function Record([int]$Id,[int]$Parent,[int]$Age) { [pscustomobject]@{ProcessId=$Id;ParentProcessId=$Parent;CreationDate=$baseTime.AddSeconds($Age)} }
$script:unity=@();$script:processTable=@();$script:queryCount=0;$script:queryFails=$false
$externalProcess=$null
# Mock only enumeration; Invoke-AutomationProcess still launches and watches real children.
function Get-Process { [CmdletBinding()] param([string]$Name) if ($Name -ne 'Unity') { throw 'Unexpected process enumeration' }; $script:unity }
function Get-AutomationProcessTable {
    $script:queryCount++
    if ($script:queryFails) { throw 'simulated CIM failure' }
    $script:processTable
}
function Unity([int]$Id) { [pscustomobject]@{Id=$Id} }
try {
    foreach ($file in Get-ChildItem $tools -Filter '*.ps1' -Recurse) {
        $tokens=$null;$errors=$null
        [void][Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$errors)
        Assert ($errors.Count -eq 0) "PowerShell parse: $($file.Name) $errors"
    }
    Assert (-not (Test-OtherUnity)) 'no Unity must be safe'
    $script:unity=@(Unity 100)
    Assert (-not (Test-OtherUnity 100)) 'owned editor must be excluded'
    Assert ($script:queryCount -eq 0) 'owned-only check should not query CIM'
    Assert (Test-OtherUnity) 'prelaunch must block any Unity, including a prior runner'
    $script:unity=@(Unity 100;Unity 101;Unity 103)
    $script:processTable=@((Record 100 50 0);(Record 101 100 1);(Record 102 101 2);(Record 103 102 3))
    # The old direct-PID filter falsely flagged 101 and 103.
    Assert (@($script:unity | Where-Object { $_.Id -ne 100 }).Count -eq 2) 'reproduce legacy worker false positive'
    foreach ($cycle in 1..3) { Assert (-not (Test-OtherUnity 100)) 'owned import workers/grandchildren must not cancel' }
    Assert (-not (Get-UnityCancellationReason 100)) 'owned tree has no cancellation reason'
    $script:unity+=Unity 200
    $script:processTable+=Record 200 50 4
    Assert (Test-OtherUnity 100) 'separate editor/competing batch must still cancel'
    Assert ((Get-UnityCancellationReason 100) -match 'owned PID=100; other PIDs=200') 'external reason/PIDs missing'
    $script:unity=@(Unity 101);$script:processTable=@((Record 101 999 1))
    Assert (Test-OtherUnity 100) 'unknown ancestry must fail closed'
    $script:processTable=@((Record 100 50 10);(Record 101 100 1))
    Assert (Test-OtherUnity 100) 'reused parent PID must not establish ownership'
    $script:processTable=@((Record 101 102 1);(Record 102 101 1))
    Assert (Test-OtherUnity 100) 'ancestry cycle must terminate and fail closed'
    $script:queryFails=$true
    Assert (Test-OtherUnity 100) 'CIM failure must fail closed'
    $script:queryFails=$false
    $marker=Join-Path $AutomationState 'DISABLED'
    Set-Content $marker 'test stop request'
    $queries=$script:queryCount
    Assert ((Get-UnityCancellationReason 100) -match 'stop marker present:') 'marker reason missing'
    Assert ($script:queryCount -eq $queries) 'stop marker should take precedence without CIM'
    Assert (Test-Path $marker) 'watchdog must not remove stop marker'
    Remove-Item $marker
    $script:unity=@()
    Assert (-not (Get-UnityCancellationReason 100)) 'removed marker must stop cancelling'
    # Native process watchdog: pass its exact PID through the same production callback.
    $script:callbackCalls=0
    $safe={param($OwnedPid)
        $script:callbackCalls++
        $script:unity=@(Unity $OwnedPid;Unity ($OwnedPid+100000))
        $script:processTable=@((Record $OwnedPid 0 0);(Record ($OwnedPid+100000) $OwnedPid 1))
        Get-UnityCancellationReason $OwnedPid
    }
    $r=Invoke-AutomationProcess $nativeShell @('-NoProfile','-Command','Start-Sleep -Milliseconds 800') -CancelCheck $safe -TimeoutSeconds 15 -Stage 'owned-tree regression'
    Assert ($r.ExitCode -eq 0 -and $script:callbackCalls -gt 1) 'real owned child must complete repeated watchdog polls'
    $externalProcess=Start-Process -FilePath $nativeShell -ArgumentList @('-NoProfile','-Command','Start-Sleep -Seconds 20') -PassThru
    foreach ($cause in @('editor','marker')) {
        $cancel={param($OwnedPid)
            if ($cause -eq 'marker') { Set-Content $marker 'stop during child execution' }
            $script:unity=@(Unity $OwnedPid;Unity $externalProcess.Id)
            $script:processTable=@((Record $OwnedPid 0 0);(Record $externalProcess.Id 50 1))
            Get-UnityCancellationReason $OwnedPid
        }
        $message=''
        try { Invoke-AutomationProcess $nativeShell @('-NoProfile','-Command','Start-Sleep -Seconds 20') -CancelCheck $cancel -TimeoutSeconds 10 -Stage $cause | Out-Null } catch { $message=$_.Exception.Message }
        Assert ($message -match 'Cancelled') 'real child cancellation not honored'
        Assert (-not $externalProcess.HasExited) 'cancellation stopped the unrelated native process'
        if ($cause -eq 'marker') { Assert ($message -match 'stop marker present:') 'real marker cancellation misclassified' }
        else { Assert ($message -match 'Unity outside owned process tree:') 'real external cancellation misclassified' }
    }
    $run=Get-Content (Join-Path $tools 'Run.ps1') -Raw
    Assert (([regex]::Matches($run,'Get-UnityCancellationReason \$OwnedPid')).Count -eq 2) 'validation/capture/build and Test Framework must both use the shared reason callback'
    Write-Host 'PASS: owned Unity/worker/descendant vs separate editor, fail-closed ancestry, marker handling, reason logging and real native-process watchdog completion/cancellation.'
} finally {
    if ($externalProcess) { if (-not $externalProcess.HasExited) { $externalProcess.Kill();[void]$externalProcess.WaitForExit(5000) };$externalProcess.Dispose() }
    Remove-Item -LiteralPath $AutomationState -Recurse -Force
}
