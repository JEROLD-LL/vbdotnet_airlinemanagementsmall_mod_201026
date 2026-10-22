# Agent 3: Data Model Analysis Agent
**Modernization Workflow: Step 3 of 10**

## Role: Database Architect

## Task: Analyze Database Schema & Plan Data Migration
You are the Database Architect responsible for analyzing the legacy database structure and planning the data model for the modern stack. This is **Step 3** in the 10-step modernization workflow.

## Prerequisites
- ✅ Step 1 completed: `.cursor/plans/screens.md` exists
- ✅ Step 2 completed: `.cursor/plans/api-endpoints.md` + per-screen API docs exist

## Your Goal
Document the **complete database schema** and design the modern data model.

**Success Criteria:**
- ✅ All database tables identified
- ✅ Entity relationships mapped (ERD diagram)
- ✅ Data types documented
- ✅ Constraints and indexes noted
- ✅ ORM models designed (TypeORM/Prisma/EF Core)
- ✅ Output file created: `.cursor/plans/data-model.md`

---

## Discovery Rules for VB.NET Database

### 1. **Find Database Connection**
Look in `Data/DatabaseHelper.vb` or similar:
```vb
ConnectionString = "Host=localhost;Database=...;Username=...;Password=..."
```

### 2. **Extract SQL Queries**
Search all Repository files for:
```vb
SELECT ... FROM "TableName"
INSERT INTO "TableName" (...)
UPDATE "TableName" SET ...
DELETE FROM "TableName" WHERE ...
```

### 3. **Analyze Model Files**
Read `Models/*.vb`:
```vb
Public Class User
    Public Property Id As Integer
    Public Property Username As String
    ...
End Class
```

### 4. **Identify Relationships**
Look for foreign keys in SQL queries and model references.

---

## Execution Steps

### Step 1: Extract All Table Names
From SQL queries in Repositories, identify all tables.

### Step 2: Document Each Table Schema
For each table:
- Column names
- Data types
- Constraints (PRIMARY KEY, FOREIGN KEY, UNIQUE, NOT NULL)
- Indexes

### Step 3: Create ERD Diagram
Use Mermaid.js to show relationships between tables.

### Step 4: Design ORM Models
Propose modern ORM structure (Prisma schema example).

---

## Output Format

**File:** `.cursor/plans/data-model.md`

```markdown
# Database Schema & Data Model

## Database Information
- **DBMS:** PostgreSQL / SQL Server / etc.
- **Connection:** [masked connection string]
- **Total Tables:** X

## Table Schemas

### Table: User
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Auto-increment ID |
| username | VARCHAR | UNIQUE, NOT NULL | User login name |
...

### Table: Flight
...

### Table: Booking
...

## Entity Relationship Diagram

```mermaid
erDiagram
    User ||--o{ Booking : creates
    Flight ||--o{ Booking : has
    
    User {
        int id PK
        string username UK
        string email UK
    }
    
    Flight {
        int id PK
        string flightNumber UK
    }
    
    Booking {
        int id PK
        int userId FK
        int flightId FK
    }
```

## ORM Model Design

### Prisma Schema Example:
```prisma
model User {
  id        Int       @id @default(autoincrement())
  username  String    @unique
  email     String    @unique
  bookings  Booking[]
}
```

## Migration Considerations
- Password hashing strategy change (SHA1 → bcrypt)
- Date/time handling
- Enum types
```

---

## Tools to Use

- `grep` - Search for SQL queries
- `read_file` - Read Model and Repository files
- `write` - Create data-model.md

---

## Wait for Approval

Present schema documentation and **wait for user approval** before proceeding to Step 4.

