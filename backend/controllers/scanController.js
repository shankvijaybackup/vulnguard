/**
 * Scan Controller
 * Handles scan operations for the VulnGuard DAST platform
 * 
 * Privacy-focused: Anonymous sessions, no data persistence
 */

// In-memory storage for current session only
let scans = []

// Enhanced scan phases for better user feedback
const SCAN_PHASES = {
  pending: { progress: 0, message: "Initializing scan..." },
  crawling: { progress: 15, message: "Discovering web pages..." },
  analyzing: { progress: 40, message: "Analyzing page structure..." },
  testing: { progress: 70, message: "Testing for vulnerabilities..." },
  classifying: { progress: 90, message: "Classifying findings..." },
  completed: { progress: 100, message: "Scan complete" },
  failed: { progress: 0, message: "Scan failed" }
}

// Get all scans (current session only)
const getAllScans = async (req, res) => {
  console.log('📋 Getting current session scans')
  res.json({
    success: true,
    data: scans,
    count: scans.length,
    note: "Anonymous session - no data persistence"
  })
}

// Get scan by ID with enhanced status
const getScanById = async (req, res) => {
  const { id } = req.params
  console.log(`🔍 Getting scan ${id}`)
  
  const scan = scans.find(s => s.id === id)
  if (!scan) {
    return res.status(404).json({ error: 'Scan not found in current session' })
  }
  
  // Add current phase info
  const phaseInfo = SCAN_PHASES[scan.status] || SCAN_PHASES.pending
  const enhancedScan = {
    ...scan,
    progress: phaseInfo.progress,
    currentPhase: scan.status,
    statusMessage: phaseInfo.message,
    lastUpdated: new Date().toISOString()
  }
  
  res.json({ success: true, data: enhancedScan })
}

// Start new scan with enhanced feedback
const startScan = async (req, res) => {
  const { targetUrl, scanOptions } = req.body
  console.log(`🚀 Starting enhanced scan for ${targetUrl}`)
  
  // Use a realistic test target if none provided
  const finalTargetUrl = targetUrl || 'https://atomicwork.com'
  
  const newScan = {
    id: `scan_${Date.now()}`,
    targetUrl: finalTargetUrl,
    status: 'pending',
    startTime: new Date().toISOString(),
    scanOptions,
    anonymous: true,
    privacyNote: "This scan is anonymous and will not be stored after your session",
    progress: 0,
    currentPhase: 'pending',
    statusMessage: SCAN_PHASES.pending.message,
    lastUpdated: new Date().toISOString(),
    phases: [
      { name: 'Initialization', status: 'completed', timestamp: new Date().toISOString() },
      { name: 'Crawling', status: 'in_progress', timestamp: null },
      { name: 'Analysis', status: 'pending', timestamp: null },
      { name: 'Testing', status: 'pending', timestamp: null },
      { name: 'Classification', status: 'pending', timestamp: null }
    ]
  }
  
  scans.unshift(newScan)
  
  // Start faster simulation for better UX
  simulateScanProgress(newScan.id)
  
  res.status(201).json({
    success: true,
    data: newScan,
    message: 'Anonymous scan started successfully',
    privacyNote: "Your scan data will be cleared when you leave this page"
  })
}

