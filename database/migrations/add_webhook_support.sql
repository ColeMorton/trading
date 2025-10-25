-- Migration: Add webhook support to jobs table
-- Date: 2025-10-20
-- Description: Adds webhook_url, webhook_headers, webhook_sent_at, and webhook_response_status columns to the jobs table

-- Add webhook columns
ALTER TABLE jobs 
ADD COLUMN IF NOT EXISTS webhook_url VARCHAR(500),
ADD COLUMN IF NOT EXISTS webhook_headers JSON,
ADD COLUMN IF NOT EXISTS webhook_sent_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS webhook_response_status INTEGER;

-- Add index for webhook jobs (for querying/debugging)
CREATE INDEX IF NOT EXISTS idx_jobs_webhook_url ON jobs(webhook_url) WHERE webhook_url IS NOT NULL;

-- Add comment for documentation
COMMENT ON COLUMN jobs.webhook_url IS 'Optional URL to receive job completion notifications';
COMMENT ON COLUMN jobs.webhook_headers IS 'Optional custom headers to include in webhook requests';
COMMENT ON COLUMN jobs.webhook_sent_at IS 'Timestamp when webhook was sent (NULL if not sent or no webhook configured)';
COMMENT ON COLUMN jobs.webhook_response_status IS 'HTTP status code from webhook delivery (0 for timeout/error, NULL if not sent)';

