# LUMIEN - SaaS Multi-Tenant Fraud Workflow Platform

A production-ready, SaaS-based multi-tenant fraud detection and case management system for Indian banks integrated with the I4C (Indian Cyber Crime Coordination Centre) network.

## Architecture Overview

### Multi-Tenant SaaS Model (Shared Database, Row-Level Isolation)

```
┌─────────────────────────────────────────────────────────────┐
│                    LUMIEN SaaS Platform                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Bank A    │  │   Bank B    │  │   Bank C    │          │
│  │  (Tenant 1) │  │  (Tenant 2) │  │  (Tenant 3) │          │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘          │
│         │                │                │                   │
│         └────────────────┼────────────────┘                   │
│                          ▼                                   │
│              ┌─────────────────────┐                         │
│              │   PostgreSQL DB     │                         │
│              │  (Shared Schema)   │                         │
│              │  bank_id isolation │                         │
│              └─────────────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- **PostgreSQL Database**: Production-ready relational database
- **Row-Level Security**: Complete data isolation per bank using `bank_id`
- **JWT Authentication**: Secure token-based auth with embedded tenant info
- **Dynamic Data Loading**: Excel dataset acts as seed data
- **Auto-Provisioning**: New banks automatically available after ingestion
- **Strict Access Control**: Users can only see their bank/branch data

## Project Structure

```
LUMIEN/
├── I4C_Simulated_Demo_Dataset.xlsx    # Source seed data
├── lumien-backend/                  # FastAPI + PostgreSQL Backend
│   ├── app/
│   │   ├── core/                       # Config, security
│   │   │   ├── config.py               # PostgreSQL configuration
│   │   │   └── security.py             # JWT with bank_id/branch_id
│   │   ├── models/                     # SQLAlchemy ORM models
│   │   │   └── models.py               # All tables with bank_id
│   │   ├── routers/                    # API endpoints
│   │   │   ├── auth.py                 # Login + Register
│   │   │   ├── tenant.py               # Multi-tenant APIs
│   │   │   └── ...
│   │   └── main.py                     # FastAPI entry point
│   ├── ingest_demo_dataset.py          # Data ingestion script
│   ├── requirements.txt
│   └── .env                            # Environment variables
├── lumien-frontend/                   # React + TypeScript Frontend
│   ├── src/
│   │   ├── api/index.ts               # API client with tenant APIs
│   │   └── pages/                      # All pages use dynamic data
│   └── package.json
└── README.md                           # This file
```

## Database Schema (PostgreSQL)

### Multi-Tenant Tables (All include bank_id)

| Table | Key Columns | Tenant Isolation |
|-------|-------------|------------------|
| `banks` | id, name, code | N/A (tenant definition) |
| `branches` | id, bank_id, name | bank_id FK |
| `users` | id, bank_id, branch_id | bank_id + branch_id |
| `complaints` | id, bank_id, branch_id | bank_id + branch_id |
| `case_workflows` | id, assigned_bank_id | assigned_bank_id |
| `hold_actions` | id, bank_id, branch_id | bank_id + branch_id |
| `status_updates` | id, bank_id, branch_id | bank_id + branch_id |
| `audit_logs` | id, bank_id, branch_id | bank_id + branch_id |

## Setup Instructions

### Prerequisites

1. **PostgreSQL 14+** installed and running
2. **Python 3.10+**
3. **Node.js 18+**

### Step 1: Install PostgreSQL

**Windows:**
1. Download from https://www.postgresql.org/download/windows/
2. Install with default settings
3. Set password for `postgres` user (remember this!)

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux (Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### Step 2: Create Database

```bash
# Connect to PostgreSQL (use your postgres password)
psql -U postgres -h localhost

