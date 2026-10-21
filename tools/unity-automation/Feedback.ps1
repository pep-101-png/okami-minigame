#requires -Version 5.1
# Delivery is opt-in. Never launches Unity, changes task state, or stores credentials.
function Get-FeedbackOptions {
    $dispatch=$false
    if ($Config.PSObject.Properties.Name -contains 'DispatchRepair') {
        if ($Config.DispatchRepair -isnot [bool]) { throw 'DispatchRepair must be a JSON boolean.' }
        $dispatch=$Config.DispatchRepair
    }
    [pscustomobject]@{Publish=[bool]$Config.PublishReports;Dispatch=$dispatch}
}
function Copy-SanitizedFeedbackText([string]$Source,[string]$Destination) {
    $length=(Get-Item -LiteralPath $Source).Length
    if ([IO.Path]::GetExtension($Source) -eq '.log' -and $length -gt 4MB) {
        $stream=[IO.File]::OpenRead($Source)
        try {
            $head=New-Object byte[] (512KB);$tail=New-Object byte[] (3MB)
            [void]$stream.Read($head,0,$head.Length);[void]$stream.Seek(-$tail.Length,[IO.SeekOrigin]::End);[void]$stream.Read($tail,0,$tail.Length)
            $text=[Text.Encoding]::UTF8.GetString($head)+"`n[TRUNCATED: $length bytes; full log retained locally; head and tail follow]`n"+[Text.Encoding]::UTF8.GetString($tail)
        } finally {$stream.Dispose()}
    } else {
        if ($length -gt 16MB) { throw 'Feedback structured text exceeds 16 MiB; retain locally for diagnosis.' }
        $text=[IO.File]::ReadAllText($Source)
    }
    # Defense in depth. Never collect configs, credentials, environments, save-data or raw process command lines.
    $text=[regex]::Replace($text,'(?i)\b(?:gh[pousr]_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+|sk-[A-Za-z0-9_-]{12,})\b','[REDACTED_TOKEN]')
    $text=[regex]::Replace($text,'(?im)(authorization\s*[:=]\s*(?:bearer\s+|token\s+)?)[^\r\n,}"]+','$1[REDACTED]')
    $text=[regex]::Replace($text,'(?im)((?:password|access[_-]?token|api[_-]?key|client[_-]?secret)\s*["'']?\s*[:=]\s*["'']?)[^\r\n"'',} ]+','$1[REDACTED]')
    [IO.File]::WriteAllText($Destination,$text,(New-Object Text.UTF8Encoding($false)))
}
function Invoke-FeedbackPublish([string]$RunDirectory,[object]$Report) {
    $options=Get-FeedbackOptions
    if (-not $options.Publish) { Write-AutomationLog 'UPLOAD skipped: PublishReports=false';return $false }
    if ($Report.commit -notmatch '^[0-9a-f]{40}$' -or $Report.runId -notmatch '^\d{8}T\d{9}Z-[0-9a-f]{6}$') { throw 'Invalid immutable feedback identity.' }
    $gh=(Get-Command gh -CommandType Application -ErrorAction Stop | Select-Object -First 1).Source
    $name=$Report.commit+'-'+$Report.runId
    $deliveryPath=Join-Path $RunDirectory 'delivery.json'
    $delivery=if (Test-Path $deliveryPath) { Get-Content $deliveryPath -Raw | ConvertFrom-Json } else { [pscustomobject]@{attempts=0;uploaded=$false;dispatched=$false;lastError='';nextRetryUtc='';complete=$false} }
    if ($delivery.uploaded -and ($delivery.dispatched -or -not $options.Dispatch)) { return $true }
    $delivery.attempts++
    try {
        $archive=Join-Path $RunDirectory ($name+'.zip');$summary=Join-Path $RunDirectory ($name+'-report.json')
        if (-not (Test-Path $archive)) {
            $payload=Join-Path $RunDirectory ('feedback-'+[guid]::NewGuid().ToString('N'))
            New-Item -ItemType Directory $payload | Out-Null
            try {
                # Explicit allowlist: never upload arbitrary root JSON (e.g. local configs).
                $allowed=@('report.json','compilation.json','validation.json','capture.json','gameplay-capture.json','video-capture.json','video-report.json','video-reuse.json','build-summary.json','process-diagnostics.json')
                foreach ($file in Get-ChildItem -LiteralPath $RunDirectory -File) {
                    if ($file.Name -notin $allowed -and $file.Name -notlike '*-editor.log' -and $file.Name -ne 'runner-stage.log' -and $file.Name -notlike '*-results.xml') { continue }
                    $source=Resolve-VideoPath $RunDirectory $file.Name
                    Copy-SanitizedFeedbackText $source (Join-Path $payload $file.Name)
                }
                $screens=Join-Path $RunDirectory 'screenshots'
                if (Test-Path $screens) {
                    $target=Join-Path $payload 'screenshots';New-Item -ItemType Directory $target | Out-Null
                    [long]$size=0
                    foreach ($file in Get-ChildItem $screens -File -Filter '*.png') {
                        $size+=$file.Length;if ($size -gt 20MB) { throw 'Screenshot upload budget exceeds 20 MiB.' }
                        Copy-Item -LiteralPath (Resolve-VideoPath $RunDirectory ('screenshots/'+$file.Name)) -Destination $target
                    }
                }
                Copy-VideoFeedback $RunDirectory $payload (Get-VideoConfig $Config)
                [long]$bytes=0;foreach ($file in Get-ChildItem $payload -Recurse -File) {$bytes+=$file.Length}
                if ($bytes -gt 140MB) { throw 'Feedback bundle exceeds 140 MiB; retained locally.' }
                Add-Type -AssemblyName System.IO.Compression.FileSystem
                [IO.Compression.ZipFile]::CreateFromDirectory($payload,$archive)
            } finally { if (Test-Path $payload) { Remove-Item -LiteralPath $payload -Recurse -Force } }
        }
        if (-not (Test-Path $summary)) { Copy-SanitizedFeedbackText (Join-Path $RunDirectory 'report.json') $summary }
        $r=Invoke-AutomationProcess $gh @('release','view','sunward-unity-feedback','--repo','pep-101-png/okami-minigame','--json','assets') -Stage 'check reporting release'
        if ($r.ExitCode -ne 0) { throw 'Reporting prerelease missing or inaccessible. Run Configure-Feedback.ps1 after gh auth login.' }
        $assets=@(($r.Stdout | ConvertFrom-Json).assets)
        foreach ($file in @($archive,$summary)) {
            $existing=@($assets | Where-Object {$_.name -eq [IO.Path]::GetFileName($file)})
            if ($existing.Count) {
                if ($existing[0].PSObject.Properties.Name -contains 'size' -and $existing[0].size -ne (Get-Item $file).Length) { throw 'Existing immutable release asset has conflicting size.' }
                continue
            }
            $r=Invoke-AutomationProcess $gh @('release','upload','sunward-unity-feedback',$file,'--repo','pep-101-png/okami-minigame') -TimeoutSeconds 300 -Stage 'upload feedback'
            if ($r.ExitCode -ne 0) { throw "Feedback upload failed: $($r.Stderr)" }
        }
        $delivery.uploaded=$true
        if ($options.Dispatch -and -not $delivery.dispatched) {
            $request=Join-Path $RunDirectory 'dispatch-request.json'
            $requestBody=@{event_type='sunward_unity_feedback';client_payload=@{commit=$Report.commit;run_id=$Report.runId;asset=($name+'.zip');sha256=(Get-FileHash $archive -Algorithm SHA256).Hash.ToLowerInvariant()}} | ConvertTo-Json -Depth 5
            [IO.File]::WriteAllText($request,$requestBody,(New-Object Text.UTF8Encoding($false)))
            $r=Invoke-AutomationProcess $gh @('api','--method','POST','repos/pep-101-png/okami-minigame/dispatches','--input',$request) -TimeoutSeconds 60 -Stage 'dispatch Codex feedback repair'
            if ($r.ExitCode -ne 0) { throw "Feedback uploaded; repair dispatch failed: $($r.Stderr)" }
            $delivery.dispatched=$true
        }
        $delivery.complete=$true;$delivery.lastError='';$delivery.nextRetryUtc=''
        Write-AutomationLog "FEEDBACK delivered: $name dispatched=$($delivery.dispatched)"
        return $true
    } catch {
        $delivery.lastError=$_.Exception.Message
        $delay=[Math]::Min(3600,60*[Math]::Pow(2,[Math]::Min(6,$delivery.attempts-1)))
        $delivery.nextRetryUtc=(Get-Date).ToUniversalTime().AddSeconds($delay).ToString('o')
        throw
    } finally { $delivery | ConvertTo-Json | Set-Content $deliveryPath -Encoding UTF8 }
}
function Invoke-FeedbackOutbox {
    if (-not (Get-FeedbackOptions).Publish) { return }
    $runs=Join-Path $AutomationState 'runs'
    if (-not (Test-Path $runs)) { return }
    $sent=0;$options=Get-FeedbackOptions
    foreach ($run in Get-ChildItem $runs -Directory | Sort-Object Name -Descending | Select-Object -First 100) {
        $path=Join-Path $run.FullName 'delivery.json'
        if (-not (Test-Path $path)) { continue }
        $delivery=Get-Content $path -Raw | ConvertFrom-Json
        if (($delivery.complete -and ($delivery.dispatched -or -not $options.Dispatch)) -or $delivery.attempts -ge 10 -or ($delivery.nextRetryUtc -and [datetime]$delivery.nextRetryUtc -gt (Get-Date).ToUniversalTime())) { continue }
        if ($sent++ -ge 3) { break }
        try { $report=Get-Content (Join-Path $run.FullName 'report.json') -Raw | ConvertFrom-Json;[void](Invoke-FeedbackPublish $run.FullName $report) }
        catch { Write-AutomationLog "OUTBOX pending: $($_.Exception.Message)" }
    }
}
