# Student Management System

A full-stack CRUD web app to add, search, update and delete student records.

**Stack:** HTML + CSS + JavaScript (Fetch API) · Python Flask (REST API) · SQLite · Node.js (optional frontend tooling: Prettier/ESLint)

## Features
- Add, view, search, update and delete students (Name, Roll No, Class, Marks, Contact)
- REST API with JSON over GET / POST / PUT / DELETE
- Validation on both frontend and backend (unique roll number, marks 0-100, valid 10-digit mobile)
- Live search and list updates without page reload
- Handles edge cases such as searching for a non-existent student
- Summary cards: total students, average marks, top marks

## Project structure
```
student-management-system/
├── app.py              # Flask app + REST API + SQLite
├── index.html          # Frontend page
├── static/css/style.css
├── static/js/app.js    # Fetch API logic
├── tests/test_api.py   # Backend tests
├── requirements.txt
└── package.json        # Node.js frontend tooling
```

## Run locally
```bash
# 1. (optional) create a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. install dependencies
pip install -r requirements.txt

# 3. start the server
python app.py
```
Open **http://127.0.0.1:5000** in your browser (do not double-click `index.html`; the Flask server must be running). On Windows you can also just double-click `run.bat`. The `students.db` file is created automatically on first run.

### Optional: Node.js tooling
```bash
npm install
npm run format
```

### Run tests
```bash
pip install pytest
python -m pytest -q
```

## API
| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/students` | List all students |
| GET | `/api/students?q=riya` | Search by name, roll no or class |
| GET | `/api/students/<id>` | Get one student |
| POST | `/api/students` | Add a student |
| PUT | `/api/students/<id>` | Update a student |
| DELETE | `/api/students/<id>` | Delete a student |
| GET | `/api/stats` | Total, average and top marks |

## Database schema
`students(id PK, name, roll_no UNIQUE, class_name, marks 0-100, contact, created_at)`