# In PostgreSQL console:
CREATE DATABASE fiducia_saas;
\q
```

### Step 3: Backend Setup

```bash
# Navigate to backend directory
cd lumien-backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
venv\Scripts\Activate.ps1
# Windows (cmd.exe):
venv\Scripts\activate.bat
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables (optional - defaults already configured)
# Create .env file:
cat > .env << EOF
DATABASE_URL=postgresql://postgres:password@localhost:5432/fiducia_saas
SECRET_KEY=your-production-secret-key-change-this
EOF
```

### Step 4: Run Data Ingestion (CRITICAL)

This creates all tenant data from the Excel file:

```bash
# Ensure virtual environment is activated
python ingest_demo_dataset.py
```

If you are using the I4C dataset ingestion script (newer integration), you can also run from the project root:

```bash
# From project root (LUMIEN/)
python ingest_i4c_dataset.py
```

You should see output like:
```
Reading dataset from C:\Users\...\I4C_Simulated_Demo_Dataset.xlsx...
Found sheets: ['I4C_Inbound_FraudReports', 'I4C_Incidents', ...]
Clearing existing data...
Existing data cleared.
Ingesting 5 banks...
  Created bank: State Bank of India (SBI) - ID: 1
  Created bank: HDFC Bank (HDFC) - ID: 2
  ...
Ingesting 12 branches...
  Created branch: BR-SBI-001 for bank SBI - ID: 1
  ...
INGESTION SUMMARY
============================================================
Banks ingested: 5
Branches ingested: 12
Users ingested: 8
Complaints ingested: 25
Workflows ingested: 25
Hold actions: 15
Status updates: 10
============================================================
Ingestion completed successfully!
```

### Step 5: Start Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's working:
- API Root: http://localhost:8000/
- API Docs: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/api/v1/openapi.json

### Step 6: Frontend Setup

```bash
# Open new terminal, navigate to frontend
cd lumien-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

Access the application at: http://localhost:5173

## Login Credentials (Seeded)

These users are automatically created on backend startup (see `lumien-backend/app/main.py`).

All seeded users use the same password:

- **Password**: `password123`

### Admin

- **Username**: `admin`
- **Password**: `password123`

### Bank Users

Use any one of the following bank users (depends on which banks exist in your ingested dataset):

- **SBI**: `sbi_user`
- **HDFC**: `hdfc_user`
- **ICICI**: `icici_user`
- **Axis**: `axis_user`
- **PNB**: `pnb_user`
- **Bank of Baroda**: `bob_user`
- **Kotak**: `kotak_user`
- **Yes Bank**: `yes_user`
- **IndusInd**: `indusind_user`
- **IDFC**: `idfc_user`
- **Canara**: `canara_user`
- **Union**: `union_user`
- **UCO**: `uco_user`

## API Reference

### Authentication APIs

| Endpoint | Method | Description | Request Body |
|----------|--------|-------------|--------------|
| `/api/v1/auth/register` | POST | Register new user | `{username, email, password, role, bank_id, branch_id}` |
| `/api/v1/auth/login` | POST | User login | `username=&password=` (form data) |

### Tenant APIs (Multi-Tenant with Isolation)

| Endpoint | Method | Description | Query Params |
|----------|--------|-------------|--------------|
| `/api/v1/tenant/banks` | GET | List banks (tenant-filtered) | - |
| `/api/v1/tenant/branches` | GET | List branches | `bank_id` |
| `/api/v1/tenant/cases` | GET | List cases | `bank_id`, `branch_id`, `status` |
| `/api/v1/tenant/cases/{id}` | GET | Case details | - |
| `/api/v1/tenant/workflow` | GET | List workflows | `case_id`, `bank_id`, `branch_id` |
| `/api/v1/tenant/dashboard` | GET | Dashboard metrics | `bank_id`, `branch_id` |
| `/api/v1/tenant/hold-actions` | GET | Hold actions | `bank_id`, `branch_id` |

## SaaS Data Isolation Rules

### Bank-Level Isolation
```python
# All API endpoints enforce this pattern:
if not is_admin:
    query = query.filter(models.Complaint.bank_id == current_user.bank_id)
```

### Branch-Level Isolation
```python
# Branch users see only their branch:
if current_user.branch_id:
    query = query.filter(models.Complaint.branch_id == current_user.branch_id)
```

