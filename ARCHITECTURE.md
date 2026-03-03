# 🏗 System Architecture Documentation

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Component Design](#component-design)
- [Workflow State Machine](#workflow-state-machine)
- [Context Chaining Strategy](#context-chaining-strategy)
- [Database Schema Design](#database-schema-design)
- [Gating Logic Implementation](#gating-logic-implementation)
- [Error Handling Strategy](#error-handling-strategy)
- [Scalability Considerations](#scalability-considerations)

## Architecture Overview

### Design Principles

This system follows these core principles:

1. **Modularity**: Each component has a single responsibility
2. **Separation of Concerns**: Clear boundaries between layers
3. **State Management**: Explicit state tracking at each stage
4. **Fail-Safe Design**: Graceful degradation and error recovery
5. **Human-in-the-Loop**: Strategic intervention points

### System Layers

```
┌─────────────────────────────────────────────┐
│         PRESENTATION LAYER                  │
│  (CLI, API endpoints can be added)          │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│      ORCHESTRATION LAYER (main.py)          │
│  • Workflow Management                      │
│  • State Transitions                        │
│  • Gating Logic                             │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│         BUSINESS LOGIC LAYER                │
│  ┌──────────────┬──────────────┬─────────┐ │
│  │ Generators   │ Summarizer   │Compiler │ │
│  └──────────────┴──────────────┴─────────┘ │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│      DATA ACCESS LAYER (db.py)              │
│  • CRUD Operations                          │
│  • Query Optimization                       │
│  • Transaction Management                   │
└─────────────────────────────────────────────┘
                    ↕
┌─────────────────────────────────────────────┐
│     PERSISTENCE LAYER (Supabase)            │
│  • PostgreSQL Database                      │
│  • Storage for compiled files               │
└─────────────────────────────────────────────┘
```

## Component Design

### 1. Config Module (config.py)

**Responsibility**: Centralized configuration management

**Design Pattern**: Singleton-like class with class variables

```python
class Config:
    # Environment variables
    # Constants
    # Validation
```

**Key Features**:
- Environment variable loading
- Default values
- Validation on startup
- Type-safe constants

### 2. Database Manager (db.py)

**Responsibility**: All database interactions

**Design Pattern**: Repository Pattern

**Key Methods**:
- Books CRUD
- Outlines with versioning
- Chapters with versioning
- Logging
- Context retrieval

**Critical Feature - Context Chaining**:
```python
def get_previous_chapter_summaries(book_id, up_to_chapter):
    """Returns summaries of all previous chapters"""
    # This is KEY to maintaining narrative continuity
```

### 3. Outline Generator (outline_generator.py)

**Responsibility**: Outline generation and parsing

**Design Pattern**: Strategy Pattern (swappable LLM)

**Methods**:
- `generate_outline()` - Initial generation
- `regenerate_outline()` - Based on feedback
- `parse_outline_into_chapters()` - Structure extraction

**Prompting Strategy**:
- System prompt defines role
- User prompt includes context and requirements
- Temperature balanced for creativity vs. consistency

### 4. Chapter Generator (chapter_generator.py)

**Responsibility**: Chapter content generation

**Design Pattern**: Strategy Pattern

**Critical Feature - Context Awareness**:
```python
def generate_chapter(title, chapter_number, ..., previous_summaries):
    # Inject previous_summaries into prompt
    # This maintains narrative continuity
```

**Prompting Strategy**:
- Chapter objective from outline
- Previous chapter context
- Editor notes if regenerating
- Writing guidelines

### 5. Summarizer (summarizer.py)

**Responsibility**: Content summarization for context

**Design Pattern**: Strategy Pattern

**Purpose**:
- Create concise summaries (150-200 words)
- Capture key information for continuity
- Reduce token usage in subsequent prompts

**Why Important**:
Without summarization, context would become too large as chapters accumulate.

### 6. Compiler (compiler.py)

**Responsibility**: Document generation

**Design Pattern**: Builder Pattern

**Methods**:
- `compile_to_docx()` - Word document with formatting
- `compile_to_txt()` - Plain text
- `compile_both_formats()` - Both outputs

**Document Structure**:
1. Title page
2. Table of contents
3. Chapters with formatting
4. Metadata (optional)

### 7. Notifier (notifier.py)

**Responsibility**: Event notifications

**Design Pattern**: Observer Pattern

**Channels**:
- Email (SMTP)
- MS Teams (Webhooks)
- Console (always)

**Key Events**:
- Outline ready
- Chapter ready
- Waiting for notes
- Final draft complete
- Errors

### 8. Main Orchestrator (main.py)

**Responsibility**: Workflow orchestration and state management

**Design Pattern**: State Machine + Coordinator

**Critical Methods**:
- State checking (`check_outline_status`, `check_chapter_status`)
- State transitions (generate, regenerate, approve)
- Workflow automation (`run_full_workflow`)

## Workflow State Machine

### Outline State Machine

```
┌──────────┐
│  START   │
└────┬─────┘
     │ create_book()
     ▼
┌─────────────────┐
│ WAITING_FOR_    │ ← No notes_on_outline_before
│ INITIAL_NOTES   │
└────┬────────────┘
     │ notes added
     ▼
┌─────────────────┐
│  GENERATING_    │
│   OUTLINE       │
└────┬────────────┘
     │ outline created
     ▼
┌─────────────────┐
│ WAITING_FOR_    │ ◄──────┐
│ OUTLINE_REVIEW  │        │
└────┬────────────┘        │
     │                     │
     │ status check        │
     ├─────────────────────┤
     │                     │
     ├─ no_notes_needed ──► PROCEED TO CHAPTERS
     │                     
     ├─ yes + notes ───────► REGENERATE (loops back)
     │                     
     └─ no/empty ─────────► PAUSED
```

### Chapter State Machine (per chapter)

```
┌──────────────────┐
│ NOT_GENERATED    │
└────┬─────────────┘
     │ outline approved
     ▼
┌──────────────────┐
│ GENERATING       │
│ + Context Fetch  │
│ + Summarization  │
└────┬─────────────┘
     │
     ▼
┌──────────────────┐
│ WAITING_FOR_     │ ◄──────┐
│ REVIEW           │        │
└────┬─────────────┘        │
     │                      │
     │ status check         │
     ├──────────────────────┤
     │                      │
     ├─ no_notes_needed ───► APPROVED → Next Chapter
     │                      
     ├─ yes + notes ────────► REGENERATE (loops back)
     │                      
     └─ no/empty ──────────► PAUSED
```

### Complete Workflow

```
START
  │
  ▼
OUTLINE STAGE
  ├─ Generate
  ├─ Review Gate
  └─ Approve/Regenerate
  │
  ▼
CHAPTER LOOP (for each chapter)
  ├─ Fetch previous summaries
  ├─ Generate with context
  ├─ Create summary
  ├─ Review Gate
  └─ Approve/Regenerate
  │
  ▼
ALL CHAPTERS APPROVED
  │
  ▼
FINAL COMPILATION
  ├─ Compile documents
  ├─ Save outputs
  └─ Notify completion
  │
  ▼
COMPLETE
```

## Context Chaining Strategy

### The Problem

When writing Chapter 5, how do we ensure it knows what happened in Chapters 1-4?

### The Solution: Summary-Based Context Chain

```python
# Simplified flow for Chapter N

# Step 1: Get previous chapter summaries
previous_summaries = db.get_previous_chapter_summaries(book_id, chapter_N)
# Returns: ["Chapter 1: ...", "Chapter 2: ...", ...]

# Step 2: Inject into prompt
context = "\n".join(previous_summaries)
prompt = f"""
Previous chapters covered:
{context}

Now write Chapter {N} about: {chapter_description}
"""

# Step 3: Generate
chapter_N = llm.generate(prompt)

# Step 4: Summarize for next chapter
summary_N = llm.summarize(chapter_N)
db.save_chapter(chapter_N, summary_N)

# Next chapter will use summaries 1..N
```

### Why Summaries?

**Problem with Full Context**:
- Chapter 1: 3000 words
- Chapter 2: 3000 words
- Chapter 3: 3000 words
- For Chapter 4: Need 9000 words of context!
- By Chapter 10: 27,000 words! Exceeds token limits.

**Solution with Summaries**:
- Chapter 1 Summary: 150 words
- Chapter 2 Summary: 150 words
- Chapter 3 Summary: 150 words
- For Chapter 4: Only 450 words of context!
- By Chapter 10: 1,350 words - manageable.

### Summary Quality

Summaries are designed to capture:
1. Main topics covered
2. Key concepts introduced
3. Important narrative progression
4. Critical information for continuity

## Database Schema Design

### Design Decisions

#### 1. Versioning Strategy

**Why Versioning?**
- Track iteration history
- Allow rollback
- Compare versions
- Audit trail

**Implementation**:
```sql
-- Outlines table
version INT DEFAULT 1

-- Get latest
SELECT * FROM outlines 
WHERE book_id = ? 
ORDER BY version DESC 
LIMIT 1
```

#### 2. Status Fields

Every entity has status fields for gating logic:
- `status_outline_notes`: yes, no, no_notes_needed
- `chapter_notes_status`: yes, no, no_notes_needed
- `final_review_notes_status`: yes, no, no_notes_needed

**State Transitions**:
```
pending → waiting_for_notes → (yes/no/no_notes_needed) → next_stage
```

#### 3. Separate Tables vs. JSON

**Decision**: Separate tables for outlines and chapters

**Why?**
- Better querying
- Efficient indexing
- Easier versioning
- Clearer relationships

#### 4. Logs Table

Complete audit trail:
```sql
CREATE TABLE logs (
    book_id UUID,
    action TEXT,
    status TEXT,
    details TEXT,
    timestamp TIMESTAMP
)
```

**Purpose**:
- Debugging
- Monitoring
- Performance analysis
- Compliance

### Key Indexes

```sql
-- Fast book lookup
CREATE INDEX idx_books_status ON books(status);

-- Fast chapter retrieval
CREATE INDEX idx_chapters_book_chapter ON chapters(book_id, chapter_number);

-- Latest version queries
CREATE INDEX idx_chapters_version ON chapters(book_id, chapter_number, version DESC);

-- Log analysis
CREATE INDEX idx_logs_timestamp ON logs(timestamp DESC);
```

## Gating Logic Implementation

### Philosophy

**Gates are checkpoints where human judgment is required.**

### Three-Value Status System

```python
NOTES_YES = "yes"              # Has feedback, needs regeneration
NOTES_NO = "no"                # Rejected, pause workflow
NOTES_NOT_NEEDED = "no_notes_needed"  # Approved, proceed
```

### Implementation Pattern

```python
def check_status(book_id, stage):
    """Generic status check pattern"""
    
    entity = db.get_entity(book_id, stage)
    status = entity['status_field']
    notes = entity['notes_field']
    
    if status == NOTES_NOT_NEEDED:
        return 'approved'
    elif status == NOTES_YES:
        if notes:
            return 'needs_regeneration'
        else:
            return 'waiting_for_notes'
    elif status == NOTES_NO:
        return 'paused'
    else:
        return 'waiting'
```

### Workflow Decision Tree

```
Check Status
    │
    ├─ no_notes_needed?
    │   └─► PROCEED TO NEXT STAGE
    │
    ├─ yes + has_notes?
    │   └─► REGENERATE
    │
    ├─ yes + no_notes?
    │   └─► WAIT
    │
    └─ no?
        └─► PAUSE WORKFLOW
```

### Examples

**Example 1: Smooth Flow**
```python
# Editor approves outline immediately
status_outline_notes = "no_notes_needed"
# System proceeds to chapter generation
```

**Example 2: Feedback Loop**
```python
# Editor provides feedback
status_outline_notes = "yes"
notes_after = "Add chapter on X"
# System regenerates outline
# New outline created
# Back to review gate
```

**Example 3: Rejection**
```python
# Editor rejects
status_outline_notes = "no"
# System pauses workflow
# Requires manual intervention
```

## Error Handling Strategy

### Layers of Error Handling

#### 1. Component Level
```python
try:
    outline = llm.generate(prompt)
except Exception as e:
    log_error(book_id, "outline_generation_failed", str(e))
    raise
```

#### 2. Orchestrator Level
```python
try:
    self.generate_outline(book_id)
except Exception as e:
    self.db.log_action(book_id, "outline_generation", "error", error_message=str(e))
    self.notifier.notify_error(book_id, title, str(e))
    # Decide: retry, pause, or fail
```

#### 3. Graceful Degradation

- LLM API down → Queue request, notify operator
- Database connection lost → Retry with exponential backoff
- Email fails → Still log to console and database

### Logging Strategy

**Three-Level Logging**:

1. **Database Logs** (persistent)
   ```python
   db.log_action(book_id, action, status, details, error_message)
   ```

2. **Console Logs** (immediate feedback)
   ```python
   print(f"✓ Chapter {n} generated")
   print(f"✗ Failed to generate outline")
   ```

3. **Notifications** (stakeholder alerts)
   ```python
   notifier.notify_error(book_id, title, error)
   ```

## Scalability Considerations

### Current Design Trade-offs

| Aspect | Current Design | Scales To |
|--------|---------------|-----------|
| Processing | Synchronous | ~10 books/hour |
| Database | Supabase Free | ~100K records |
| LLM Calls | Sequential | Rate limit dependent |
| Storage | Local files | Limited by disk |

### Scaling Path

#### Phase 1: Basic Production (Handles 10-50 books/day)
- Add task queue (Celery + Redis)
- Implement retry logic
- Add connection pooling

#### Phase 2: Medium Scale (Handles 100-500 books/day)
- Horizontal scaling with workers
- Load balancer
- Distributed caching (Redis)
- Batch processing

#### Phase 3: Large Scale (Handles 1000+ books/day)
- Microservices architecture
- Event-driven design
- Vector database for context
- CDN for file delivery

### Bottlenecks and Solutions

**Bottleneck 1: LLM API Calls**
- **Problem**: Sequential calls are slow
- **Solution**: 
  - Batch where possible
  - Use streaming for long responses
  - Implement fallback models

**Bottleneck 2: Context Size**
- **Problem**: As book grows, context grows
- **Solution**: 
  - Smart summarization (already implemented)
  - Semantic search for relevant context
  - Hierarchical summarization

**Bottleneck 3: Database Queries**
- **Problem**: Complex queries for context retrieval
- **Solution**:
  - Materialized views
  - Caching layer
  - Read replicas

### Monitoring Strategy

**Key Metrics**:
1. Books per hour processed
2. Average chapter generation time
3. Regeneration rate (quality indicator)
4. Error rate by component
5. LLM token usage

**Alerting**:
- Error rate > 5% → Immediate alert
- Queue depth > 100 → Warning
- Generation time > 5 min → Investigate

## Design Patterns Used

### 1. Repository Pattern (db.py)
Abstracts data access, easy to swap database.

### 2. Strategy Pattern (Generators)
Swap LLM providers without changing logic.

### 3. State Machine (Orchestrator)
Explicit state management and transitions.

### 4. Observer Pattern (Notifier)
Decouple event producers from consumers.

### 5. Builder Pattern (Compiler)
Construct complex documents step by step.

### 6. Facade Pattern (Orchestrator)
Simple interface to complex subsystem.

## Security Considerations

### Data Protection
- API keys in environment variables
- Database credentials secured
- No sensitive data in logs

### Input Validation
- Validate book titles and inputs
- Sanitize file names
- Prevent SQL injection (using parameterized queries)

### Rate Limiting
- Respect LLM API rate limits
- Implement request throttling
- Handle 429 errors gracefully

## Testing Strategy

### Unit Tests
- Test each component independently
- Mock external dependencies
- Cover edge cases

### Integration Tests
- Test workflow stages
- Test database operations
- Test LLM integration

### End-to-End Tests
- Complete book generation
- Feedback loops
- Error scenarios

## Conclusion

This architecture prioritizes:
1. **Clarity**: Easy to understand flow
2. **Modularity**: Easy to modify components
3. **Reliability**: Robust error handling
4. **Scalability**: Clear scaling path
5. **Quality**: Human-in-the-loop gates

The design balances automation with control, speed with quality, and simplicity with extensibility.
