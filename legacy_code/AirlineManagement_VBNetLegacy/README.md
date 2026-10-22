# VB.NET Legacy Application - Airline Management System

## Overview

This is a **VB.NET Windows Forms** legacy application that implements all features from REFERENCE_FSD.md. This application will serve as the legacy system that will later be migrated to ReactJS frontend.

## Project Structure

```
VBNetLegacy/
├── Models/              # User, Flight, Booking entities
├── Data/                # DatabaseHelper (PostgreSQL connection)
├── Repositories/        # UserRepository, FlightRepository, BookingRepository
├── Services/            # BookingService, ValidationHelper, SessionManager
├── Forms/               # All Windows Forms UI screens
│   ├── LoginForm.vb
│   ├── RegisterForm.vb
│   ├── MainForm.vb
│   ├── FlightsForm.vb
│   ├── BookFlightForm.vb
│   ├── MyBookingsForm.vb
│   ├── CreateFlightForm.vb (Admin)
│   ├── CustomersForm.vb (Admin)
│   └── ... (all other forms)
├── Program.vb           # Application entry point
└── AirlineManagement.vbproj
```

## Requirements

- **.NET 6.0 SDK** or later
- **Windows** (Windows Forms requires Windows)
- **PostgreSQL** database
- **Visual Studio 2022** or later (recommended)

## Database Configuration

The application uses PostgreSQL with password: `postgres123`

Connection string is in `Data/DatabaseHelper.vb`:
```vb
Private Shared ReadOnly ConnectionString As String = "Host=localhost;Database=AirlineManagement;Username=postgres;Password=postgres123"
```

## Setup Instructions

1. **Create Database:**
   - Run `database/schema_postgresql.sql` in PostgreSQL
   - Database name: `AirlineManagement`

2. **Open Project:**
   - Open `AirlineManagement.vbproj` in Visual Studio
   - Or use: `dotnet restore` and `dotnet build`

3. **Run Application:**
   - Press F5 in Visual Studio
   - Or use: `dotnet run`

## Default Credentials

- **Username:** `admin`
- **Password:** `admin123`

## Features Implemented

All features from REFERENCE_FSD.md:

### User Features
- ✅ User Registration (RegisterForm)
- ✅ User Login (LoginForm)
- ✅ View Flights (FlightsForm)
- ✅ Book Flights (BookFlightForm)
- ✅ View Own Bookings (MyBookingsForm)
- ✅ Edit Bookings (EditBookingForm)
- ✅ Delete Bookings
- ✅ Profile Management (ProfileForm, EditProfileForm)

### Admin Features
- ✅ Create Flights (CreateFlightForm)
- ✅ Edit Flights (EditFlightForm)
- ✅ Delete Flights
- ✅ View All Customers (CustomersForm)
- ✅ View All Bookings (MasterBookingsForm)

### Business Logic
- ✅ Transaction Management Pattern (BookingService)
- ✅ All validation rules (ValidationHelper)
- ✅ Session management (SessionManager)
- ✅ Role-based access control

## UI Screens

All screens are Windows Forms with:
- TextBoxes for input
- DataGridView for data display
- Buttons for actions
- Labels for information
- Error messages displayed in red labels

## Next Steps

After this legacy application is complete, you can:
1. Analyze the UI screens (forms, controls, layout)
2. Create wireframes from the Windows Forms
3. Document UI flow and interactions
4. Migrate to ReactJS frontend while keeping backend unchanged

## Notes

- This is a **Windows Forms** application (desktop GUI)
- Runs on **Windows** only (Windows Forms requirement)
- Uses **VB.NET** programming language
- Database: **PostgreSQL**
- All FSD requirements implemented

