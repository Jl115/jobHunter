-- Migration: Add markdown description column for rich job post rendering

ALTER TABLE jobs ADD COLUMN description_markdown TEXT;
