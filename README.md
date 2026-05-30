# HealthScan AI 🩺

A full-stack health prediction application built with **Flask** (Python backend), **SQLite** (persistent storage), and a custom dark clinical UI (HTML/CSS/JS frontend). It integrates the **Anthropic Claude API** to generate AI-powered health assessments from blood test values.

---

## ✨ Features

| Feature | Details |
|---|---|
| **CRUD** | Create, Read, Update, Delete patient records |
| **AI Analysis** | Claude API generates clinical remarks from blood values |
| **Rule-based fallback** | Works offline without an API key using logic-based assessment |
| **Data Validation** | Email format, past DOB, positive numeric blood values |
| **Colour-coded values** | Green/yellow/red chips indicate normal/warning/danger ranges |
| **Search** | Live search by name or email (debounced) |
| **Remarks Drawer** | Side panel to view full AI assessment, with re-analyse button |
| **Persistent Storage** | SQLite database via SQLAlchemy ORM |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask, SQLAlchemy |
| Database | SQLite (file: `instance/health.db`) |
| AI | Anthropic Claude (`claude-sonnet-4-20250514`) |
| Frontend | Vanilla HTML5 + CSS3 + JavaScript (ES2022) |
| Fonts | Space Mono, DM Sans (Google Fonts) |

**Why this stack?**
- Flask is lightweight and perfect for REST APIs without the boilerplate of larger frameworks.
- SQLite requires zero setup — ideal for a portable demo.
- Vanilla JS keeps the frontend dependency-free and fast.
- Claude API provides medically-nuanced text generation far superior to rule-based systems.

---

## 🚀 Setup & Run

### 1. Clone the repository
```bash
git clone https://github.com/YOUR_USERNAME/healthscan-ai.git
cd healthscan-ai
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set your Anthropic API key
```bash
export ANTHROPIC_API_KEY="your_key_here"   # Linux/Mac
set ANTHROPIC_API_KEY=your_key_here        # Windows CMD
```
> If no API key is set, the app falls back to a built-in rule-based health assessment.

### 5. Run the application
```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## 📁 Project Structure

```
healthscan-ai/
├── app.py                  # Flask backend — routes, models, AI integration
├── requirements.txt        # Python dependencies
├── instance/
│   └── health.db           # SQLite database (auto-created on first run)
├── templates/
│   └── index.html          # Main HTML template
└── static/
    ├── css/
    │   └── style.css       # Dark clinical UI styles
    └── js/
        └── app.js          # Frontend CRUD logic
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/patients` | List all patients (supports `?search=`) |
| `POST` | `/api/patients` | Create patient + generate AI remarks |
| `GET` | `/api/patients/:id` | Get single patient |
| `PUT` | `/api/patients/:id` | Update patient + regenerate remarks |
| `DELETE` | `/api/patients/:id` | Delete patient |
| `POST` | `/api/patients/:id/analyze` | Re-run AI analysis |

---

## ⚠️ Reference Ranges Used

| Biomarker | Normal Range |
|---|---|
| Fasting Glucose | 70–99 mg/dL |
| Haemoglobin | 12–17.5 g/dL |
| Total Cholesterol | < 200 mg/dL |

---

## 📸 Screenshots

> Add screenshots of your running application here.

---

## 📝 License

MIT — free to use and modify.
