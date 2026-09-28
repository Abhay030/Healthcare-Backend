# Healthcare Backend API

A healthcare backend built with **Django + Django REST Framework + PostgreSQL + JWT authentication**.

Users can register and log in, manage their own patient records, manage doctors, and assign doctors to patients.

## 🖥️ Built-in Interactive Playground

Open **http://127.0.0.1:8000/** in your browser — the project serves an interactive UI
(single page, no build step) where you can test every endpoint directly:

- **Register / log in** — the JWT is stored in your browser and attached to every request automatically (with silent refresh when it expires)
- **Patients** — add, edit, delete your patients
- **Doctors** — add, edit, delete doctors
- **Mappings** — assign doctors to patients, look up a patient's doctors, remove mappings
- **Console** — live view of every request and its JSON response with the HTTP status

The UI is a convenience layer on top of the same API documented below — everything it
does, you can also do from Postman or curl.

## Tech Stack

| Component | Choice |
|---|---|
| Framework | Django 5.2 + Django REST Framework |
| Database | PostgreSQL |
| Auth | JWT (djangorestframework-simplejwt) |
| Config | Environment variables (.env) |

## Setup

```bash
# 1. Create a virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Create the database (once)
psql -U postgres -c "CREATE USER healthcare_user WITH PASSWORD 'your-password' CREATEDB;"
psql -U postgres -c "CREATE DATABASE healthcare_db OWNER healthcare_user;"

# 3. Configure environment variables
copy .env.example .env          # then edit .env with your real values

# 4. Run migrations and start the server
python manage.py migrate
python manage.py runserver
```

All sensitive configuration (secret key, DB credentials) lives in `.env` — never commit it.

## Project Structure

```
config/            # Django project (settings, urls)
api/
  models.py        # User (email login), Patient, Doctor, PatientDoctorMapping
  serializers.py   # Validation + serialization
  views.py         # API endpoints
  permissions.py   # Doctor ownership rule
  urls.py          # API routes
```

## API Endpoints

All endpoints except register/login require a JWT: send `Authorization: Bearer <access_token>`.

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register/` | Register with `name`, `email`, `password` (min 8 chars) |
| POST | `/api/auth/login/` | Log in with `email`, `password` → returns `access` + `refresh` tokens |
| POST | `/api/auth/refresh/` | Exchange a refresh token for a new access token |

### Patients — each user sees only their own patients

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/patients/` | Add a patient |
| GET | `/api/patients/` | List my patients |
| GET | `/api/patients/<id>/` | Patient details (404 if not yours) |
| PUT | `/api/patients/<id>/` | Update patient |
| DELETE | `/api/patients/<id>/` | Delete patient |

Patient fields: `name` (required), `age` (1–150), `gender` (`male`/`female`/`other`), `phone`, `address`, `medical_history`.

### Doctors — visible to all users; only the creator can edit/delete

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/doctors/` | Add a doctor |
| GET | `/api/doctors/` | List all doctors |
| GET | `/api/doctors/<id>/` | Doctor details |
| PUT | `/api/doctors/<id>/` | Update doctor (403 unless you created it) |
| DELETE | `/api/doctors/<id>/` | Delete doctor (403 unless you created it) |

Doctor fields: `name`, `specialization` (required), `phone`, `email`.

### Patient-Doctor Mappings

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/mappings/` | Assign a doctor to one of **your** patients: `{"patient": 1, "doctor": 2}` |
| GET | `/api/mappings/` | List all mappings for your patients |
| GET | `/api/mappings/<patient_id>/` | All doctors assigned to that patient (404 if not yours) |
| DELETE | `/api/mappings/<mapping_id>/` | Remove the mapping (204) |

Note: per the assignment spec, `/api/mappings/<id>/` serves two operations — the `id` is a
**patient id** for GET and a **mapping id** for DELETE. Duplicate patient-doctor pairs are rejected.

## Example Flow (curl)

```bash
# Register + login
curl -X POST http://127.0.0.1:8000/api/auth/register/ -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"alicepass123"}'

curl -X POST http://127.0.0.1:8000/api/auth/login/ -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"alicepass123"}'
# -> copy "access" from the response

# Use the token
curl -X POST http://127.0.0.1:8000/api/patients/ -H "Authorization: Bearer <access>" \
  -H "Content-Type: application/json" \
  -d '{"name":"John Doe","age":45,"gender":"male","phone":"9876543210"}'
```

## Testing

```bash
python manage.py test api        # automated tests (register, login, scoping, mappings)
bash test_api_live.sh            # optional: live smoke test against a running server
```

## Security Notes

- Passwords are hashed (Django PBKDF2); never stored or returned in plain text.
- JWT authentication on all endpoints by default (register/login opt out explicitly).
- Patients are strictly user-scoped — users can never read or modify another user's patients or mappings.
- Doctor edits are restricted to the doctor's creator.
