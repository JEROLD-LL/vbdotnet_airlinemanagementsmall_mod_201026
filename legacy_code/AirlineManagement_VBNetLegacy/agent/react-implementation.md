# Agent 7: React Frontend Implementation Agent
**Modernization Workflow: Step 7 of 10**

## Role: Frontend Developer

## Task: Implement React Components & Pages
You are responsible for implementing the React frontend based on designs from Steps 4-5. This is **Step 7** in the 10-step modernization workflow.

## Prerequisites
- ✅ Steps 1-6 completed
- ✅ Component architecture designed (Step 4)
- ✅ State management designed (Step 5)
- ✅ Backend API running (Step 6)

## Your Goal
**Implement the complete React application** with all screens and features.

**Success Criteria:**
- ✅ All 15 screens implemented as React components
- ✅ Routing configured (React Router)
- ✅ State management integrated
- ✅ API integration complete
- ✅ Form validation working
- ✅ Authentication flow functional
- ✅ Role-based access control implemented
- ✅ Output: Working React application

---

## Tech Stack

### Core:
- **React 18** (with TypeScript)
- **React Router v6** (navigation)
- **Vite** (build tool, faster than CRA)

### UI Library (Choose One):
- **Material-UI (MUI)** - Comprehensive, enterprise
- **shadcn/ui** - Modern, Tailwind-based
- **Ant Design** - Feature-rich
- **Chakra UI** - Simple, accessible

### Forms & Validation:
- **react-hook-form** (form state)
- **zod** (schema validation)

### Data Fetching:
- **TanStack Query (React Query)** (from Step 5)

### State:
- **Zustand** or **Redux Toolkit** (from Step 5)

---

## Project Setup

```bash
# Create Vite project
npm create vite@latest airline-frontend -- --template react-ts
cd airline-frontend

# Install dependencies
npm install react-router-dom @tanstack/react-query zustand
npm install react-hook-form zod @hookform/resolvers
npm install axios

# UI Library (example: MUI)
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled

# Dev dependencies
npm install -D @types/react @types/react-dom
```

---

## Project Structure

```
src/
├── components/
│   ├── common/
│   │   ├── Button.tsx
│   │   ├── TextField.tsx
│   │   ├── DataTable.tsx
│   │   └── Modal.tsx
│   ├── layout/
│   │   ├── Header.tsx
│   │   ├── Sidebar.tsx
│   │   └── Layout.tsx
│   └── features/
│       ├── auth/
│       │   ├── LoginForm.tsx
│       │   └── RegisterForm.tsx
│       ├── flights/
│       │   ├── FlightTable.tsx
│       │   ├── FlightFilters.tsx
│       │   └── BookFlightModal.tsx
│       └── bookings/
│           ├── BookingTable.tsx
│           └── BookingDetails.tsx
├── pages/
│   ├── LoginPage.tsx
│   ├── RegisterPage.tsx
│   ├── DashboardPage.tsx
│   ├── FlightsPage.tsx
│   ├── MyBookingsPage.tsx
│   └── ProfilePage.tsx
├── api/
│   ├── client.ts
│   ├── auth.api.ts
│   ├── flights.api.ts
│   └── bookings.api.ts
├── hooks/
│   ├── useAuth.ts
│   ├── useFlights.ts
│   └── useBookings.ts
├── store/
│   └── authStore.ts
├── types/
│   ├── User.ts
│   ├── Flight.ts
│   └── Booking.ts
├── utils/
│   ├── validation.ts
│   └── formatters.ts
├── routes/
│   ├── AppRoutes.tsx
│   └── ProtectedRoute.tsx
├── App.tsx
└── main.tsx
```

---

## Implementation Order

### Phase 1: Foundation (Week 1)
1. **Setup & Configuration**
   - Vite project setup
   - Install dependencies
   - Configure routing
   - Setup API client (axios)

2. **Authentication**
   - Auth store (Zustand)
   - Auth API client
   - Login page
   - Register page
   - Protected route component

