#requires -Version 5.1
# No Pester dependency. Loads AST fragments only: never starts sync or installs a task.
$ErrorActionPreference = 'Stop'
$syncDirectory = Split-Path -Parent $PSScriptRoot
$syncPath = Join-Path $syncDirectory 'Sync.ps1'
$syncAst = $null
foreach ($file in (Get-ChildItem -LiteralPath $syncDirectory -Filter '*.ps1' -Recurse)) {
    $tokens = $null
    $parseErrors = $null
    $ast = [Management.Automation.Language.Parser]::ParseFile($file.FullName, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count) { throw "Parse failed for $($file.Name): $($parseErrors -join '; ')" }
    if ($file.FullName -eq $syncPath) { $syncAst = $ast }
}
if (-not $syncAst) { throw 'Sync.ps1 AST was not loaded.' }
$helper = $syncAst.Find({ param($node)
    $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Invoke-SunwardGit'
}, $true)
if (-not $helper) { throw 'Native Git helper is missing.' }
# Recreate the case-insensitive function/alias shadow that caused the original overflow.
function Git { throw 'A function named Git intercepted the native invocation.' }
function git.exe { throw 'A function named git.exe intercepted the native invocation.' }
function Reject-GitAlias { throw 'An alias named git intercepted the native invocation.' }
Set-Alias -Name git -Value Reject-GitAlias -Scope Local
$Repository = Join-Path ([IO.Path]::GetTempPath()) ('Sunward Git test ' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $Repository | Out-Null
try {
    # Evaluate the exact application-resolution assignment used in each production script.
    foreach ($name in @('Sync.ps1','Install.ps1','Status.ps1')) {
        $tokens = $null; $parseErrors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile((Join-Path $syncDirectory $name), [ref]$tokens, [ref]$parseErrors)
        $assignment = $ast.Find({ param($node)
            $node -is [Management.Automation.Language.AssignmentStatementAst] -and
            $node.Left -is [Management.Automation.Language.VariableExpressionAst] -and
            $node.Left.VariablePath.UserPath -eq 'GitExecutable'
        }, $true)
        if (-not $assignment) { throw "$name does not resolve the native executable." }
        . ([scriptblock]::Create($assignment.Extent.Text))
        if (-not [IO.Path]::IsPathRooted($GitExecutable)) { throw "$name did not resolve an absolute executable path." }
        $version = & $GitExecutable --version
        if ($LASTEXITCODE -ne 0 -or $version -notmatch '^git version ') { throw "$name resolved the wrong command." }
        $bareGit = $ast.Find({ param($node)
            $node -is [Management.Automation.Language.CommandAst] -and
            $node.GetCommandName() -in @('git','git.exe')
        }, $true)
        if ($bareGit) { throw "$name contains an ambiguous Git invocation." }
    }
    . ([scriptblock]::Create($helper.Extent.Text))
    if ((Invoke-SunwardGit @('--version')) -notmatch '^git version ') { throw 'Helper did not invoke native Git.' }
    $value = Invoke-SunwardGit @('-c','sunward.testValue=argument with spaces','config','--get','sunward.testValue')
    if ($value -cne 'argument with spaces') { throw 'Argument boundaries were not preserved.' }
    $failedSafely = $false
    try { Invoke-SunwardGit @('__sunward_invalid_command__') | Out-Null }
    catch {
        if ($_.Exception.Message -notmatch 'git __sunward_invalid_command__ failed:') { throw }
        $failedSafely = $true
    }
    if (-not $failedSafely) { throw 'Native Git failures were silently accepted.' }
    if ($ErrorActionPreference -ne 'Stop') { throw 'Error handling preference was not preserved.' }
    Write-Host 'PASS: all scripts parse; native resolution bypasses Git functions/aliases; spaced arguments and Git failure handling work.'
} finally {
    Remove-Item -LiteralPath $Repository -Recurse -Force
    Remove-Item Alias:\git -ErrorAction SilentlyContinue
    Remove-Item Function:\Git -ErrorAction SilentlyContinue
    Remove-Item Function:\git.exe -ErrorAction SilentlyContinue
    Remove-Item Function:\Reject-GitAlias -ErrorAction SilentlyContinue
}
