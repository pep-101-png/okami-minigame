#requires -Version 5.1
function Get-VideoConfig([object]$InputConfig) {
    $defaults=[ordered]@{Enabled=$true;Fps=30;Width=960;Height=540;TimeoutSeconds=900;MaxFrames=2400;MaxFrameMegabytes=2048;PreferRecorder=$true;FFmpegPath='';FFprobePath='';Crf=24;KeepEncodedFrames=$false;MaxFeedbackMegabytes=80;MaxFrameArchiveMegabytes=20}
    $result=[ordered]@{}
    foreach ($key in $defaults.Keys) {
        $result[$key]=if ($InputConfig.Video -and $InputConfig.Video.PSObject.Properties.Name -contains $key) { $InputConfig.Video.$key } else { $defaults[$key] }
    }
    foreach ($key in @('Enabled','PreferRecorder','KeepEncodedFrames')) { if ($result[$key] -isnot [bool]) { throw "Video.$key must be a JSON boolean." } }
    foreach ($key in @('Fps','Width','Height','TimeoutSeconds','MaxFrames','MaxFrameMegabytes','Crf','MaxFeedbackMegabytes','MaxFrameArchiveMegabytes')) { if ($result[$key] -isnot [int] -and $result[$key] -isnot [long]) { throw "Video.$key must be an integer." } }
    if ($result.Fps -lt 12 -or $result.Fps -gt 60 -or $result.Width -lt 320 -or $result.Width -gt 1920 -or $result.Height -lt 180 -or $result.Height -gt 1080 -or $result.Width%2 -ne 0 -or $result.Height%2 -ne 0 -or $result.TimeoutSeconds -lt 30 -or $result.TimeoutSeconds -gt 3600 -or $result.MaxFrames -lt 1 -or $result.MaxFrames -gt 6000 -or $result.MaxFrameMegabytes -lt 1 -or $result.MaxFrameMegabytes -gt 4096 -or $result.Crf -lt 18 -or $result.Crf -gt 35 -or $result.MaxFeedbackMegabytes -lt 1 -or $result.MaxFeedbackMegabytes -gt 256 -or $result.MaxFrameArchiveMegabytes -lt 1 -or $result.MaxFrameArchiveMegabytes -gt 64) { throw 'Video configuration exceeds supported timing/resolution/storage limits.' }
    [pscustomobject]$result
}
function Resolve-VideoPath([string]$RunDirectory,[string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative)) { throw 'Video artifact paths must be run-relative.' }
    $root=[IO.Path]::GetFullPath($RunDirectory).TrimEnd([char[]]'\/')
    $path=[IO.Path]::GetFullPath((Join-Path $root $Relative))
    if (-not $path.StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Video path escapes the run directory.' }
    $ancestor=$path
    while ($ancestor -and $ancestor -ne $root) {
        if ((Test-Path -LiteralPath $ancestor) -and ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'Video paths cannot traverse symlinks/junctions.' }
        $ancestor=[IO.Path]::GetDirectoryName($ancestor)
    }
    return $path
}
function Find-VideoTool([string]$Explicit,[string]$Name,[string]$Sibling='') {
    if ($Explicit) { if (-not (Test-Path -LiteralPath $Explicit -PathType Leaf)) { return $null }; return (Resolve-Path -LiteralPath $Explicit).Path }
    $command=Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($command) { return $command.Source }
    if ($Sibling) {
        $extension=if ($env:OS -eq 'Windows_NT') { '.exe' } else { '' }
        $candidate=Join-Path (Split-Path $Sibling -Parent) ($Name+$extension)
        if (Test-Path $candidate) { return $candidate }
    }
    return $null
}
function Get-FrameInfo([string]$RunDirectory,[object]$Clip) {
    if ($Clip.name -notmatch '^[a-z0-9-]{1,80}$' -or $Clip.expectedFrames -lt 1 -or $Clip.expectedFrames -gt 6000 -or $Clip.frames -ne $Clip.expectedFrames -or $Clip.fps -lt 12 -or $Clip.fps -gt 60) { throw 'Incomplete or invalid capture frame metadata.' }
    $directory=Resolve-VideoPath $RunDirectory $Clip.framesDirectory
    $files=@(Get-ChildItem -LiteralPath $directory -Filter 'frame_*.png' -File | Sort-Object Name)
    if ($files.Count -ne $Clip.expectedFrames) { throw "Frame count mismatch for $($Clip.name)." }
    [long]$bytes=0
    for ($i=0;$i -lt $files.Count;$i++) {
        if ($files[$i].Name -cne ('frame_{0:D6}.png' -f $i)) { throw 'Missing/non-contiguous/duplicate frame numbers.' }
        $path=Resolve-VideoPath $RunDirectory ($Clip.framesDirectory+'/'+$files[$i].Name)
        $stream=[IO.File]::OpenRead($path)
        try { $header=New-Object byte[] 24; if ($stream.Read($header,0,24) -ne 24) { throw 'Truncated PNG frame.' } } finally { $stream.Dispose() }
        if ([BitConverter]::ToString($header[0..7]) -ne '89-50-4E-47-0D-0A-1A-0A' -or [Text.Encoding]::ASCII.GetString($header,12,4) -ne 'IHDR') { throw 'Invalid PNG frame header.' }
        $w=[byte[]]$header[16..19];$h=[byte[]]$header[20..23]
        if ([BitConverter]::IsLittleEndian) { [array]::Reverse($w);[array]::Reverse($h) }
        if ([BitConverter]::ToUInt32($w,0) -ne $Clip.width -or [BitConverter]::ToUInt32($h,0) -ne $Clip.height) { throw 'Frame resolution mismatch.' }
        $bytes+=$files[$i].Length
    }
    return [pscustomobject]@{Directory=$directory;Count=$files.Count;Bytes=$bytes;Duration=$files.Count/[double]$Clip.fps;Files=$files}
}
function Test-EncodedVideo([string]$Path,[object]$Clip,[string]$Probe) {
    if (-not $Probe) { throw 'ffprobe is required to verify encoded video.' }
    $r=Invoke-AutomationProcess -Executable $Probe -Arguments @('-v','error','-count_frames','-show_entries','stream=codec_type,codec_name,width,height,nb_read_frames,avg_frame_rate:format=duration,format_name','-of','json',$Path) -TimeoutSeconds 120 -Stage ('probe '+$Clip.name)
    if ($r.ExitCode -ne 0 -or -not [string]::IsNullOrWhiteSpace($r.Stderr)) { throw "Video probe failed: $($r.Stderr)" }
    $data=$r.Stdout | ConvertFrom-Json
    $streams=@($data.streams | Where-Object { $_.codec_type -eq 'video' })
    if ($streams.Count -ne 1) { throw 'Expected one video stream.' }
    $video=$streams[0]; $ratio=$video.avg_frame_rate -split '/'
    if ($ratio.Count -ne 2 -or [double]$ratio[1] -eq 0) { throw 'Invalid video frame rate.' }
    $fps=[double]$ratio[0]/[double]$ratio[1]
    $duration=[double]::Parse([string]$data.format.duration,[Globalization.CultureInfo]::InvariantCulture)
    $expected=[double]$Clip.expectedFrames/[double]$Clip.fps
    if ($video.width -ne $Clip.width -or $video.height -ne $Clip.height -or [int]$video.nb_read_frames -ne $Clip.expectedFrames -or [Math]::Abs($fps-$Clip.fps) -gt .02 -or [Math]::Abs($duration-$expected) -gt [Math]::Max(.12,2/[double]$Clip.fps) -or $data.format.format_name -notmatch 'mp4') { throw 'Encoded duration/frame-count/resolution/fps/container mismatch.' }
    return [pscustomobject]@{duration=$duration;frames=[int]$video.nb_read_frames;width=[int]$video.width;height=[int]$video.height;fps=$fps;codec=$video.codec_name;sha256=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
}
function Complete-GameplayVideos([string]$RunDirectory,[object]$Settings) {
    $capturePath=Join-Path $RunDirectory 'video-capture.json'
    $result=[ordered]@{schemaVersion=1;status='capture_unavailable';quality='unreviewed';scope='Frame/encoding checks do not establish correct movement, paw contact, blending or appearance.';clips=@();errors=@()}
    if (-not (Test-Path $capturePath)) { $result.errors+='Unity did not return a video manifest; inspect gameplay-video-editor.log.' }
    else {
        $capture=Get-Content $capturePath -Raw | ConvertFrom-Json
        $result.captureStatus=$capture.status
        $ffmpeg=Find-VideoTool $Settings.FFmpegPath 'ffmpeg'; $ffprobe=Find-VideoTool $Settings.FFprobePath 'ffprobe' $ffmpeg
        $result.ffmpegAvailable=[bool]$ffmpeg; $result.ffprobeAvailable=[bool]$ffprobe
        $directory=Join-Path $RunDirectory 'videos'; New-Item -ItemType Directory -Path $directory -Force | Out-Null
        [long]$fallbackBytes=0
        foreach ($clip in $capture.clips) {
            $entry=[ordered]@{name=$clip.name;status='failed';captureStatus=$clip.status;expectedFrames=$clip.expectedFrames;fps=$clip.fps;resolution=@($clip.width,$clip.height);quality='unreviewed';framesPreserved=$true;errors=@();sourceFrames=$clip.framesDirectory}
            try {
                $frames=Get-FrameInfo $RunDirectory $clip
                $entry.frames=$frames.Count; $entry.duration=$frames.Duration
                if ($clip.telemetryFile) { Copy-Item -LiteralPath (Resolve-VideoPath $RunDirectory $clip.telemetryFile) -Destination (Join-Path $directory ($clip.name+'-telemetry.csv')) }
                $destination=Join-Path $directory ($clip.name+'.mp4')
                $encoded=$false
                if (Test-Path $destination) { $entry.probe=Test-EncodedVideo $destination $clip $ffprobe; $encoded=$true; $entry.encoder='existing_verified' }
                if (-not $encoded -and $clip.recorderCandidate) {
                    $candidate=Resolve-VideoPath $RunDirectory $clip.recorderCandidate
                    if ((Test-Path $candidate) -and $ffprobe) {
                        try { $entry.probe=Test-EncodedVideo $candidate $clip $ffprobe; Copy-Item -LiteralPath $candidate -Destination $destination; $encoded=$true; $entry.encoder='unity_recorder' }
                        catch { $entry.errors+='Recorder candidate rejected: '+$_.Exception.Message }
                    }
                }
                if (-not $encoded -and $ffmpeg) {
                    $temporary=Join-Path $directory ($clip.name+'-partial-'+[Guid]::NewGuid().ToString('N')+'.mp4')
                    $r=Invoke-AutomationProcess -Executable $ffmpeg -Arguments @('-hide_banner','-loglevel','error','-n','-framerate',[string]$clip.fps,'-start_number','0','-i',(Join-Path $frames.Directory 'frame_%06d.png'),'-frames:v',[string]$frames.Count,'-c:v','libx264','-preset','veryfast','-crf',[string]$Settings.Crf,'-maxrate','2500k','-bufsize','5000k','-pix_fmt','yuv420p','-threads','2','-an','-movflags','+faststart',$temporary) -TimeoutSeconds 300 -Stage ('encode '+$clip.name)
                    if ($r.ExitCode -ne 0) { throw "FFmpeg encoding failed: $($r.Stderr)" }
                    if ($ffprobe) { $entry.probe=Test-EncodedVideo $temporary $clip $ffprobe; $encoded=$true; $entry.encoder='ffmpeg_libx264' }
                    Move-Item -LiteralPath $temporary -Destination $destination
                    if (-not $ffprobe) { $entry.status='mp4_unverified_missing_ffprobe'; $entry.errors+='ffprobe unavailable; frames preserved and MP4 not claimed verified.' }
                }
                if ($encoded) {
                    $entry.status='encoded_verified_unreviewed';$entry.file='videos/'+$clip.name+'.mp4'
                    if ($ffmpeg) {
                        $sheet=Join-Path $directory ($clip.name+'-contact.png'); $stride=[Math]::Max(1,[int][Math]::Floor($frames.Count/12))
                        if (-not (Test-Path $sheet)) {
                            $filter='select=not(mod(n\,'+$stride+')),scale=320:-2,tile=4x3'
                            $r=Invoke-AutomationProcess -Executable $ffmpeg -Arguments @('-hide_banner','-loglevel','error','-n','-i',$destination,'-vf',$filter,'-frames:v','1','-threads','1',$sheet) -TimeoutSeconds 60 -Stage ('contact sheet '+$clip.name)
                            if ($r.ExitCode -ne 0) { $entry.errors+='Contact sheet unavailable: '+$r.Stderr }
                        }
                        if (Test-Path $sheet) { $entry.contactSheet='videos/'+$clip.name+'-contact.png';$entry.contactStride=$stride }
                    }
                    $marker=Join-Path $frames.Directory '.sunward-owned-frames'
                    if (-not $Settings.KeepEncodedFrames -and (Test-Path $marker) -and (Get-Content $marker -Raw).Trim() -ceq $clip.name) {
                        foreach ($file in $frames.Files) { Remove-Item -LiteralPath $file.FullName }
                        $entry.framesPreserved=$false
                    }
                } else {
                    if ($entry.status -eq 'failed') { $entry.status=if ($ffmpeg) { 'encoding_unverified' } else { 'frames_only_missing_ffmpeg' } }
                    if (-not $ffmpeg) { $entry.errors+='FFmpeg unavailable and no verified Recorder MP4; numbered frames retained.' }
                    if (Test-Path $destination) { $entry.file='videos/'+$clip.name+'.mp4' }
                    if ($frames.Bytes -le $Settings.MaxFrameArchiveMegabytes*1MB -and $fallbackBytes+$frames.Bytes -le $Settings.MaxFeedbackMegabytes*1MB) {
                        Add-Type -AssemblyName System.IO.Compression.FileSystem
                        $archive=Join-Path $directory ($clip.name+'-frames.zip')
                        if (-not (Test-Path $archive)) { [IO.Compression.ZipFile]::CreateFromDirectory($frames.Directory,$archive) }
                        $entry.frameArchive='videos/'+$clip.name+'-frames.zip';$fallbackBytes+=(Get-Item $archive).Length
                    } else { $entry.errors+='Frame archive exceeds upload budget; full numbered frames remain local.' }
                }
            } catch { $entry.errors+=$_.Exception.Message; Write-AutomationLog "VIDEO ERROR $($clip.name): $($_.Exception.Message)" }
            $result.clips+= [pscustomobject]$entry
        }
        $verified=@($result.clips | Where-Object { $_.status -eq 'encoded_verified_unreviewed' })
        $result.status=if ($result.clips.Count -gt 0 -and $verified.Count -eq $result.clips.Count -and $capture.status -eq 'frames_captured_unreviewed') { 'encoded_verified_unreviewed' } elseif ($verified.Count -gt 0) { 'partial_video_or_action_coverage' } else { 'frames_only_or_capture_failed' }
        if ($capture.error) { $result.errors+=$capture.error }
    }
    $result | ConvertTo-Json -Depth 12 | Set-Content (Join-Path $RunDirectory 'video-report.json') -Encoding UTF8
    return [pscustomobject]$result
}
function Copy-VideoFeedback([string]$RunDirectory,[string]$Payload,[object]$Settings) {
    $directory=Join-Path $RunDirectory 'videos'
    if (-not (Test-Path $directory)) { return }
    $target=Join-Path $Payload 'videos';New-Item -ItemType Directory -Path $target -Force | Out-Null
    [long]$used=0; $delivery=@()
    foreach ($file in Get-ChildItem -LiteralPath $directory -File | Where-Object { $_.Extension -in @('.mp4','.png','.csv','.zip') -and $_.Name -notlike '*-partial-*' } | Sort-Object Name) {
        $path=Resolve-VideoPath $RunDirectory ('videos/'+$file.Name)
        $status=if ($used+$file.Length -le $Settings.MaxFeedbackMegabytes*1MB) { 'included' } else { 'not_uploaded_budget_full_local_copy_retained' }
        if ($status -eq 'included') { Copy-Item -LiteralPath $path -Destination $target; $used+=$file.Length }
        $delivery+=@{name=$file.Name;bytes=$file.Length;status=$status}
    }
    @{bytes=$used;limitMegabytes=$Settings.MaxFeedbackMegabytes;files=$delivery} | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $Payload 'video-delivery.json') -Encoding UTF8
}
function Get-VideoFingerprint([string]$Commit,[object]$Settings) {
    $tree=Invoke-ReadGit @('rev-parse',"${Commit}:Sunward-Unity")
    $bytes=[Text.Encoding]::UTF8.GetBytes('protocol=1;'+$tree+';'+($Settings | ConvertTo-Json -Compress))
    $sha=[Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant() } finally { $sha.Dispose() }
}

function Test-VideoCache([object]$Cached,[string]$Fingerprint) {
    if (-not $Cached -or $Cached.fingerprint -ne $Fingerprint -or $Cached.status -ne 'encoded_verified_unreviewed') { return $false }
    $path=Join-Path $Cached.runDirectory 'video-report.json'
    if (-not (Test-Path $path)) { return $false }
    try {
        $report=Get-Content $path -Raw | ConvertFrom-Json
        if ($report.status -ne 'encoded_verified_unreviewed' -or @($report.clips).Count -eq 0) { return $false }
        foreach ($clip in $report.clips) {
            if (-not $clip.file -or -not (Test-Path -LiteralPath (Resolve-VideoPath $Cached.runDirectory $clip.file))) { return $false }
        }
        return $true
    } catch { return $false }
}
