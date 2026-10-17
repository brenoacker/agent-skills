<#
.SYNOPSIS
    Installs agent skills into Antigravity, Claude Code, or Codex.
.PARAMETER Target
    The target AI agent: 'antigravity', 'claude', 'codex', or 'all'.
.PARAMETER Scope
    Installation scope: 'global' (default) or 'project'.
.PARAMETER DestinationOverride
    Custom target directory (primarily for testing and custom paths).
.PARAMETER Skills
    Optional list of specific skill names to install. If omitted, installs all skills.
#>
param (
    [Parameter(Mandatory = $true)]
    [string]$Target,

    [Parameter(Mandatory = $false)]
    [ValidateSet("global", "project", "test")]
    [string]$Scope = "global",

    [Parameter(Mandatory = $false)]
    [string]$DestinationOverride = "",

    [Parameter(Mandatory = $false)]
    [string[]]$Skills = @()
)

$ValidTargets = @("antigravity", "claude", "codex", "all")
if ($ValidTargets -notcontains $Target.ToLower()) {
    Write-Error "Invalid target '$Target'. Expected one of: $($ValidTargets -join ', ')."
    Write-Host "Usage: .\scripts\install.ps1 -Target [antigravity|claude|codex|all] [-Scope global|project]"
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$SourceSkillsDir = Join-Path $RepoRoot "skills"

if (-not (Test-Path $SourceSkillsDir)) {
    Write-Error "Source skills directory not found at $SourceSkillsDir"
    exit 1
}

function Get-TargetDirectory([string]$AgentTarget) {
    if ($DestinationOverride) {
        if ($Target.ToLower() -eq "all") {
            return Join-Path $DestinationOverride $AgentTarget
        }
        return $DestinationOverride
    }

    $HomeDir = if ($env:USERPROFILE) { $env:USERPROFILE } else { $env:HOME }
    
    switch ($AgentTarget.ToLower()) {
        "antigravity" {
            if ($Scope -eq "project") { return Join-Path (Get-Location) ".agents\skills" }
            return Join-Path $HomeDir ".gemini\antigravity\skills"
        }
        "claude" {
            if ($Scope -eq "project") { return Join-Path (Get-Location) ".claude\skills" }
            return Join-Path $HomeDir ".claude\skills"
        }
        "codex" {
            if ($Scope -eq "project") { return Join-Path (Get-Location) ".codex\skills" }
            return Join-Path $HomeDir ".codex\skills"
        }
    }
}

function Copy-SkillsTo([string]$DestDir) {
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    }

    $SkillFolders = Get-ChildItem -Path $SourceSkillsDir -Directory
    if ($Skills.Count -gt 0) {
        $SkillFolders = $SkillFolders | Where-Object { $Skills -contains $_.Name }
    }

    foreach ($folder in $SkillFolders) {
        $targetFolder = Join-Path $DestDir $folder.Name
        Copy-Item -Path $folder.FullName -Destination $targetFolder -Recurse -Force
        Write-Host "Installed skill '$($folder.Name)' -> $targetFolder"
    }
}

$TargetsToProcess = @()
if ($Target.ToLower() -eq "all") {
    $TargetsToProcess = @("antigravity", "claude", "codex")
} else {
    $TargetsToProcess = @($Target.ToLower())
}

foreach ($t in $TargetsToProcess) {
    $dest = Get-TargetDirectory $t
    Write-Host "Installing skills for target: $t into $dest..."
    Copy-SkillsTo $dest
}

Write-Host "Skills installation completed successfully."
exit 0
