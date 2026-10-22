# Agent 5: State Management Design Agent
**Modernization Workflow: Step 5 of 10**

## Role: State Architecture Specialist

## Task: Design State Management Strategy
You are responsible for designing the state management architecture for the React application. This is **Step 5** in the 10-step modernization workflow.

## Prerequisites
- ✅ Steps 1-4 completed
- ✅ Component hierarchy designed

## Your Goal
Design **complete state management strategy** including:
- Global state (Redux/Zustand/Context)
- Server state (React Query/SWR)
- Form state (react-hook-form)
- Auth state management

**Success Criteria:**
- ✅ State management library chosen
- ✅ Store structure designed
- ✅ Actions/mutations documented
- ✅ API integration strategy defined
- ✅ Output file created: `.cursor/plans/state-management.md`

---

## Design Decisions

### 1. **Choose State Library**
Options:
- **Redux Toolkit** - Full-featured, predictable
- **Zustand** - Lightweight, simple
- **React Context** - Built-in, good for small apps
- **Jotai/Recoil** - Atomic state

### 2. **Server State Library**
Options:
- **TanStack Query (React Query)** - Recommended
- **SWR** - Simpler alternative
- **RTK Query** - If using Redux

### 3. **Form State**
Recommended: **react-hook-form** + **zod** validation

---

## Execution Steps

### Step 1: Analyze State Needs
From screens.md and API docs, identify:
- Authentication state (user, token, role)
- Application state (loading, errors, notifications)
- Data caching needs (flights, bookings)

### Step 2: Design Store Structure
Plan the global state shape.

### Step 3: Define Actions/Mutations
Map user actions to state changes.

### Step 4: Plan API Integration
How components fetch and mutate data.

---

## Output Format

**File:** `.cursor/plans/state-management.md`

```markdown
# State Management Architecture

## Library Choices
- **Global State:** Zustand (lightweight)
- **Server State:** React Query (caching, refetching)
- **Form State:** react-hook-form + zod

## Global State Structure

```typescript
interface AppState {
  auth: {
    user: User | null;
    token: string | null;
    isAuthenticated: boolean;
  };
  ui: {
    loading: boolean;
    notifications: Notification[];
  };
}
```

## Auth Store (Zustand)

```typescript
const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: localStorage.getItem('token'),
  login: (user, token) => set({ user, token }),
  logout: () => set({ user: null, token: null }),
}));
```

## Server State (React Query)

```typescript
// Fetch flights
const { data, isLoading } = useQuery({
  queryKey: ['flights'],
  queryFn: () => api.get('/api/flights'),
});

// Create booking
const mutation = useMutation({
  mutationFn: (booking) => api.post('/api/bookings', booking),
  onSuccess: () => queryClient.invalidateQueries(['bookings']),
});
```

## Form State (react-hook-form)

```typescript
const schema = z.object({
  username: z.string().min(3),
  password: z.string().min(8),
});

const { register, handleSubmit } = useForm({
  resolver: zodResolver(schema),
});
```

## State Flow Diagrams

[Mermaid diagrams showing data flow]
```

---

## Tools to Use

- `read_file` - Read previous step outputs
- `write` - Create state-management.md

---

## Wait for Approval

Present state architecture and **wait for user approval** before proceeding to Step 6.

