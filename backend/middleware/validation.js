/**
 * Validation Middleware
 * Input validation for API endpoints
 */

const Joi = require('joi');
const { formatValidationError } = require('./errorMiddleware');

/**
 * Scan request validation schema
 */
const scanRequestSchema = Joi.object({
  targetUrl: Joi.string()
    .uri({ scheme: ['http', 'https'] })
    .required()
    .messages({
      'string.uri': 'Target URL must be a valid HTTP/HTTPS URL',
      'any.required': 'Target URL is required'
    }),

  scanOptions: Joi.object({
    enableSpider: Joi.boolean().default(true),
    enableActive: Joi.boolean().default(true),
    maxChildren: Joi.number().integer().min(1).max(1000).default(10),
    scanPolicy: Joi.string().valid('Default Policy', 'API Policy', 'Quick Policy').default('Default Policy'),
    timeout: Joi.number().integer().min(300).max(7200).default(1800), // 5 minutes to 2 hours
    userAgent: Joi.string().max(500),
    excludePatterns: Joi.array().items(Joi.string()).max(10),
    includePatterns: Joi.array().items(Joi.string()).max(10)
  }).default(),

  notificationSettings: Joi.object({
    email: Joi.string().email(),
    webhook: Joi.string().uri(),
    slackWebhook: Joi.string().uri()
  }).optional()
});

/**
 * Authentication request validation schema
 */
const authRequestSchema = Joi.object({
  username: Joi.string().alphanum().min(3).max(30).required(),
  password: Joi.string().min(6).required()
});

/**
 * Validate scan request middleware
 */
const validateScanRequest = (req, res, next) => {
  const { error, value } = scanRequestSchema.validate(req.body, {
    abortEarly: false,
    allowUnknown: false
  });

  if (error) {
    return res.status(400).json(formatValidationError(error));
  }

  // Replace request body with validated value
  req.body = value;
  next();
};

/**
 * Validate authentication request middleware
 */
const validateAuthRequest = (req, res, next) => {
  const { error, value } = authRequestSchema.validate(req.body, {
    abortEarly: false,
    allowUnknown: false
  });

  if (error) {
    return res.status(400).json(formatValidationError(error));
  }

  req.body = value;
  next();
};

/**
 * Validate URL parameter middleware
 */
const validateObjectId = (req, res, next) => {
  const { id } = req.params;

  if (!id || !id.match(/^[0-9a-fA-F]{24}$/)) {
    return res.status(400).json({
      success: false,
      error: 'Invalid ID format',
      statusCode: 400
    });
  }

  next();
};

/**
 * Validate query parameters middleware
 */
const validateQueryParams = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.query, {
      abortEarly: false,
      allowUnknown: false
    });

    if (error) {
      return res.status(400).json(formatValidationError(error));
    }

    req.query = value;
    next();
  };
};

/**
 * Common query parameter schemas
 */
const paginationSchema = Joi.object({
  page: Joi.number().integer().min(1).default(1),
  limit: Joi.number().integer().min(1).max(100).default(10),
  sort: Joi.string().valid('asc', 'desc').default('desc'),
  sortBy: Joi.string().default('createdAt')
});

const scanFilterSchema = Joi.object({
  status: Joi.string().valid('pending', 'running', 'completed', 'failed'),
  targetUrl: Joi.string(),
  dateFrom: Joi.date().iso(),
  dateTo: Joi.date().iso().min(Joi.ref('dateFrom'))
});

module.exports = {
  validateScanRequest,
  validateAuthRequest,
  validateObjectId,
  validateQueryParams,
  paginationSchema,
  scanFilterSchema
};