### Admin Override
```python
# Admin users can see all data or filter by any bank/branch
if is_admin:
    # Allow any bank_id/branch_id filter
else:
    # Force user's bank_id/branch_id
```

## Testing the SaaS Multi-Tenancy

### Test Scenario 1: Data Isolation

```bash
# 1. Login as SBI user
POST /api/v1/auth/login
{username: "sbi_user", password: "password123"}

# 2. Get cases - should ONLY see SBI cases
GET /api/v1/tenant/cases

# 3. Try to access HDFC case (should fail with 403)
GET /api/v1/tenant/cases/5  # HDFC case ID
```

### Test Scenario 2: New Tenant Onboarding

```bash
# 1. Add new bank data to Excel file
# 2. Re-run ingestion
python ingest_demo_dataset.py

# 3. Register user for new bank
POST /api/v1/auth/register
{
    "username": "newbank_user",
    "email": "user@newbank.com",
    "password": "password123",
    "role": "branch_user",
    "bank_id": 6,  # New bank ID
    "branch_id": 13  # New branch ID
}

# 4. Login and verify isolation
```

### Test Scenario 3: Admin Access

```bash
# 1. Login as admin
POST /api/v1/auth/login
{username: "admin", password: "password123"}

# 2. Admin can see all banks
GET /api/v1/tenant/banks  # Returns all banks

# 3. Admin can filter by any bank
GET /api/v1/tenant/cases?bank_id=2  # HDFC cases
```

## Default Users (After Ingestion)

| Username | Password | Role | Bank | Access |
|----------|----------|------|------|--------|
| `admin` | `password123` | Super Admin | All | Universal |
| `sbi_user` | `password123` | Branch User | SBI | SBI only |
| `hdfc_user` | `password123` | Branch User | HDFC | HDFC only |
| `icici_user` | `password123` | Branch User | ICICI | ICICI only |

## Excel Data Format

The system uses `I4C_Simulated_Demo_Dataset.xlsx` as the source seed data with **14 sheets**:

### Dataset Sheets (14 Total)

1. **I4C_Inbound_FraudReports** - Fraud reports from I4C
2. **I4C_Incidents** - Individual transaction incidents
3. **Bank_Case_Workflow** - Case workflow tracking
4. **Bank_Hold_Actions** - Hold/freeze actions by banks
5. **Bank_StatusUpdate_Request** - I4C status update requests
6. **Bank_StatusUpdate_TxnDetails** - Transaction details for status updates
7. **I4C_StatusUpdate_Response** - I4C response records
8. **Workflow_Timeline** - Multi-stakeholder timeline events
9. **Meta_BankMaster** - Bank master reference data
10. **Meta_StatusCodes** - Status code definitions
11. **Bank_Branches** - Branch master data
12. **Bank_Users** - Bank user accounts
13. **Demo_Scenarios** - Test scenarios

### Meta_BankMaster Sheet
```
bank_code | bank_name      | ifsc_prefix | integration_model | sla_hours
----------|----------------|-------------|-------------------|----------
SBI       | State Bank...  | SBIN        | API               | 24
HDFC      | HDFC Bank      | HDFC        | API               | 24
```

### Bank_Branches Sheet
```
branch_code | bank_code | branch_name    | ifsc_code       | city
------------|-----------|----------------|-----------------|----------
BR-SBI-001  | SBI       | Main Branch    | SBIN0001234     | Mumbai
BR-HDFC-001 | HDFC      | HQ Branch      | HDFC0000567     | Delhi
```

### Bank_Users Sheet
```
username    | bank_code | branch_code | password    | user_type
------------|-----------|-------------|-------------|----------
sbi_user    | SBI       | BR-SBI-001  | password123 | BANK_USER
hdfc_user   | HDFC      | BR-HDFC-001 | password123 | BANK_USER
```

## Production Deployment

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/fiducia_saas
SECRET_KEY=your-256-bit-secret-key-here

