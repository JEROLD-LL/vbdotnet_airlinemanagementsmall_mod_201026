# Agent 6: Backend API Implementation Agent
**Modernization Workflow: Step 6 of 10**

## Role: Backend Developer

## Task: Implement REST API Endpoints
You are responsible for implementing the backend API based on the design from Step 2. This is **Step 6** in the 10-step modernization workflow.

## Prerequisites
- ✅ Steps 1-5 completed
- ✅ API endpoints designed (Step 2)
- ✅ Data model documented (Step 3)

## Your Goal
**Implement the complete REST API** for the React frontend.

**Success Criteria:**
- ✅ All endpoints from api-endpoints.md implemented
- ✅ Authentication middleware created (JWT)
- ✅ Validation middleware added
- ✅ Database queries migrated (use ORM)
- ✅ Error handling implemented
- ✅ API tested (unit + integration tests)
- ✅ Output: Working backend API

---

## Tech Stack Decision

### Backend Framework Options:
1. **Node.js + Express** (JavaScript/TypeScript)
2. **.NET Core Web API** (C# - keep same stack)
3. **NestJS** (TypeScript, enterprise-grade)
4. **FastAPI** (Python, modern & fast)

### ORM Options:
1. **Prisma** (Node.js, excellent DX)
2. **TypeORM** (Node.js, feature-rich)
3. **Entity Framework Core** (.NET)
4. **SQLAlchemy** (Python)

---

## Implementation Steps

### Step 1: Project Setup
```bash
# Example: Node.js + Express + Prisma
npm init -y
npm install express prisma @prisma/client bcrypt jsonwebtoken
npm install -D typescript @types/node @types/express
```

### Step 2: Database Setup
```bash
# Initialize Prisma
npx prisma init

# Create schema (from data-model.md)
# Run migrations
npx prisma migrate dev
```

### Step 3: Implement Auth Endpoints
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/session

### Step 4: Implement Resource Endpoints
- User endpoints
- Flight endpoints
- Booking endpoints

### Step 5: Add Middleware
- Authentication (JWT validation)
- Authorization (role checks)
- Validation (request body validation)
- Error handling

### Step 6: Testing
- Unit tests for services
- Integration tests for endpoints

---

## Code Structure

```
backend/
├── src/
│   ├── controllers/
│   │   ├── auth.controller.ts
│   │   ├── flight.controller.ts
│   │   └── booking.controller.ts
│   ├── services/
│   │   ├── auth.service.ts
│   │   ├── flight.service.ts
│   │   └── booking.service.ts
│   ├── middleware/
│   │   ├── auth.middleware.ts
│   │   ├── validation.middleware.ts
│   │   └── error.middleware.ts
│   ├── routes/
│   │   ├── auth.routes.ts
│   │   ├── flight.routes.ts
│   │   └── booking.routes.ts
│   ├── models/ (or prisma/schema.prisma)
│   └── app.ts
├── tests/
├── package.json
└── tsconfig.json
```

---

## Example Implementation

### Auth Controller (TypeScript + Express):
```typescript
export async function login(req: Request, res: Response) {
  const { username, password } = req.body;
  
  // Find user
  const user = await prisma.user.findUnique({ where: { username } });
  if (!user) {
    return res.status(401).json({ 
      success: false, 
      message: 'Invalid credentials' 
    });
  }
  
  // Verify password (bcrypt, not SHA1!)
  const isValid = await bcrypt.compare(password, user.password);
  if (!isValid) {
    return res.status(401).json({ 
      success: false, 
      message: 'Invalid credentials' 
    });
  }
  
  // Generate JWT
  const token = jwt.sign(
    { userId: user.id, role: user.role },
    process.env.JWT_SECRET!,
    { expiresIn: '30m' }
  );
  
  res.json({
    success: true,
    data: {
      user: { id: user.id, username: user.username, role: user.role },
      token,
      expiresIn: 1800
    }
  });
}
```

---

## Security Checklist

- ✅ Replace SHA1 with bcrypt (cost factor 12)
- ✅ Use JWT for stateless auth
- ✅ Validate all inputs (use Zod or Joi)
- ✅ Sanitize SQL (use ORM, never string concatenation)
- ✅ Rate limiting (express-rate-limit)
- ✅ CORS configuration
- ✅ HTTPS in production
- ✅ Environment variables for secrets
- ✅ Log security events

---

## Migration from VB.NET

### Password Migration Strategy:
```typescript
// Check if user has old SHA1 password
if (user.passwordHashType === 'SHA1') {
  // Verify with SHA1
  const sha1Hash = crypto.createHash('sha1').update(password).digest('hex');
  if (sha1Hash.toUpperCase() === user.password) {
    // Correct password, rehash with bcrypt
    const bcryptHash = await bcrypt.hash(password, 12);
    await prisma.user.update({
      where: { id: user.id },
      data: { password: bcryptHash, passwordHashType: 'BCRYPT' }
    });
    // Continue with login...
  }
}
```

---

## Testing Strategy

### Unit Tests:
```typescript
describe('AuthService', () => {
  it('should hash passwords with bcrypt', async () => {
    const hash = await authService.hashPassword('password123');
    expect(hash).not.toBe('password123');
    expect(await bcrypt.compare('password123', hash)).toBe(true);
  });
});
```

### Integration Tests:
```typescript
describe('POST /api/auth/login', () => {
  it('should return token for valid credentials', async () => {
    const res = await request(app)
      .post('/api/auth/login')
      .send({ username: 'test', password: 'password' });
    
    expect(res.status).toBe(200);
    expect(res.body.data.token).toBeDefined();
  });
});
```

---

## Tools to Use

- `read_file` - Read API specs from Step 2
- `write` - Create backend code files
- `run_terminal_cmd` - Run npm install, migrations, tests

---

## Deliverables

Before marking Step 6 complete:

- ✅ All endpoints implemented and tested
- ✅ Authentication working (JWT)
- ✅ Database migrations run
- ✅ Postman/Thunder Client collection for testing
- ✅ API documentation updated with implementation notes

---

## Wait for Approval

Test all endpoints, present test results, and **wait for user approval** before proceeding to Step 7.

