/**
 * Error Handling Middleware
 * Centralized error handling for the VulnGuard API
 */

const logger = require('../utils/logger');

/**
 * Custom error class for API errors
 */
class APIError extends Error {
  constructor(message, statusCode = 500, isOperational = true, stack = '') {
    super(message);
    this.name = this.constructor.name;
    this.message = message;
    this.statusCode = statusCode;
    this.isOperational = isOperational;

    if (stack) {
      this.stack = stack;
    } else {
      Error.captureStackTrace(this, this.constructor);
    }
  }
}

/**
 * 404 Not Found handler
 */
const notFound = (req, res, next) => {
  const error = new APIError(`Not found - ${req.originalUrl}`, 404);
  res.status(404);
  next(error);
};

/**
 * Global error handler middleware
 */
const errorHandler = (err, req, res, next) => {
  let error = { ...err };
  error.message = err.message;

  // Log error
  logger.logError(err, {
    url: req.url,
    method: req.method,
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });

  // Mongoose bad ObjectId
  if (err.name === 'CastError') {
    const message = 'Resource not found';
    error = new APIError(message, 404);
  }

  // Mongoose duplicate key
  if (err.code === 11000) {
    const message = 'Duplicate field value entered';
    error = new APIError(message, 400);
  }

  // Mongoose validation error
  if (err.name === 'ValidationError') {
    const message = Object.values(err.errors).map(val => val.message).join(', ');
    error = new APIError(message, 400);
  }

  // JWT errors
  if (err.name === 'JsonWebTokenError') {
    const message = 'Invalid token';
    error = new APIError(message, 401);
  }

  if (err.name === 'TokenExpiredError') {
    const message = 'Token expired';
    error = new APIError(message, 401);
  }

  // Development vs Production error response
  if (process.env.NODE_ENV === 'development') {
    res.status(error.statusCode || 500).json({
      success: false,
      error: error.message || 'Server Error',
      stack: err.stack,
      statusCode: error.statusCode || 500
    });
  } else {
    // Production - don't leak error details
    res.status(error.statusCode || 500).json({
      success: false,
      error: error.message || 'Server Error',
      statusCode: error.statusCode || 500
    });
  }
};

/**
 * Async error wrapper
 * Wraps async route handlers to catch rejected promises
 */
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

/**
 * Handle multer file upload errors
 */
const handleMulterError = (err, req, res, next) => {
  if (err instanceof multer.MulterError) {
    if (err.code === 'LIMIT_FILE_SIZE') {
      const error = new APIError('File too large', 400);
      return next(error);
    }
    if (err.code === 'LIMIT_FILE_COUNT') {
      const error = new APIError('Too many files', 400);
      return next(error);
    }
    if (err.code === 'LIMIT_UNEXPECTED_FILE') {
      const error = new APIError('Unexpected file field', 400);
      return next(error);
    }
  }
  next(err);
};

/**
 * Validation error formatter for Joi
 */
const formatValidationError = (error) => {
  const errors = error.details.map(detail => ({
    field: detail.path.join('.'),
    message: detail.message,
    value: detail.context.value
  }));

  return {
    success: false,
    error: 'Validation failed',
    details: errors,
    statusCode: 400
  };
};

module.exports = {
  APIError,
  notFound,
  errorHandler,
  asyncHandler,
  handleMulterError,
  formatValidationError
};
