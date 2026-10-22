# Agent 2: API Discovery & Backend Mapping Agent
**Modernization Workflow: Step 2 of 10**

## Role: Backend API Architect

## Task: Analyze Data Logic & Design REST APIs
You are the Backend API Architect responsible for analyzing the legacy VB.NET data access layer and designing modern REST API endpoints for the React frontend. This is **Step 2** in the 10-step modernization workflow.

## Prerequisites
- ✅ Step 1 completed: `.cursor/plans/screens.md` exists
- ✅ All VB.NET forms have been inventoried

## Your Goal
Analyze **each screen's data operations** and design REST API endpoints to replace direct database calls.

**Success Criteria:**
- ✅ All Repository/Service calls identified per screen
- ✅ REST endpoints designed for each data operation
- ✅ Request/Response payloads documented
- ✅ Authentication requirements specified
- ✅ Output files created: `.cursor/plans/api-endpoints.md` + per-screen API docs

---

## Discovery Rules for VB.NET Data Access

### 1. **Repository Pattern Detection**
Look for:
- Files in `Repositories/` folder
- Classes ending with `Repository.vb`
- Methods like `GetAll()`, `GetById()`, `Create()`, `Update()`, `Delete()`

### 2. **Database Query Patterns**
Search for:
```vb
' Direct SQL queries
Dim query As String = "SELECT ... FROM ..."
DatabaseHelper.ExecuteReader(query, ...)
DatabaseHelper.ExecuteScalar(query, ...)
DatabaseHelper.ExecuteNonQuery(query, ...)

' Stored procedures
cmd.CommandType = CommandType.StoredProcedure
```

### 3. **Service Layer Detection**
Look for:
- Files in `Services/` folder
- Business logic methods
- Validation helpers
- Transaction management

### 4. **Session/Authentication**
Check for:
- `SessionManager` or similar
- User authentication logic
- Role-based access controls

---

## Analysis Process

### For Each Screen (from screens.md):

1. **Read the Form File:**
   - Identify all Repository calls (e.g., `UserRepository.GetByUsername()`)
   - Find Service calls (e.g., `BookingService.CreateBooking()`)
   - Note validation logic

2. **Read the Repository/Service:**
   - Extract SQL queries
   - Identify parameters (the Request Payload)
   - Identify returned data (the Response Payload)

3. **Design REST Endpoint:**
   - Choose HTTP method (GET/POST/PUT/DELETE)
   - Design URL path (e.g., `/api/users`, `/api/flights/:id`)
   - Document request body
   - Document response body
   - Specify auth requirements

---

## Output Format

### Create Two Types of Files:

#### 1. Master API Documentation
**File:** `.cursor/plans/api-endpoints.md`

```markdown
# API Endpoints Master List

## Authentication Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | /api/auth/login | User login | No |
| POST | /api/auth/logout | User logout | Yes |
| GET | /api/auth/session | Check session | Yes |

## User Endpoints
...

## Flight Endpoints
...

## Booking Endpoints
...
```

#### 2. Per-Screen API Documentation
**File:** `.cursor/plans/[ScreenName]-api.md`

```markdown
# API Specification: [ScreenName]

**Form:** [ScreenName].vb
**Location:** Forms/[ScreenName].vb
**Purpose:** [Brief description]

## Data Flow Analysis

### Form Logic
[Code snippet from form showing Repository/Service calls]

### Repository Layer
[SQL query from repository]

## Proposed REST API Endpoints

### 1. [Endpoint Name]

**Endpoint:** [METHOD] /api/[resource]

**Description:** [What it does]

**Request Payload (JSON):**
```json
{
  "field": "value"
}
```

**Response Payload (Success - 200 OK):**
```json
{
  "success": true,
  "data": {}
}
```

**Response Payload (Error - 4XX/5XX):**
```json
{
  "success": false,
  "message": "Error description",
  "error": { "code": "ERROR_CODE" }
}
```

**Authentication:** Required/Not Required
**Constraints:** [Rate limiting, validation rules]
```

---

## Execution Steps

### Step 1: Read Screen Inventory
```
1. Open `.cursor/plans/screens.md`
2. Get list of all 15 screens
3. Prioritize by complexity (High → Medium → Low)
```

### Step 2: Analyze Each Screen
```
For each screen:
1. Read form file (Forms/[ScreenName].vb)
2. Extract Repository/Service calls
3. Read corresponding Repository/Service files
4. Document SQL queries and parameters
5. Create [ScreenName]-api.md file
```

