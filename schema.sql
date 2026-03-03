-- ============================================================
-- SUPABASE DATABASE SCHEMA
-- Automated Book Generation System
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE 1: books
-- Stores main book information and status
-- ============================================================
CREATE TABLE books (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    notes_on_outline_before TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',  -- pending, in_progress, completed, error
    final_review_notes_status TEXT DEFAULT '',  -- yes, no, no_notes_needed
    final_review_notes TEXT DEFAULT '',
    book_output_status TEXT DEFAULT 'pending',  -- pending, completed
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Index for faster lookups
CREATE INDEX idx_books_status ON books(status);
CREATE INDEX idx_books_created_at ON books(created_at DESC);

-- ============================================================
-- TABLE 2: outlines
-- Stores book outlines with versioning support
-- ============================================================
CREATE TABLE outlines (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    outline_text TEXT NOT NULL,
    notes_before TEXT DEFAULT '',
    notes_after TEXT DEFAULT '',
    status_outline_notes TEXT DEFAULT 'pending',  -- yes, no, no_notes_needed, pending
    version INT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Indexes
CREATE INDEX idx_outlines_book_id ON outlines(book_id);
CREATE INDEX idx_outlines_version ON outlines(book_id, version DESC);

-- ============================================================
-- TABLE 3: chapters
-- Stores individual chapters with versioning support
-- ============================================================
CREATE TABLE chapters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    chapter_number INT NOT NULL,
    title TEXT DEFAULT '',
    content TEXT NOT NULL,
    summary TEXT NOT NULL,  -- For context chaining
    outline_section TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    chapter_notes_status TEXT DEFAULT 'pending',  -- yes, no, no_notes_needed, pending
    version INT DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Indexes
CREATE INDEX idx_chapters_book_id ON chapters(book_id);
CREATE INDEX idx_chapters_book_chapter ON chapters(book_id, chapter_number);
CREATE INDEX idx_chapters_version ON chapters(book_id, chapter_number, version DESC);

-- ============================================================
-- TABLE 4: logs
-- Audit trail of all actions and events
-- ============================================================
CREATE TABLE logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    book_id UUID NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    action TEXT NOT NULL,  -- e.g., 'outline_generated', 'chapter_1_generated'
    status TEXT NOT NULL,  -- completed, error, pending
    details TEXT DEFAULT '',
    error_message TEXT DEFAULT '',
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Indexes
CREATE INDEX idx_logs_book_id ON logs(book_id);
CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);
CREATE INDEX idx_logs_book_timestamp ON logs(book_id, timestamp DESC);

-- ============================================================
-- VIEWS FOR CONVENIENCE
-- ============================================================

-- Latest outline for each book
CREATE VIEW latest_outlines AS
SELECT DISTINCT ON (book_id) *
FROM outlines
ORDER BY book_id, version DESC;

-- Latest version of each chapter
CREATE VIEW latest_chapters AS
SELECT DISTINCT ON (book_id, chapter_number) *
FROM chapters
ORDER BY book_id, chapter_number, version DESC;

-- Book summary view with counts
CREATE VIEW book_summaries AS
SELECT 
    b.id,
    b.title,
    b.status,
    b.created_at,
    COUNT(DISTINCT c.chapter_number) as chapter_count,
    CASE 
        WHEN EXISTS (SELECT 1 FROM outlines o WHERE o.book_id = b.id) THEN true
        ELSE false
    END as has_outline
FROM books b
LEFT JOIN chapters c ON b.id = c.book_id
GROUP BY b.id, b.title, b.status, b.created_at;

-- ============================================================
-- FUNCTIONS
-- ============================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for books table
CREATE TRIGGER update_books_updated_at 
    BEFORE UPDATE ON books
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- ROW LEVEL SECURITY (Optional - configure based on your needs)
-- ============================================================

-- Enable RLS
ALTER TABLE books ENABLE ROW LEVEL SECURITY;
ALTER TABLE outlines ENABLE ROW LEVEL SECURITY;
ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;
ALTER TABLE logs ENABLE ROW LEVEL SECURITY;

-- Example policy - allow all operations (customize based on your auth)
CREATE POLICY "Allow all operations" ON books FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON outlines FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON chapters FOR ALL USING (true);
CREATE POLICY "Allow all operations" ON logs FOR ALL USING (true);

-- ============================================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================================

-- Insert a sample book
-- INSERT INTO books (title, notes_on_outline_before, status) VALUES
-- ('Sample Book: Introduction to AI', 
--  'Create an outline for a beginner-friendly AI book covering basics, machine learning, and practical applications.',
--  'pending');

-- ============================================================
-- STORAGE BUCKET (Optional - for storing compiled files)
-- ============================================================

-- To create storage bucket in Supabase dashboard or via SQL:
-- INSERT INTO storage.buckets (id, name, public) VALUES ('book-outputs', 'book-outputs', true);

-- Then set policies for the bucket in Supabase dashboard

-- ============================================================
-- USEFUL QUERIES
-- ============================================================

-- Get all books with their latest outline and chapter count
-- SELECT 
--     b.id,
--     b.title,
--     b.status,
--     o.outline_text,
--     COUNT(DISTINCT c.chapter_number) as chapter_count
-- FROM books b
-- LEFT JOIN latest_outlines o ON b.id = o.book_id
-- LEFT JOIN latest_chapters c ON b.id = c.book_id
-- GROUP BY b.id, b.title, b.status, o.outline_text;

-- Get all chapters for a specific book (latest versions)
-- SELECT chapter_number, title, summary, chapter_notes_status
-- FROM latest_chapters
-- WHERE book_id = 'YOUR_BOOK_ID'
-- ORDER BY chapter_number;

-- Get activity log for a book
-- SELECT action, status, details, timestamp
-- FROM logs
-- WHERE book_id = 'YOUR_BOOK_ID'
-- ORDER BY timestamp DESC;
