param(
    [string]$RoslynDirectory = '',
    [string]$ProjectPath = (Join-Path $PSScriptRoot '../../Sunward-Unity')
)
$ErrorActionPreference = 'Stop'
# A syntax check only: no Unity assemblies are available in the cloud workspace.
# Supply a PowerShell 7 directory containing Microsoft's Roslyn DLLs.
if (-not $RoslynDirectory) { $RoslynDirectory = $PSHOME }
Add-Type -Path (Join-Path $RoslynDirectory 'Microsoft.CodeAnalysis.dll')
Add-Type -Path (Join-Path $RoslynDirectory 'Microsoft.CodeAnalysis.CSharp.dll')
$files = @(Get-ChildItem (Join-Path $ProjectPath 'Assets') -Recurse -Filter '*.cs')
$errors = @()
foreach ($mode in @('Editor','Player')) {
    $symbols = @('UNITY_6000_0_OR_NEWER','UNITY_6000_6_OR_NEWER','ENABLE_INPUT_SYSTEM')
    if ($mode -eq 'Editor') { $symbols += 'UNITY_EDITOR' }
    $parseOptions = [Microsoft.CodeAnalysis.CSharp.CSharpParseOptions]::Default.WithPreprocessorSymbols([string[]]$symbols)
    foreach ($file in $files) {
        $tree = [Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText(
            [IO.File]::ReadAllText($file.FullName), $parseOptions, $file.FullName)
        $errors += @($tree.GetDiagnostics() | Where-Object { $_.Severity.ToString() -eq 'Error' })
    }
}
if ($errors.Count) { throw ($errors -join [Environment]::NewLine) }
Write-Output "PASS: $($files.Count) C# files passed Editor and Player Roslyn syntax parsing. Unity API compilation and runtime behaviour remain unverified."
