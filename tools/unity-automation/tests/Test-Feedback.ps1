#requires -Version 5.1
$ErrorActionPreference='Stop'
$tools=Split-Path $PSScriptRoot -Parent
$AutomationState=Join-Path ([IO.Path]::GetTempPath()) ('sunward-feedback-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $AutomationState | Out-Null
. (Join-Path $tools 'Common.ps1')
. (Join-Path $tools 'Video.ps1')
. (Join-Path $tools 'Feedback.ps1')
function Assert([bool]$Value,[string]$Message) { if (-not $Value) { throw "ASSERT: $Message" } }
$Config=[pscustomobject]@{PublishReports=$true;DispatchRepair=$true;Video=[pscustomobject]@{Enabled=$false}}
$script:assets=@();$script:dispatches=0;$script:failUpload=$true;$script:uploads=0
function Get-Command { [CmdletBinding()] param([string]$Name,[string]$CommandType) if ($Name -ne 'gh') {throw 'Unexpected command lookup'};[pscustomobject]@{Source='fixture-gh'} }
function Invoke-AutomationProcess {
    param([string]$Executable,[string[]]$Arguments,[int]$TimeoutSeconds,[string]$Stage)
    if ($Arguments[0] -eq 'release' -and $Arguments[1] -eq 'view') {
        return [pscustomobject]@{ExitCode=0;Stdout=(@{assets=$script:assets}|ConvertTo-Json -Depth 5);Stderr=''}
    }
    if ($Arguments[0] -eq 'release' -and $Arguments[1] -eq 'upload') {
        $file=Get-Item $Arguments[3]
        if ($script:failUpload -and $file.Name -like '*-report.json') {return [pscustomobject]@{ExitCode=1;Stdout='';Stderr='synthetic upload outage'}}
        $script:uploads++
        $script:assets+=@{name=$file.Name;size=$file.Length}
        return [pscustomobject]@{ExitCode=0;Stdout='';Stderr=''}
    }
    if ($Arguments[0] -eq 'api') { $script:dispatches++;throw 'Subscription workflow must never dispatch the API repair receiver.' }
    throw "Unexpected publishing command: $Arguments"
}
try {
    $run=Join-Path $AutomationState 'runs/fixture';New-Item -ItemType Directory $run -Force | Out-Null
    $report=[pscustomobject]@{commit=('a'*40);runId='20261021T120000000Z-abcdef';status='deferred';errors=@('capture cancelled')}
    $report | ConvertTo-Json | Set-Content (Join-Path $run 'report.json')
    Set-Content (Join-Path $run 'capture-editor.log') 'API_KEY=secret123 authorization: Bearer hidden ghp_abcdefghijklmnop sk-abcdefghijklmnop'
    Set-Content (Join-Path $run 'config.json') 'DO_NOT_UPLOAD'
    Set-Content (Join-Path $run 'process-diagnostics.json') '{"reason":"parent_exited_or_missing"}'
    $failed=$false
    try { Invoke-FeedbackPublish $run $report | Out-Null } catch {$failed=$true}
    Assert $failed 'outage was not reported'
    $delivery=Get-Content (Join-Path $run 'delivery.json') -Raw | ConvertFrom-Json
    Assert (-not $delivery.uploaded -and -not $delivery.dispatched -and $delivery.attempts -eq 1) 'outbox lost partial progress'
    Assert ($script:uploads -eq 1) 'partial upload not preserved'
    $zip=Get-ChildItem $run -Filter '*.zip' | Select-Object -First 1
    $extract=Join-Path $AutomationState 'inspect';[IO.Compression.ZipFile]::ExtractToDirectory($zip.FullName,$extract)
    Assert (-not (Test-Path (Join-Path $extract 'config.json'))) 'credentials/config included in bundle'
    $text=Get-Content (Join-Path $extract 'capture-editor.log') -Raw
    Assert ($text -notmatch 'secret123|hidden|ghp_abc|sk-abc') 'known credential patterns were not redacted'
    Assert (Test-Path (Join-Path $extract 'process-diagnostics.json')) 'process diagnostics omitted'
    $script:failUpload=$false
    Invoke-FeedbackOutbox
    Assert ($script:dispatches -eq 0) 'outbox ignored retry backoff'
    $delivery.nextRetryUtc=(Get-Date).ToUniversalTime().AddSeconds(-1).ToString('o')
    $delivery | ConvertTo-Json | Set-Content (Join-Path $run 'delivery.json')
    Invoke-FeedbackOutbox
    Assert ($script:dispatches -eq 0 -and $script:uploads -eq 2) 'outbox duplicated uploads or failed retry'
    Assert (Invoke-FeedbackPublish $run $report) 'idempotent completion failed'
    Assert ($script:dispatches -eq 0 -and $script:uploads -eq 2) 'duplicate dispatch/upload'
    $large=Join-Path $AutomationState 'large.log'
    [IO.File]::WriteAllText($large,('A'*5MB)+' tail error API_KEY=hidden')
    $bounded=Join-Path $AutomationState 'bounded.log';Copy-SanitizedFeedbackText $large $bounded
    Assert ((Get-Item $bounded).Length -lt 4MB -and (Get-Content $bounded -Raw) -match 'TRUNCATED:') 'oversize log blocked all feedback instead of bounded head/tail'
    Assert ((Get-Content $bounded -Raw) -notmatch 'API_KEY=hidden') 'tail credential not redacted'
    $delivery=Get-Content (Join-Path $run 'delivery.json') -Raw | ConvertFrom-Json
    $delivery.complete=$false;$delivery.dispatched=$false;$delivery.attempts=10
    $delivery | ConvertTo-Json | Set-Content (Join-Path $run 'delivery.json')
    Invoke-FeedbackOutbox
    Assert ($script:dispatches -eq 0) 'outbox attempt cap ignored'
    $Config.PublishReports=$false
    Assert (-not (Invoke-FeedbackPublish $run $report)) 'publishing opt-out ignored'
    Write-Host 'PASS: deferred logs/diagnostics, allowlisted/redacted ZIP, immutable upload, subscription-only (zero API dispatch), retry outbox, deduplication and opt-out (GitHub mocked).'
} finally {Remove-Item -LiteralPath $AutomationState -Recurse -Force}
