# Jenkins Setup Script for Claude AI Agent Pipeline
# Usage: .\setup_jenkins.ps1 -JenkinsUser "priti123" -JenkinsPassword "Vivek@123"
#
# ClaudeApiKey is read from the CLAUDE_API_KEY environment variable.
# Set it before running:
#   $env:CLAUDE_API_KEY = "sk-ant-..."
#
# Or pass it directly:
#   .\setup_jenkins.ps1 -JenkinsUser "priti123" -JenkinsPassword "Vivek@123" -ClaudeApiKey "sk-ant-..."

param(
    [Parameter(Mandatory=$true)][string]$JenkinsUser,
    [Parameter(Mandatory=$true)][string]$JenkinsPassword,
    [string]$JenkinsUrl    = "http://localhost:8080",
    [string]$ClaudeApiKey  = $env:CLAUDE_API_KEY,
    [string]$JobName       = "Claude-AI-Code-Review",
    [string]$RepoPath      = "https://github.com/prtnayak62/bob-squad"
)

if (-not $ClaudeApiKey) {
    Write-Host "ERROR: Set CLAUDE_API_KEY environment variable or pass -ClaudeApiKey" -ForegroundColor Red
    Write-Host "  Example: `$env:CLAUDE_API_KEY = 'sk-ant-...'" -ForegroundColor Yellow
    exit 1
}

$ErrorActionPreference = "Stop"
$b64  = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${JenkinsUser}:${JenkinsPassword}"))
$base = @{ Authorization = "Basic $b64" }

