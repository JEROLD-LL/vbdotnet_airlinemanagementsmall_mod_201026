# Agent 8: Testing & Integration Agent
**Modernization Workflow: Step 8 of 10**

## Role: QA Engineer & Integration Specialist

## Task: Test & Integrate Frontend + Backend
You are responsible for comprehensive testing and integration of the complete application. This is **Step 8** in the 10-step modernization workflow.

## Prerequisites
- ✅ Steps 1-7 completed
- ✅ Backend API implemented (Step 6)
- ✅ React frontend implemented (Step 7)

## Your Goal
**Ensure the application works end-to-end** with comprehensive testing.

**Success Criteria:**
- ✅ Unit tests for backend (>80% coverage)
- ✅ Unit tests for frontend (>70% coverage)
- ✅ Integration tests for API endpoints
- ✅ E2E tests for critical user flows
- ✅ All tests passing
- ✅ Output: Test reports + test documentation

---

## Testing Strategy

### 1. Backend Testing (Node.js example)
```bash
npm install -D jest @types/jest supertest
npm install -D @testing-library/jest-dom
```

**Test Types:**
- **Unit Tests:** Services, utilities (Jest)
- **Integration Tests:** API endpoints (Supertest)
- **Database Tests:** Repository layer (Test DB)

### 2. Frontend Testing
```bash
npm install -D vitest @testing-library/react @testing-library/user-event
npm install -D @testing-library/jest-dom jsdom
```

**Test Types:**
- **Component Tests:** Individual components (Vitest + Testing Library)
- **Hook Tests:** Custom hooks
- **Integration Tests:** Page components with API mocking

### 3. E2E Testing
```bash
npm install -D playwright
# or
npm install -D cypress
```

**Test Flows:**
- User registration & login
- Browse flights & book
- View & edit bookings
- Admin: Create/edit flights

---

## Test Implementation

### Backend Unit Test Example:
```typescript
// tests/services/auth.service.test.ts
import { AuthService } from '../../src/services/auth.service';
import bcrypt from 'bcrypt';

describe('AuthService', () => {
  describe('hashPassword', () => {
    it('should hash password with bcrypt', async () => {
      const password = 'TestPassword123!';
      const hash = await AuthService.hashPassword(password);
      
      expect(hash).not.toBe(password);
      expect(await bcrypt.compare(password, hash)).toBe(true);
    });
  });

  describe('verifyPassword', () => {
    it('should return true for correct password', async () => {
      const password = 'TestPassword123!';
      const hash = await AuthService.hashPassword(password);
      
      const isValid = await AuthService.verifyPassword(password, hash);
      expect(isValid).toBe(true);
    });

    it('should return false for incorrect password', async () => {
      const password = 'TestPassword123!';
      const hash = await AuthService.hashPassword(password);
      
      const isValid = await AuthService.verifyPassword('WrongPassword', hash);
      expect(isValid).toBe(false);
    });
  });
});
```

### Backend Integration Test Example:
```typescript
// tests/integration/auth.test.ts
import request from 'supertest';
import app from '../../src/app';
import { prisma } from '../../src/db';

describe('POST /api/auth/login', () => {
  beforeAll(async () => {
    // Setup test database
    await prisma.$connect();
  });

  afterAll(async () => {
    await prisma.$disconnect();
  });

  beforeEach(async () => {
    // Clean database
    await prisma.user.deleteMany();
    
    // Create test user
    await prisma.user.create({
      data: {
        username: 'testuser',
        password: await bcrypt.hash('password123', 12),
        email: 'test@example.com',
        fullName: 'Test User',
        role: 'user',
      },
    });
  });

  it('should return token for valid credentials', async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({
        username: 'testuser',
        password: 'password123',
      });

    expect(response.status).toBe(200);
    expect(response.body.success).toBe(true);
    expect(response.body.data.token).toBeDefined();
    expect(response.body.data.user.username).toBe('testuser');
  });

  it('should return 401 for invalid credentials', async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({
        username: 'testuser',
        password: 'wrongpassword',
      });

    expect(response.status).toBe(401);
    expect(response.body.success).toBe(false);
  });

  it('should return 400 for missing fields', async () => {
    const response = await request(app)
      .post('/api/auth/login')
      .send({ username: 'testuser' });

    expect(response.status).toBe(400);
  });
});
```

