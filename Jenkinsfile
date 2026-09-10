/**
 * Jenkins Pipeline with Claude AI Agent Code Review
 *
 * This pipeline performs automated code review using Anthropic's Claude AI Agent
 * and enforces quality gates before allowing builds to proceed.
 *
 * Features:
 * - Agentic AI code review with Claude (tool-use loop)
 * - Configurable quality thresholds
 * - Comprehensive HTML reporting
 * - Windows-compatible commands
 *
 * @author Jenkins Pipeline Team
 * @version 3.0
 */

pipeline {
    agent any
    
    environment {
        // Claude AI Agent Configuration (IBM Gateway)
        CLAUDE_API_KEY = credentials('claude-api-key')
        CLAUDE_MODEL = 'claude-sonnet-4-6'
        CLAUDE_BASE_URL = 'https://api.nextgen-beta.ica.ibm.com/ica'

        // Quality Gate Thresholds
        // Build is BLOCKED if any score falls below these values
        CODE_QUALITY_THRESHOLD     = '70'   // Block if code quality  < 70
        SECURITY_THRESHOLD         = '70'   // Block if security      < 70
        MAINTAINABILITY_THRESHOLD  = '60'   // Block if maintainability < 60

        // Build Configuration
        BUILD_TIMESTAMP = "${new Date().format('yyyyMMdd-HHmmss')}"
    }
    
    parameters {
        choice(
            name: 'REVIEW_DEPTH', 
            choices: ['QUICK', 'STANDARD', 'COMPREHENSIVE'], 
            description: 'Code review depth level'
        )
        booleanParam(
            name: 'SKIP_QUALITY_GATE', 
            defaultValue: false, 
            description: 'Skip quality gate validation (not recommended for production)'
        )
        string(
            name: 'CUSTOM_THRESHOLD', 
            defaultValue: '', 
            description: 'Override quality threshold (0-100, leave empty for defaults)'
        )
    }
    
    stages {
        stage('Checkout') {
            steps {
                script {
                    echo "🔄 Checking out code from repository..."
                    checkout scm
                    extractGitMetadata()
                }
            }
        }
        
        stage('Pre-Build Analysis') {
            steps {
                script {
                    echo "📊 Running pre-build analysis..."
                    analyzeCodebase()
                }
            }
        }
        
        stage('Claude AI Agent Code Review') {
            steps {
                script {
                    echo "🤖 Starting Claude AI Agent Code Review..."
                    performCodeReview()
                }
            }
        }
        
        stage('Quality Gate') {
            steps {
                script {
                    echo "🚦 Evaluating Quality Gate..."
                    echo "   Thresholds — Code Quality: ${CODE_QUALITY_THRESHOLD}, Security: ${SECURITY_THRESHOLD}, Maintainability: ${MAINTAINABILITY_THRESHOLD}"
                    try {
                        evaluateQualityGate()
                    } catch (Exception e) {
                        // Store error — generate report first so the HTML shows WHY it failed
                        env.QUALITY_GATE_ERROR = e.getMessage()
                        echo "❌ Quality Gate FAILED — report will still be generated"
                    }
                }
            }
        }

        stage('Build') {
            // Skipped automatically if quality gate failed
            when {
                expression { env.QUALITY_GATE_STATUS != 'FAILED' }
            }
            steps {
                script {
                    echo "🔨 Building application..."
                    buildApplication()
                }
            }
        }

        stage('Test') {
            // Skipped automatically if quality gate failed
            when {
                expression { env.QUALITY_GATE_STATUS != 'FAILED' }
            }
            steps {
                script {
                    echo "🧪 Running tests..."
                    runTests()
                }
            }
        }

        stage('Generate Report') {
            steps {
                script {
                    echo "📄 Generating report for commit ${env.GIT_COMMIT_SHORT}..."
                    generateReport()

                    // Fail the build AFTER the report is generated
                    // so the HTML report always shows what went wrong
                    if (env.QUALITY_GATE_ERROR) {
                        error("🚫 BUILD BLOCKED — ${env.QUALITY_GATE_ERROR}")
                    }
                }
            }
        }
    }
    
    post {
        success {
            script {
                handleSuccess()
            }
        }
        
        failure {
            script {
                handleFailure()
            }
        }
        
        unstable {
            script {
                handleUnstable()
            }
        }
        
        always {
            script {
                // Publish HTML report with full styling
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'pipeline-report.html',
                    reportName: 'Pipeline Report',
                    reportTitles: 'Claude AI Agent Code Review Report'
                ])
                
                cleanup()
            }
        }
    }
}

// ============================================================================
// HELPER FUNCTIONS - Improve maintainability by extracting reusable logic
// ============================================================================

/**
 * Extract Git metadata (commit hash, author, message)
 * Windows-compatible implementation
 */
