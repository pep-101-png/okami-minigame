#requires -Version 5.1
param([Parameter(Mandatory=$true)][string]$RunDirectory)
# Retry delivery of an existing report, never rerun Unity or mutate game source.
$ErrorActionPreference='Stop'
$AutomationState=Join-Path $env:LOCALAPPDATA 'SunwardUnityAutomation'
. (Join-Path $PSScriptRoot 'Common.ps1')
$Config=Get-Content (Join-Path $AutomationState 'config.json') -Raw | ConvertFrom-Json
$Config.PublishReports=$true
$tokens=$null; $errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'Run.ps1'),[ref]$tokens,[ref]$errors)
if ($errors.Count) { throw ($errors -join '; ') }
$function=$ast.Find({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'Publish-Feedback'},$true)
. ([scriptblock]::Create($function.Extent.Text))
$report=Get-Content (Join-Path $RunDirectory 'report.json') -Raw | ConvertFrom-Json
Publish-Feedback $RunDirectory $report