# Optional
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEBUG=false
```

### Docker Deployment (Optional)

```dockerfile
# Dockerfile for backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Troubleshooting

### PostgreSQL Connection Issues

```bash
# Test connection
psql -U postgres -h localhost -d fiducia_saas -c "SELECT 1;"

# Check if database exists
psql -U postgres -h localhost -l

# Reset database (CAUTION: deletes all data!)
dropdb -U postgres fiducia_saas
createdb -U postgres fiducia_saas
```

### Ingestion Errors

```bash
# If Excel file not found, check path
python -c "import os; print(os.path.abspath('../I4C_Simulated_Demo_Dataset.xlsx'))"

# If permission errors, check PostgreSQL user permissions
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE fiducia_saas TO postgres;"
```

### API Errors

```bash
# Check if backend is running
curl http://localhost:8000/

# Check database connection
curl http://localhost:8000/api/v1/tenant/banks
```

## Security Considerations

1. **Change default passwords** before production
2. **Use HTTPS** in production
3. **Rotate JWT secret keys** regularly
4. **Enable PostgreSQL SSL** for remote connections
5. **Implement rate limiting** for API endpoints
6. **Regular security audits** of tenant isolation

## Support

For issues or questions:
1. Check the API docs at `/docs`
2. Review the logs: `uvicorn app.main:app --reload --log-level debug`
3. Verify database connectivity
4. Ensure Excel file format is correct

## License

Internal Use Only - FIDUCIA SaaS Platform

## Project Structure

```
LUMIEN/
├── I4C_Simulated_Demo_Dataset.xlsx    # Source data file
├── lumien-backend/                  # FastAPI Backend
│   ├── app/
│   │   ├── core/                     # Config, security
│   │   ├── models/                   # SQLAlchemy models
│   │   ├── routers/                  # API endpoints
│   │   │   ├── auth.py               # Authentication
│   │   │   ├── tenant.py             # Multi-tenant APIs (NEW)
│   │   │   ├── complaints.py         # Case management
│   │   │   ├── bank.py               # Bank operations
│   │   │   ├── admin.py              # Admin endpoints
│   │   │   └── i4c.py                # I4C ingestion
│   │   ├── schemas/                  # Pydantic schemas
│   │   └── main.py                   # FastAPI app entry
│   ├── ingest_demo_dataset.py        # Data ingestion script
│   ├── requirements.txt
│   └── lumien.db                    # SQLite database
├── lumien-frontend/                 # React + Vite Frontend
│   ├── src/
│   │   ├── api/                      # API client
│   │   ├── pages/                    # Page components
│   │   │   ├── Gateway.tsx           # Bank selection (DYNAMIC)
│   │   │   ├── Login.tsx             # Authentication
│   │   │   ├── Dashboard.tsx         # Admin dashboard (DYNAMIC)
│   │   │   ├── CaseInbox.tsx         # Case listing (DYNAMIC)
│   │   │   └── ...
│   │   └── ...
│   └── package.json
└── README.md                         # This file
```

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to backend directory
cd lumien-backend

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Data Ingestion (CRITICAL - Run First)

The system requires data ingestion to populate banks, branches, users, and cases:

```bash
# Ensure you're in the backend directory with venv activated
python ingest_demo_dataset.py
```

This script will:
- Clear existing data
- Load banks from `Meta_BankMaster` sheet
- Load branches from `Bank_Branches` sheet
- Load users from `Bank_Users` sheet
- Load cases from `I4C_Inbound_FraudReports`
- Load workflows from `Bank_Case_Workflow`
- Load hold actions from `Bank_Hold_Actions`
- Link all data with proper foreign keys

### 3. Start Backend Server

```bash
# From fiducia-backend directory
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/api/v1/openapi.json`

### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd lumien-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Endpoints

### Multi-Tenant APIs (`/api/v1/tenant/`)