### Frontend Component Test Example:
```typescript
// src/components/__tests__/LoginForm.test.tsx
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { LoginPage } from '../../pages/LoginPage';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: false } },
});

const renderWithProviders = (component) => {
  return render(
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        {component}
      </QueryClientProvider>
    </BrowserRouter>
  );
};

describe('LoginPage', () => {
  it('should render login form', () => {
    renderWithProviders(<LoginPage />);
    
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('should show validation errors for empty fields', async () => {
    renderWithProviders(<LoginPage />);
    
    const submitButton = screen.getByRole('button', { name: /login/i });
    fireEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText(/username is required/i)).toBeInTheDocument();
      expect(screen.getByText(/password is required/i)).toBeInTheDocument();
    });
  });

  it('should call login API on submit', async () => {
    const mockLogin = vi.fn().mockResolvedValue({
      user: { id: 1, username: 'test', role: 'user' },
      token: 'fake-token',
    });

    vi.mock('../../api/auth.api', () => ({
      authApi: { login: mockLogin },
    }));

    renderWithProviders(<LoginPage />);

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'testuser' },
    });
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password123' },
    });
    fireEvent.click(screen.getByRole('button', { name: /login/i }));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      });
    });
  });
});
```

### E2E Test Example (Playwright):
```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication Flow', () => {
  test('should login successfully', async ({ page }) => {
    await page.goto('http://localhost:5173');

    // Fill login form
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button:has-text("Login")');

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.locator('text=Welcome, Test User')).toBeVisible();
  });

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('http://localhost:5173');

    await page.fill('input[name="username"]', 'wronguser');
    await page.fill('input[name="password"]', 'wrongpass');
    await page.click('button:has-text("Login")');

    // Should show error message
    await expect(page.locator('text=Invalid credentials')).toBeVisible();
  });
});

test.describe('Booking Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login first
    await page.goto('http://localhost:5173');
    await page.fill('input[name="username"]', 'testuser');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button:has-text("Login")');
    await page.waitForURL(/.*dashboard/);
  });

  test('should book a flight', async ({ page }) => {
    // Navigate to flights
    await page.click('text=Flights');

    // Select a flight
    await page.click('button:has-text("Book")');

    // Fill booking form
    await page.fill('input[name="passengerName"]', 'John Doe');
    await page.fill('input[name="passengerEmail"]', 'john@example.com');
    await page.fill('input[name="seatNumber"]', '12A');
    await page.click('button:has-text("Book Flight")');

    // Should show success message
    await expect(page.locator('text=Booking successful')).toBeVisible();
  });
});
```

---

## Test Coverage Requirements

### Backend:
- **Services:** 90%+ coverage
- **Controllers:** 85%+ coverage
- **Middleware:** 90%+ coverage
- **Overall:** 80%+ coverage

### Frontend:
- **Components:** 70%+ coverage
- **Pages:** 75%+ coverage
- **Hooks:** 85%+ coverage
- **Utils:** 90%+ coverage
- **Overall:** 70%+ coverage

---

## Test Documentation

**File:** `.cursor/plans/testing-strategy.md`

```markdown
# Testing Strategy & Results

## Test Coverage

### Backend
- Unit Tests: 156 tests, 94% coverage
- Integration Tests: 48 tests, 89% coverage
- Total: 204 tests, 91% coverage

### Frontend
- Component Tests: 87 tests, 76% coverage
- Integration Tests: 24 tests, 82% coverage
- Total: 111 tests, 78% coverage

### E2E
- Critical Flows: 12 scenarios
- All passing

## Test Execution

### Run all tests:
```bash
# Backend
cd backend && npm test

# Frontend
cd frontend && npm test

# E2E
npx playwright test
```

## CI/CD Integration
Tests run automatically on:
- Every pull request
- Before deployment
- Nightly (full E2E suite)
```

---

## Integration Testing

### Test Checklist:

- ✅ **Authentication Flow**
  - Login with valid credentials
  - Login with invalid credentials
  - Logout
  - Session timeout
  - Token refresh

- ✅ **User Registration**
  - Register new user
  - Duplicate username/email validation
  - Password strength validation

- ✅ **Flight Management**
  - List flights
  - View flight details
  - Search/filter flights
  - Admin: Create flight
  - Admin: Edit flight
  - Admin: Delete flight

- ✅ **Booking Management**
  - Book flight
  - View bookings
  - Edit booking
  - Delete booking
  - Admin: View all bookings

- ✅ **User Profile**
  - View profile
  - Edit profile
  - Change password

- ✅ **Admin Features**
  - View customers
  - Role-based access control

---

## Tools to Use

- `run_terminal_cmd` - Run test commands
- `write` - Create test files and documentation
- `read_file` - Read code to write tests for

---

## Deliverables

Before marking Step 8 complete:

- ✅ All tests passing (backend + frontend + E2E)
- ✅ Coverage targets met (>80% backend, >70% frontend)
- ✅ Test documentation created
- ✅ CI/CD pipeline configured
- ✅ Test reports generated

---

## Wait for Approval

Present test results and coverage reports, then **wait for user approval** before proceeding to Step 9.

