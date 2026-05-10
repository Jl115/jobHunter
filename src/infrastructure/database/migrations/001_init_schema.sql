-- Initial schema for Job Hunter Desktop App

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    url TEXT NOT NULL UNIQUE,
    source TEXT NOT NULL,
    title TEXT,
    company TEXT,
    location TEXT,
        description TEXT,      -- full plain-text job posting content
    raw_html TEXT NOT NULL,
    scraped_at TEXT NOT NULL,
    extracted_at TEXT,
    match_score REAL DEFAULT 0.0,
    status TEXT DEFAULT 'new' CHECK(status IN ('new', 'viewed', 'applied', 'rejected')),
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS resumes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    parsed_skills TEXT,
    parsed_experience TEXT,
    uploaded_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    resume_id INTEGER,
    email_subject TEXT,
    email_body TEXT,
    sent_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (resume_id) REFERENCES resumes(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at);
CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score);