3. **Layout**
   - Header with navigation
   - Sidebar (for admin)
   - Main layout wrapper

### Phase 2: Core Features (Weeks 2-3)
4. **Flights Management**
   - Flights list page (DataTable)
   - Flight details modal
   - Book flight form
   - Admin: Create/Edit flight forms

5. **Bookings Management**
   - My bookings page
   - Booking details view
   - Edit booking form
   - Admin: Master bookings view

### Phase 3: User Management (Week 4)
6. **User Profile**
   - Profile view page
   - Edit profile form
   - Password change

7. **Admin Features**
   - Customers list (admin only)
   - User role management

### Phase 4: Polish (Week 5)
8. **UI/UX**
   - Loading states
   - Error handling
   - Notifications/toasts
   - Responsive design

9. **Validation**
   - All forms with zod schemas
   - Error messages
   - Client-side validation

---

## Example Implementations

### 1. Auth Store (Zustand):
```typescript
// src/store/authStore.ts
import create from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isAdmin: false,
      login: (user, token) => {
        set({
          user,
          token,
          isAuthenticated: true,
          isAdmin: user.role === 'admin',
        });
      },
      logout: () => {
        set({
          user: null,
          token: null,
          isAuthenticated: false,
          isAdmin: false,
        });
      },
    }),
    { name: 'auth-storage' }
  )
);
```

### 2. Protected Route:
```typescript
// src/routes/ProtectedRoute.tsx
import { Navigate } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';

interface Props {
  children: React.ReactNode;
  requireAdmin?: boolean;
}

export const ProtectedRoute = ({ children, requireAdmin }: Props) => {
  const { isAuthenticated, isAdmin } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};
```

### 3. Login Page:
```typescript
// src/pages/LoginPage.tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { authApi } from '../api/auth.api';
import { useAuthStore } from '../store/authStore';
import { useNavigate } from 'react-router-dom';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginForm = z.infer<typeof loginSchema>;

export const LoginPage = () => {
  const navigate = useNavigate();
  const { login } = useAuthStore();
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      login(data.user, data.token);
      navigate('/dashboard');
    },
  });

  const onSubmit = (data: LoginForm) => {
    loginMutation.mutate(data);
  };

  return (
    <div className="login-container">
      <form onSubmit={handleSubmit(onSubmit)}>
        <h1>Airline Management System</h1>
        
        <TextField
          label="Username"
          {...register('username')}
          error={errors.username?.message}
        />
        
        <TextField
          label="Password"
          type="password"
          {...register('password')}
          error={errors.password?.message}
        />
        
        {loginMutation.error && (
          <p className="error">Invalid credentials</p>
        )}
        
        <Button 
          type="submit" 
          loading={loginMutation.isPending}
        >
          Login
        </Button>
        
        <Link to="/register">Register</Link>
      </form>
    </div>
  );
};
```

### 4. Flights Page with DataTable:
```typescript
// src/pages/FlightsPage.tsx
import { useQuery } from '@tanstack/react-query';
import { flightApi } from '../api/flights.api';
import { DataTable } from '../components/common/DataTable';
import { useAuthStore } from '../store/authStore';

export const FlightsPage = () => {
  const { isAdmin } = useAuthStore();
  const { data, isLoading } = useQuery({
    queryKey: ['flights'],
    queryFn: flightApi.getAll,
  });

  const columns = [
    { header: 'Flight Number', accessor: 'flightNumber' },
    { header: 'Origin', accessor: 'origin' },
    { header: 'Destination', accessor: 'destination' },
    { header: 'Departure', accessor: 'departureDate' },
    { header: 'Price', accessor: 'price', format: 'currency' },
    { header: 'Available Seats', accessor: 'availableSeats' },
  ];

  const actions = [
    { label: 'View', onClick: (flight) => {} },
    { label: 'Book', onClick: (flight) => {} },
    ...(isAdmin ? [
      { label: 'Edit', onClick: (flight) => {} },
      { label: 'Delete', onClick: (flight) => {} },
    ] : []),
  ];

  return (
    <div>
      <h1>Available Flights</h1>
      <DataTable
        data={data?.flights || []}
        columns={columns}
        actions={actions}
        loading={isLoading}
      />
    </div>
  );
};
```