// Faster scan progress simulation for better UX
const simulateScanProgress = (scanId) => {
  const phaseOrder = ['pending', 'crawling', 'analyzing', 'testing', 'classifying', 'completed']
  let currentPhaseIndex = 0
  
  console.log(`🎯 Starting scan simulation for ${scanId}`)
  
  const progressInterval = setInterval(() => {
    const scan = scans.find(s => s.id === scanId)
    if (!scan) {
      console.log(`❌ Scan ${scanId} not found, stopping simulation`)
      clearInterval(progressInterval)
      return
    }
    
    console.log(`📊 Scan ${scanId} - Current status: ${scan.status}, Phase: ${currentPhaseIndex + 1}/${phaseOrder.length}`)
    
    // Move to next phase faster
    if (currentPhaseIndex < phaseOrder.length - 1) {
      currentPhaseIndex++
      const newStatus = phaseOrder[currentPhaseIndex]
      scan.status = newStatus
      scan.currentPhase = newStatus
      scan.lastUpdated = new Date().toISOString()
      
      console.log(`🔄 Scan ${scanId} moved to phase: ${newStatus}`)
      
      // Update phases array
      if (scan.phases) {
        const phaseIndex = phaseOrder.indexOf(newStatus) - 1
        if (phaseIndex >= 0 && scan.phases[phaseIndex]) {
          scan.phases[phaseIndex].status = 'completed'
          scan.phases[phaseIndex].timestamp = new Date().toISOString()
        }
        if (scan.phases[currentPhaseIndex]) {
          scan.phases[currentPhaseIndex].status = 'in_progress'
        }
      }
    } else {
      // Scan completed
      scan.status = 'completed'
      scan.currentPhase = 'completed'
      scan.endTime = new Date().toISOString()
      scan.resultsCount = Math.floor(Math.random() * 5) + 2 // 2-6 vulnerabilities
      if (scan.phases && scan.phases[scan.phases.length - 1]) {
        scan.phases[scan.phases.length - 1].status = 'completed'
        scan.phases[scan.phases.length - 1].timestamp = new Date().toISOString()
      }
      console.log(`✅ Scan ${scanId} completed successfully`)
      clearInterval(progressInterval)
    }
  }, 600) // Even faster updates every 0.6 seconds
}

// Get scan status with detailed progress
const getScanStatus = async (req, res) => {
  const { id } = req.params
  console.log(`📊 Getting detailed status for scan ${id}`)
  
  const scan = scans.find(s => s.id === id)
  if (!scan) {
    return res.status(404).json({ error: 'Scan not found in current session' })
  }
  
  const phaseInfo = SCAN_PHASES[scan.status] || SCAN_PHASES.pending
  
  res.json({
    success: true,
    status: scan.status,
    progress: phaseInfo.progress,
    currentPhase: scan.currentPhase,
    statusMessage: phaseInfo.message,
    lastUpdated: scan.lastUpdated,
    targetUrl: scan.targetUrl,
    startTime: scan.startTime,
    phases: scan.phases || [],
    anonymous: true,
    estimatedTimeRemaining: scan.status === 'completed' ? 0 : Math.max(2, 15 - (Date.now() - new Date(scan.startTime).getTime()) / 1000)
  })
}

// Cancel scan
const cancelScan = async (req, res) => {
  const { id } = req.params
  console.log(`❌ Cancelling scan ${id}`)
  
  const scanIndex = scans.findIndex(s => s.id === id)
  if (scanIndex === -1) {
    return res.status(404).json({ error: 'Scan not found in current session' })
  }
  
  scans[scanIndex].status = 'cancelled'
  scans[scanIndex].currentPhase = 'cancelled'
  scans[scanIndex].statusMessage = 'Scan cancelled by user'
  
  res.json({
    success: true,
    message: 'Scan cancelled successfully'
  })
}

// Get scan results with enhanced details
const getScanResults = async (req, res) => {
  const { id } = req.params
  console.log(`📋 Getting detailed results for scan ${id}`)
  
  const scan = scans.find(s => s.id === id)
  if (!scan) {
    return res.status(404).json({ error: 'Scan not found in current session' })
  }
  
  if (scan.status !== 'completed') {
    return res.status(400).json({ 
      error: 'Scan not completed yet',
      status: scan.status,
      message: 'Please wait for the scan to complete before viewing results'
    })
  }
  
  // Generate realistic mock results based on scan target
  const mockResults = generateMockResults(scan.targetUrl)
  
  res.json({
    success: true,
    vulnerabilities: mockResults,
    count: mockResults.length,
    scanInfo: {
      targetUrl: scan.targetUrl,
      startTime: scan.startTime,
      endTime: scan.endTime,
      duration: scan.endTime ? (new Date(scan.endTime).getTime() - new Date(scan.startTime).getTime()) / 1000 : 0
    },
    summary: {
      total: mockResults.length,
      high: mockResults.filter(v => v.severity === 'High').length,
      medium: mockResults.filter(v => v.severity === 'Medium').length,
      low: mockResults.filter(v => v.severity === 'Low').length
    },
    privacyNote: "Results are anonymous and session-only"
  })
}