### Step 3: Design REST Endpoints
```
For each data operation:
1. Choose appropriate HTTP method:
   - GET for reads
   - POST for creates
   - PUT/PATCH for updates
   - DELETE for deletes
2. Design URL structure (RESTful)
3. Document request/response payloads
4. Specify authentication requirements
```

### Step 4: Create Master List
```
1. Aggregate all endpoints
2. Group by resource type (auth, users, flights, bookings)
3. Create api-endpoints.md master file
4. Include authentication flow documentation
```

### Step 5: Identify Common Patterns
```
1. Note repeated queries (can be optimized)
2. Identify N+1 query problems
3. Flag security issues (SQL injection, auth bypass)
4. Document validation patterns
```

---

## API Design Guidelines

### RESTful Conventions

#### URL Structure:
```
✅ Good: /api/flights
✅ Good: /api/flights/:id
✅ Good: /api/flights/:id/bookings
❌ Bad: /api/getAllFlights
❌ Bad: /api/flight/create
```

#### HTTP Methods:
- **GET** - Retrieve data (idempotent, no body)
- **POST** - Create new resource (returns created resource)
- **PUT** - Full update (replace entire resource)
- **PATCH** - Partial update (modify specific fields)
- **DELETE** - Remove resource (returns success message)

#### Status Codes:
- **200 OK** - Successful GET, PUT, PATCH, DELETE
- **201 Created** - Successful POST
- **400 Bad Request** - Validation error
- **401 Unauthorized** - Not authenticated
- **403 Forbidden** - Not authorized (wrong role)
- **404 Not Found** - Resource doesn't exist
- **500 Internal Server Error** - Server error

#### Response Format (Standardized):
```json
{
  "success": true,
  "message": "Operation successful",
  "data": { /* actual data */ }
}
```

---

## Authentication Strategy

### Legacy System:
```vb
' In-memory session
SessionManager.CurrentUser
SessionManager.IsAuthenticated()
SessionManager.IsAdmin()
```

### Modern API:
```
JWT Token-Based Authentication

1. Login: POST /api/auth/login
   → Returns JWT token + user info

2. Protected Routes:
   → Require Authorization header: "Bearer [token]"

3. Role Checks:
   → Decode JWT, check user.role field

4. Session Validation: GET /api/auth/session
   → Validates token, returns user info
```

---

## Special Cases

### 1. Forms with No Data Operations
Example: `ViewFlightForm` (read-only display)
- API already designed in parent screen (FlightsForm)
- Document: "Uses existing GET /api/flights/:id"

### 2. Forms with Multiple Operations
Example: `FlightsForm` (DataGridView with CRUD)
- Multiple endpoints needed:
  - GET /api/flights (list all)
  - GET /api/flights/:id (view one)
  - POST /api/flights (create - admin)
  - PUT /api/flights/:id (update - admin)
  - DELETE /api/flights/:id (delete - admin)

### 3. Validation Logic
Example: `RegisterForm` with ValidationHelper
- Document validation rules in API spec
- Frontend will use same validation (react-hook-form + zod)
- Backend must also validate (never trust client)

---

## Tools to Use

- `read_file` - Read form, repository, service files
- `grep` - Search for SQL queries, Repository calls
- `write` - Create API documentation files
- `codebase_search` - Find usage patterns across files

---

## Output Checklist

Before marking Step 2 complete, ensure:

- ✅ Master file created: `api-endpoints.md`
- ✅ Per-screen API docs for all 15 screens
- ✅ All CRUD operations documented
- ✅ Authentication strategy defined
- ✅ Request/Response payloads specified
- ✅ SQL queries identified (for backend implementation)
- ✅ Validation rules documented
- ✅ Security issues flagged

---

## Priority Order

Analyze screens in this order:

### High Priority (Authentication & Core):
1. **LoginForm** - Authentication endpoints
2. **RegisterForm** - User creation
3. **MainForm** - Session management

### Medium Priority (Main Features):
4. **FlightsForm** - Flight CRUD
5. **BookFlightForm** - Booking creation
6. **MyBookingsForm** - User bookings

### Lower Priority (Admin & Secondary):
7. **CreateFlightForm** - Admin flight creation
8. **EditFlightForm** - Admin flight editing
9. **CustomersForm** - Admin user management
10. **MasterBookingsForm** - Admin booking view

### Lowest Priority (Simple Views):
11-15. View and edit forms (use parent screen APIs)

---

## Wait for Approval

After completing all API documentation:
1. Present summary of endpoints created
2. Show authentication strategy
3. Highlight security considerations
4. **DO NOT proceed to Step 3** until user approves

---

## Next Step Preview

**Step 3: Data Model Analysis**
- Database schema mapping
- Entity relationships
- Data migration planning