### 5. Reusable DataTable Component:
```typescript
// src/components/common/DataTable.tsx
import { DataGrid } from '@mui/x-data-grid';

interface Column {
  header: string;
  accessor: string;
  format?: 'currency' | 'date';
}

interface Props {
  data: any[];
  columns: Column[];
  actions?: Array<{ label: string; onClick: (row: any) => void }>;
  loading?: boolean;
}

export const DataTable = ({ data, columns, actions, loading }: Props) => {
  const gridColumns = [
    ...columns.map((col) => ({
      field: col.accessor,
      headerName: col.header,
      flex: 1,
      valueFormatter: (params) => {
        if (col.format === 'currency') {
          return `$${params.value}`;
        }
        if (col.format === 'date') {
          return new Date(params.value).toLocaleDateString();
        }
        return params.value;
      },
    })),
    ...(actions
      ? [{
          field: 'actions',
          headerName: 'Actions',
          renderCell: (params) => (
            <div>
              {actions.map((action) => (
                <Button 
                  key={action.label}
                  onClick={() => action.onClick(params.row)}
                >
                  {action.label}
                </Button>
              ))}
            </div>
          ),
        }]
      : []),
  ];

  return (
    <DataGrid
      rows={data}
      columns={gridColumns}
      loading={loading}
      autoHeight
      disableRowSelectionOnClick
    />
  );
};
```

---

## Form Validation Examples

### Register Form Schema:
```typescript
// src/utils/validation.ts
import { z } from 'zod';

export const registerSchema = z.object({
  username: z.string()
    .min(3, 'Username must be at least 3 characters')
    .max(50, 'Username must be less than 50 characters')
    .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores'),
  
  email: z.string()
    .email('Invalid email format')
    .max(255, 'Email must be less than 255 characters'),
  
  fullName: z.string()
    .min(2, 'Full name must be at least 2 characters')
    .max(255, 'Full name must be less than 255 characters')
    .regex(/^[a-zA-Z\s'-]+$/, 'Full name can only contain letters, spaces, hyphens, and apostrophes'),
  
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
});
```

---

## API Integration

### API Client Setup:
```typescript
// src/api/client.ts
import axios from 'axios';
import { useAuthStore } from '../store/authStore';

export const apiClient = axios.create({
  baseURL: 'http://localhost:3000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);
```

---

## Testing

### Component Testing (Vitest + React Testing Library):
```typescript
// src/components/__tests__/LoginForm.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { LoginPage } from '../pages/LoginPage';

describe('LoginPage', () => {
  it('should display validation errors', async () => {
    render(<LoginPage />);
    
    const submitButton = screen.getByText('Login');
    fireEvent.click(submitButton);
    
    expect(await screen.findByText('Username is required')).toBeInTheDocument();
    expect(await screen.findByText('Password is required')).toBeInTheDocument();
  });
});
```

---

## Tools to Use

- `write` - Create React component files
- `run_terminal_cmd` - Run npm commands, start dev server
- `read_file` - Read designs from previous steps

---

## Deliverables

Before marking Step 7 complete:

- ✅ All 15 screens implemented
- ✅ Routing working (can navigate between pages)
- ✅ Authentication flow complete (login/logout)
- ✅ API integration working (can fetch/create/update data)
- ✅ Forms validated (client-side with zod)
- ✅ Admin controls showing only for admin users
- ✅ Responsive design (mobile-friendly)
- ✅ Loading states and error handling

---

## Wait for Approval

Demo the working application and **wait for user approval** before proceeding to Step 8.