def extractGitMetadata() {
    try {
        // Use direct git commands with output redirection
        bat '''
            @echo off
            git rev-parse --short HEAD > commit_short.txt
            git log -1 --pretty=%%an > commit_author.txt
        '''
        
        env.GIT_COMMIT_SHORT = readFile('commit_short.txt').trim()
        env.GIT_AUTHOR = readFile('commit_author.txt').trim()
        
        // Fallback if author is empty
        if (!env.GIT_AUTHOR || env.GIT_AUTHOR.isEmpty() || env.GIT_AUTHOR == "ECHO is off.") {
            env.GIT_AUTHOR = "Unknown Author"
        }
        
        echo "✓ Commit: ${env.GIT_COMMIT_SHORT}"
        echo "✓ Author: ${env.GIT_AUTHOR}"
    } catch (Exception e) {
        echo "⚠️ Warning: Could not extract full Git metadata: ${e.message}"
        env.GIT_COMMIT_SHORT = "unknown"
        env.GIT_AUTHOR = "Unknown Author"
    }
}

/**
 * Analyze codebase for basic metrics
 */
def analyzeCodebase() {
    bat '''
        @echo off
        echo Files changed in this commit:
        git diff --name-only HEAD~1 HEAD 2>nul || echo Initial commit
        
        echo.
        echo Total lines of code:
        dir /s /b *.java *.py *.js *.ts 2>nul | find /c /v "" || echo 0
    '''
}

/**
 * Perform Claude AI Agent code review
 */
def performCodeReview() {
    def reviewDepth = params.REVIEW_DEPTH
    
    def reviewResult = bat(
        script: """
            @echo off
            python scripts\\claude_code_review.py ^
                --api-key "%CLAUDE_API_KEY%" ^
                --base-url "%CLAUDE_BASE_URL%" ^
                --model "%CLAUDE_MODEL%" ^
                --review-depth "${reviewDepth}" ^
                --commit "%GIT_COMMIT_SHORT%" ^
                --output-file "review-report.json"
        """,
        returnStatus: true
    )
    
    if (reviewResult != 0) {
        error("❌ Claude AI Agent code review failed")
    }
    
    parseReviewResults()
}

/**
 * Parse JSON text into a Map — runs outside the CPS sandbox so Groovy's
 * built-in JsonSlurper is fully available with no plugin or approval needed.
 */
@NonCPS
private Map parseJson(String text) {
    return new groovy.json.JsonSlurper().parseText(text)
}

/**
 * Parse and display review results.
 * readFile() is sandbox-safe; JSON parsing delegated to @NonCPS helper.
 */
def parseReviewResults() {
    def reviewData = parseJson(readFile('review-report.json'))
    def scores     = reviewData.scores

    env.CODE_QUALITY_SCORE    = scores.code_quality    as String
    env.SECURITY_SCORE        = scores.security         as String
    env.MAINTAINABILITY_SCORE = scores.maintainability  as String
    env.OVERALL_SCORE         = scores.overall          as String

    echo "📈 Review Scores:"
    echo "  - Code Quality:    ${env.CODE_QUALITY_SCORE}/100"
    echo "  - Security:        ${env.SECURITY_SCORE}/100"
    echo "  - Maintainability: ${env.MAINTAINABILITY_SCORE}/100"
    echo "  - Overall:         ${env.OVERALL_SCORE}/100"

    archiveArtifacts artifacts: 'review-report.json', fingerprint: true
}

/**
 * Evaluate quality gate with configurable thresholds
 */
def evaluateQualityGate() {
    if (params.SKIP_QUALITY_GATE) {
        echo "⚠️ Quality Gate SKIPPED by user request"
        env.QUALITY_GATE_STATUS = 'SKIPPED'
        return
    }
    
    // Check build history for unresolved issues
    def historyCheck = bat(
        script: """
            @echo off
            python scripts\\build_history_tracker.py --action check
        """,
        returnStatus: true
    )
    
    if (historyCheck != 0) {
        error("❌ Build BLOCKED: Previous builds have unresolved issues that must be fixed first. Check build history for details.")
    }
    
    def thresholds = determineThresholds()
    
    def qualityGateResult = bat(
        script: """
            @echo off
            python scripts\\quality_gate.py ^
                --review-file "review-report.json" ^
                --code-threshold ${thresholds.code} ^
                --security-threshold ${thresholds.security} ^
                --maintainability-threshold ${thresholds.maintainability} ^
                --output-file "quality-gate-result.json"
        """,
        returnStatus: true
    )
    
    processQualityGateResults()
    
    // Add build to history
    addBuildToHistory()
}

/**
 * Determine quality thresholds based on parameters
 */
def determineThresholds() {
    def codeThreshold = params.CUSTOM_THRESHOLD ? 
        params.CUSTOM_THRESHOLD.toInteger() : 
        CODE_QUALITY_THRESHOLD.toInteger()
    
    return [
        code: codeThreshold,
        security: SECURITY_THRESHOLD.toInteger(),
        maintainability: MAINTAINABILITY_THRESHOLD.toInteger()
    ]
}

/**
 * Process and display quality gate results.
 * JSON parsing delegated to @NonCPS helper — no plugin, no sandbox issue.
 */