# Helper: get crumb then call Jenkins
function Invoke-J {
    param([string]$Path, [string]$Method = "GET", [string]$Body = "", [string]$CT = "application/json")
    $uri = "$JenkinsUrl$Path"
    if ($Method -eq "GET") {
        return Invoke-RestMethod -Uri $uri -Headers $base -Method GET -UseBasicParsing
    }
    $h = $base.Clone()
    $h["Content-Type"] = $CT
    try {
        $cr = Invoke-RestMethod -Uri "$JenkinsUrl/crumbIssuer/api/json" -Headers $base -UseBasicParsing
        $h[$cr.crumbRequestField] = $cr.crumb
    } catch { }
    return Invoke-RestMethod -Uri $uri -Headers $h -Method $Method -Body $Body -UseBasicParsing
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Jenkins Claude AI Pipeline Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# ── Step 1: Verify Jenkins reachable ─────────────────────────────────────────
Write-Host ""
Write-Host "[1/5] Checking Jenkins connection..." -ForegroundColor Yellow
try {
    $info = Invoke-J "/api/json"
    Write-Host "      OK - Jenkins is running" -ForegroundColor Green
} catch {
    Write-Host "      FAIL - Cannot reach Jenkins at $JenkinsUrl" -ForegroundColor Red
    Write-Host "      Check: is Jenkins running? Are credentials correct?" -ForegroundColor Red
    exit 1
}

# ── Step 2: Check plugins ─────────────────────────────────────────────────────
Write-Host ""
Write-Host "[2/5] Checking required plugins..." -ForegroundColor Yellow
$needed = @("workflow-aggregator","git","htmlpublisher","pipeline-stage-view")
try {
    $pl = Invoke-J "/pluginManager/api/json?depth=1"
    foreach ($p in $needed) {
        if ($pl.plugins | Where-Object { $_.shortName -eq $p }) {
            Write-Host "      OK - $p" -ForegroundColor Green
        } else {
            Write-Host "      MISSING - $p  (install via Manage Jenkins > Plugins)" -ForegroundColor Red
        }
    }
} catch {
    Write-Host "      Could not check plugins - continuing anyway" -ForegroundColor Yellow
}

# ── Step 3: Create credential ─────────────────────────────────────────────────
Write-Host ""
Write-Host "[3/5] Creating credential 'claude-api-key'..." -ForegroundColor Yellow
$credXml = "<?xml version='1.1' encoding='UTF-8'?><org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl><scope>GLOBAL</scope><id>claude-api-key</id><description>Anthropic Auth Token IBM Gateway</description><secret>$ClaudeApiKey</secret></org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>"
try {
    Invoke-J "/credentials/store/system/domain/_/createCredentials" -Method "POST" -Body $credXml -CT "application/xml" | Out-Null
    Write-Host "      OK - Credential created" -ForegroundColor Green
} catch {
    $msg = $_.Exception.Message
    if ($msg -like "*409*" -or $msg -like "*already*") {
        Write-Host "      OK - Credential already exists" -ForegroundColor Green
    } else {
        Write-Host "      WARN - $msg" -ForegroundColor Yellow
        Write-Host "      -> Add manually: Manage Jenkins > Credentials > Global > Add Credentials" -ForegroundColor Yellow
        Write-Host "         Kind=Secret text | ID=claude-api-key | Secret=$ClaudeApiKey" -ForegroundColor Yellow
    }
}

# ── Step 4: Create pipeline job ───────────────────────────────────────────────
Write-Host ""
Write-Host "[4/5] Creating pipeline job '$JobName'..." -ForegroundColor Yellow
$jobXml = "<?xml version='1.1' encoding='UTF-8'?><flow-definition plugin='workflow-job'><description>Claude AI Agentic Code Review Pipeline</description><keepDependencies>false</keepDependencies><properties><hudson.model.ParametersDefinitionProperty><parameterDefinitions><hudson.model.ChoiceParameterDefinition><name>REVIEW_DEPTH</name><choices class='java.util.Arrays`$ArrayList'><a class='string-array'><string>STANDARD</string><string>QUICK</string><string>COMPREHENSIVE</string></a></choices><description>Review depth</description></hudson.model.ChoiceParameterDefinition><hudson.model.BooleanParameterDefinition><name>SKIP_QUALITY_GATE</name><defaultValue>false</defaultValue><description>Skip quality gate</description></hudson.model.BooleanParameterDefinition><hudson.model.StringParameterDefinition><name>CUSTOM_THRESHOLD</name><defaultValue></defaultValue><description>Override threshold 0-100</description></hudson.model.StringParameterDefinition></parameterDefinitions></hudson.model.ParametersDefinitionProperty></properties><definition class='org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition'><scm class='hudson.plugins.git.GitSCM'><configVersion>2</configVersion><userRemoteConfigs><hudson.plugins.git.UserRemoteConfig><url>file:///$RepoPath</url></hudson.plugins.git.UserRemoteConfig></userRemoteConfigs><branches><hudson.plugins.git.BranchSpec><name>*/master</name></hudson.plugins.git.BranchSpec></branches><doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations></scm><scriptPath>Jenkinsfile</scriptPath><lightweight>true</lightweight></definition><disabled>false</disabled></flow-definition>"

try {
    Invoke-J "/job/$JobName/api/json" | Out-Null
    # Job exists - update it
    Invoke-J "/job/$JobName/config.xml" -Method "POST" -Body $jobXml -CT "application/xml" | Out-Null
    Write-Host "      OK - Job '$JobName' updated" -ForegroundColor Green
} catch {
    try {
        Invoke-J "/createItem?name=$([System.Uri]::EscapeDataString($JobName))" -Method "POST" -Body $jobXml -CT "application/xml" | Out-Null
        Write-Host "      OK - Job '$JobName' created" -ForegroundColor Green
    } catch {
        Write-Host "      FAIL - $($_.Exception.Message)" -ForegroundColor Red
    }
}

# ── Step 5: Trigger first build ───────────────────────────────────────────────
Write-Host ""
Write-Host "[5/5] Triggering first build..." -ForegroundColor Yellow
try {
    Invoke-J "/job/$JobName/build" -Method "POST" -Body "" -CT "application/x-www-form-urlencoded" | Out-Null
    Write-Host "      OK - Build queued" -ForegroundColor Green
} catch {
    Write-Host "      INFO - Trigger build manually from the Jenkins UI" -ForegroundColor Yellow
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Done!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Open in browser:" -ForegroundColor White
Write-Host "  $JenkinsUrl/job/$JobName" -ForegroundColor Green
Write-Host ""
Write-Host "  Steps after opening:" -ForegroundColor Yellow
Write-Host "  1. Click 'Build with Parameters'" -ForegroundColor White
Write-Host "  2. Select REVIEW_DEPTH = STANDARD" -ForegroundColor White
Write-Host "  3. Click Build" -ForegroundColor White
Write-Host "  4. Wait for pipeline to finish" -ForegroundColor White
Write-Host "  5. Click 'Pipeline Report' in left sidebar to see HTML report" -ForegroundColor White
Write-Host ""

# Open browser automatically
Start-Process "$JenkinsUrl/job/$JobName"