// Generate realistic mock results
const generateMockResults = (targetUrl) => {
  const baseUrl = new URL(targetUrl).hostname
  const vulnerabilities = []
  
  // SQL Injection - more likely for dynamic sites
  if (Math.random() > 0.3) {
    vulnerabilities.push({
      id: `vuln_${Date.now()}_${vulnerabilities.length}`,
      type: 'SQL Injection',
      severity: 'High',
      url: `${targetUrl}/search`,
      description: `Potential SQL injection vulnerability detected in search functionality on ${baseUrl}`,
      confidence: 0.85 + Math.random() * 0.1,
      impact: 'Data breach, unauthorized access to database',
      remediation: 'Use parameterized queries, input sanitization, prepared statements',
      anonymous: true,
      discoveredAt: new Date().toISOString()
    })
  }
  
  // XSS - common on modern web apps
  if (Math.random() > 0.4) {
    vulnerabilities.push({
      id: `vuln_${Date.now()}_${vulnerabilities.length}`,
      type: 'Cross-Site Scripting (XSS)',
      severity: 'Medium',
      url: `${targetUrl}/comment`,
      description: `Cross-site scripting vulnerability found in user input handling on ${baseUrl}`,
      confidence: 0.72 + Math.random() * 0.15,
      impact: 'Session hijacking, defacement, cookie theft',
      remediation: 'Output encoding, Content Security Policy, input validation',
      anonymous: true,
      discoveredAt: new Date().toISOString()
    })
  }
  
  // Information Disclosure - common misconfiguration
  if (Math.random() > 0.6) {
    vulnerabilities.push({
      id: `vuln_${Date.now()}_${vulnerabilities.length}`,
      type: 'Information Disclosure',
      severity: 'Low',
      url: `${targetUrl}/api/status`,
      description: `Server information disclosure in error responses on ${baseUrl}`,
      confidence: 0.65 + Math.random() * 0.1,
      impact: 'Information gathering for targeted attacks',
      remediation: 'Generic error pages, remove version headers, disable debug info',
      anonymous: true,
      discoveredAt: new Date().toISOString()
    })
  }
  
  return vulnerabilities
}

// Rerun scan
const rerunScan = async (req, res) => {
  const { id } = req.params
  console.log(`🔄 Rerunning scan ${id}`)
  
  const scanIndex = scans.findIndex(s => s.id === id)
  if (scanIndex === -1) {
    return res.status(404).json({ error: 'Scan not found in current session' })
  }
  
  scans[scanIndex].status = 'pending'
  scans[scanIndex].currentPhase = 'pending'
  scans[scanIndex].startTime = new Date().toISOString()
  delete scans[scanIndex].endTime
  
  // Restart simulation
  simulateScanProgress(scans[scanIndex].id)
  
  res.json({
    success: true,
    message: 'Scan rerun initiated',
    anonymous: true
  })
}

// Generate report
const generateReport = async (req, res) => {
  const { id } = req.params
  console.log(`📊 Generating detailed report for scan ${id}`)
  
  const scan = scans.find(s => s.id === id)
  if (!scan) {
    return res.status(404).json({ error: 'Scan not found in current session' })
  }
  
  const report = {
    scanId: scan.id,
    targetUrl: scan.targetUrl,
    scanDate: scan.startTime,
    completionDate: scan.endTime,
    status: scan.status,
    anonymous: true,
    privacyNote: "This report is anonymous and will not be stored",
    duration: scan.endTime ? (new Date(scan.endTime).getTime() - new Date(scan.startTime).getTime()) / 1000 : 0,
    summary: {
      totalVulnerabilities: scan.resultsCount || 0,
      high: Math.floor(Math.random() * 2),
      medium: Math.floor(Math.random() * 3) + 1,
      low: Math.floor(Math.random() * 2) + 1
    },
    phases: scan.phases || []
  }
  
  res.json({
    success: true,
    report,
    privacyNote: "Anonymous report - no data retention"
  })
}

// Clear all session data (privacy protection)
const clearSessionData = async (req, res) => {
  console.log('🗑️ Clearing all session data for privacy')
  scans = []
  res.json({
    success: true,
    message: 'All session data cleared for privacy protection',
    anonymous: true
  })
}

module.exports = {
  getAllScans,
  getScanById,
  startScan,
  getScanStatus,
  cancelScan,
  getScanResults,
  rerunScan,
  generateReport,
  clearSessionData
}
