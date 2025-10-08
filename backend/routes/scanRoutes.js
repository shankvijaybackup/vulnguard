/**
 * Scan Routes
 * API endpoints for managing vulnerability scans
 * 
 * Privacy-focused: Anonymous sessions, no data persistence
 */

const express = require('express')
const router = express.Router()
const { asyncHandler } = require('../middleware/errorMiddleware')
const { validateScanRequest } = require('../middleware/validation')
const scanController = require('../controllers/scanController')

// GET /api/scans - List current session scans only
router.get('/', asyncHandler(scanController.getAllScans))

// GET /api/scans/:id - Get specific scan from current session
router.get('/:id', asyncHandler(scanController.getScanById))

// POST /api/scans - Start new anonymous scan
router.post('/', validateScanRequest, asyncHandler(scanController.startScan))

// GET /api/scans/:id/status - Get scan status (current session only)
router.get('/:id/status', asyncHandler(scanController.getScanStatus))

// DELETE /api/scans/:id - Cancel/delete scan from current session
router.delete('/:id', asyncHandler(scanController.cancelScan))

// GET /api/scans/:id/results - Get scan results (current session only)
router.get('/:id/results', asyncHandler(scanController.getScanResults))

// POST /api/scans/:id/rerun - Rerun a scan (current session only)
router.post('/:id/rerun', asyncHandler(scanController.rerunScan))

// GET /api/scans/:id/report - Generate anonymous scan report
router.get('/:id/report', asyncHandler(scanController.generateReport))

// POST /api/scans/clear - Clear all session data for privacy
router.post('/clear', asyncHandler(scanController.clearSessionData))

module.exports = router