| Endpoint | Method | Description | Query Params |
|----------|--------|-------------|--------------|
| `/banks` | GET | List all banks | - |
| `/branches` | GET | List branches | `bank_id` |
| `/cases` | GET | List cases | `bank_id`, `branch_id`, `status` |
| `/cases/{id}` | GET | Case details | - |
| `/workflow` | GET | List workflows | `case_id`, `bank_id`, `branch_id` |
| `/dashboard` | GET | Dashboard metrics | `bank_id`, `branch_id` |
| `/hold-actions` | GET | List hold actions | `bank_id`, `branch_id`, `case_id` |

### Authentication (`/api/v1/auth/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/login` | POST | User login (returns bank_id, branch_id in token) |

### Legacy APIs

- `/api/v1/cases/*` - Case management
- `/api/v1/bank/*` - Bank operations
- `/api/v1/admin/*` - Admin endpoints
- `/api/v1/i4c/*` - I4C integration

## User Authentication

Default users are created during data ingestion. Common usernames:

| Username | Role | Bank | Branch |
|----------|------|------|--------|
| `admin` | Super Admin | All | All |
| `sbi_user` | Bank User | SBI | Main Branch |
| `hdfc_user` | Bank User | HDFC | Main Branch |

All default passwords: `password123`

## Key Features

### Dynamic Multi-Tenancy
- Banks, branches, and users loaded from Excel
- No hardcoded bank values in frontend
- Automatic UI updates when data changes

### Bank/Branch Filtering
- Admins can view all banks/branches
- Bank users only see their assigned bank/branch
- Dashboard filters by bank/branch
- Case inbox filters by bank/branch

### Data Security
- JWT tokens with embedded bank_id and branch_id
- API-level filtering based on user permissions
- Audit logs for all actions

## Testing Scenario

To verify the system works with new data:

1. **Modify the Excel file** - Add new banks, branches, or cases
2. **Re-run ingestion**:
   ```bash
   python ingest_demo_dataset.py
   ```
3. **Refresh the UI** - The Gateway page will show new banks
4. **Login with a new bank user** - Only see that bank's data
5. **Verify filtering** - Dashboard and Case Inbox filter correctly

## Database Schema

### Core Tables
- `banks` - Bank information
- `branches` - Branch details with bank foreign key
- `users` - User accounts with bank_id and branch_id
- `complaints` - Fraud cases with bank_id and branch_id
- `case_workflows` - Workflow records with foreign keys
- `hold_actions` - Hold actions with bank/branch links
- `status_updates` - Status history with bank/branch links
- `enrichment_results` - AI enrichment data
- `routing_logs` - Case routing history
- `audit_logs` - Complete audit trail

## Troubleshooting

### Backend Issues

**Database locked error:**
```bash
# Stop the server, delete the DB file, re-run ingestion
del fiducia.db
python ingest_demo_dataset.py
```

**Import errors:**
```bash
# Ensure you're in the correct directory with venv activated
cd lumien-backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload
```

### Frontend Issues

**API connection errors:**
- Verify backend is running on port 8000
- Check CORS settings in `app/core/config.py`

**Blank page after login:**
- Check browser console for errors
- Verify localStorage has `fiducia_token`

## Development Notes

### Adding New Excel Sheets

The ingestion script (`ingest_demo_dataset.py`) dynamically handles new sheets:
1. Add sheet name check in the `ingest()` function
2. Create a new `ingest_*` function for the sheet
3. Link data using the mapping dictionaries (`bank_map`, `branch_map`, etc.)

### Adding New API Endpoints

1. Add endpoint to `app/routers/tenant.py`
2. Use `get_current_user` dependency for authentication
3. Apply bank/branch filtering for non-admin users
4. Return properly serialized data

## Technologies

**Backend:**
- FastAPI (Python)
- SQLAlchemy ORM
- SQLite Database
- JWT Authentication
- Pandas (Excel processing)

**Frontend:**
- React 18
- TypeScript
- Vite
- Tailwind CSS
- Recharts (Charts)
- Lucide React (Icons)

## License

Internal Use Only - FIDUCIA Platform

## Support

For issues or questions, contact the development team.