def processQualityGateResults() {
    def gateData = parseJson(readFile('quality-gate-result.json'))

    env.QUALITY_GATE_STATUS  = gateData.status  as String
    env.QUALITY_GATE_MESSAGE = gateData.message as String

    echo "Quality Gate Result: ${env.QUALITY_GATE_STATUS}"
    echo "Message:             ${env.QUALITY_GATE_MESSAGE}"

    if (env.QUALITY_GATE_STATUS == 'FAILED') {
        echo "❌ Quality Gate FAILED"
        echo "Failed Criteria:"
        (gateData.failed_criteria ?: []).each { echo "  - ${it}" }
        error("Quality Gate Failed - Build cannot proceed")
    } else if (env.QUALITY_GATE_STATUS == 'WARNING') {
        echo "⚠️ Quality Gate PASSED with warnings"
        echo "Warning Criteria:"
        (gateData.warning_criteria ?: []).each { echo "  - ${it}" }
        echo "ℹ️  Build will continue as SUCCESS despite warnings"
    } else {
        echo "✅ Quality Gate PASSED"
    }

    archiveArtifacts artifacts: 'quality-gate-result.json', fingerprint: true
}

/**
 * Build application (customize based on your project type)
 */
def buildApplication() {
    bat '''
        @echo off
        REM Customize these commands for your project
        REM Java/Maven: mvn clean package -DskipTests
        REM Node.js: npm install && npm run build
        REM Python: pip install -r requirements.txt && python setup.py build
        
        echo Build completed successfully
    '''
}

/**
 * Run test suite (customize based on your project type)
 */
def runTests() {
    bat '''
        @echo off
        REM Customize these commands for your project
        REM Java/Maven: mvn test
        REM Node.js: npm test
        REM Python: pytest
        
        echo Tests completed
    '''
}

/**
 * Generate comprehensive HTML report
 */
def generateReport() {
    bat """
        @echo off
        python scripts\\generate_report.py ^
            --review-file review-report.json ^
            --quality-gate-file quality-gate-result.json ^
            --commit %GIT_COMMIT_SHORT% ^
            --author "%GIT_AUTHOR%" ^
            --output-file pipeline-report.html
    """
    
    archiveArtifacts artifacts: 'pipeline-report.html', fingerprint: true
    echo "📊 Report archived as artifact: pipeline-report.html"
    echo "💡 Tip: Install 'HTML Publisher Plugin' to view reports directly in Jenkins UI"
}

/**
 * Handle successful pipeline completion
 */
def handleSuccess() {
    echo "✅ Pipeline completed successfully!"
    echo "Claude AI Agent Review — Overall Score: ${env.OVERALL_SCORE}/100"
    echo "Quality Gate: ${env.QUALITY_GATE_STATUS}"
    
    // Optional: Send success notification
    // emailext subject: "✅ Build Success: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
    //          body: "Quality Score: ${env.OVERALL_SCORE}/100\nQuality Gate: ${env.QUALITY_GATE_STATUS}",
    //          to: "${env.GIT_AUTHOR}@company.com"
}

/**
 * Handle pipeline failure
 */
def handleFailure() {
    echo "❌ Pipeline failed!"
    echo "Quality Gate: ${env.QUALITY_GATE_STATUS}"
    
    // Optional: Send failure notification
    // emailext subject: "❌ Build Failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
    //          body: "Quality Gate: ${env.QUALITY_GATE_STATUS}\nCheck console output for details.",
    //          to: "${env.GIT_AUTHOR}@company.com"
}

/**
 * Handle unstable pipeline (warnings)
 */
def handleUnstable() {
    echo "⚠️ Pipeline completed with warnings"
    echo "Quality Gate: ${env.QUALITY_GATE_STATUS}"
}

/**
 * Add build to history tracker
 */
def addBuildToHistory() {
    def buildStatus = env.QUALITY_GATE_STATUS == 'FAILED' ? 'FAILED' :
                     env.QUALITY_GATE_STATUS == 'WARNING' ? 'WARNING' : 'PASSED'
    
    bat """
        @echo off
        python scripts\\build_history_tracker.py ^
            --action add ^
            --commit ${env.GIT_COMMIT_SHORT} ^
            --author "${env.GIT_AUTHOR}" ^
            --status ${buildStatus} ^
            --review-file review-report.json ^
            --quality-gate-file quality-gate-result.json
    """
    
    // Generate history report
    bat """
        @echo off
        python scripts\\build_history_tracker.py ^
            --action report ^
            --output-file history-report.json
    """
    
    archiveArtifacts artifacts: 'build-history.json,history-report.json', allowEmptyArchive: true
}

/**
 * Cleanup and archive artifacts
 */
def cleanup() {
    echo "🧹 Cleaning up..."
    archiveArtifacts artifacts: '*.json,*.html,*.txt', allowEmptyArchive: true
    
    // Optional: Clean workspace
    // cleanWs()
}