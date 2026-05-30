"""
HealthScan AI - Health Prediction Application
Backend: Flask + SQLite
AI: Anthropic Claude API for health analysis
"""

import os
import re
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template, abort
from flask_sqlalchemy import SQLAlchemy
import anthropic

app = Flask(__name__)

# --- Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'health.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Set your Anthropic API key via environment variable:
#   export ANTHROPIC_API_KEY="your_key_here"
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

db = SQLAlchemy(app)


# --- Model ---
class Patient(db.Model):
    __tablename__ = "patients"

    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(120), nullable=False)
    date_of_birth = db.Column(db.String(10), nullable=False)   # stored as YYYY-MM-DD
    email         = db.Column(db.String(200), nullable=False, unique=True)
    glucose       = db.Column(db.Float, nullable=False)        # mg/dL
    haemoglobin   = db.Column(db.Float, nullable=False)        # g/dL
    cholesterol   = db.Column(db.Float, nullable=False)        # mg/dL
    remarks       = db.Column(db.Text, default="")
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id":            self.id,
            "full_name":     self.full_name,
            "date_of_birth": self.date_of_birth,
            "email":         self.email,
            "glucose":       self.glucose,
            "haemoglobin":   self.haemoglobin,
            "cholesterol":   self.cholesterol,
            "remarks":       self.remarks,
            "created_at":    self.created_at.isoformat() if self.created_at else "",
            "updated_at":    self.updated_at.isoformat() if self.updated_at else "",
        }


with app.app_context():
    os.makedirs(os.path.join(BASE_DIR, "instance"), exist_ok=True)
    db.create_all()


# --- Validation helpers ---
def validate_email(email: str) -> bool:
    return bool(re.match(r"^[\w.+\-]+@[\w\-]+\.[a-zA-Z]{2,}$", email))


def validate_dob(dob: str) -> bool:
    """Date of birth must be a valid past date."""
    try:
        d = datetime.strptime(dob, "%Y-%m-%d").date()
        return d < date.today()
    except ValueError:
        return False


def validate_positive_float(value) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def validate_patient_data(data: dict, is_update: bool = False) -> list[str]:
    errors = []
    fields = ["full_name", "date_of_birth", "email", "glucose", "haemoglobin", "cholesterol"]

    if not is_update:
        for f in fields:
            if f not in data or str(data[f]).strip() == "":
                errors.append(f"'{f}' is required.")

    if "email" in data and data["email"]:
        if not validate_email(data["email"]):
            errors.append("Invalid email address format.")

    if "date_of_birth" in data and data["date_of_birth"]:
        if not validate_dob(data["date_of_birth"]):
            errors.append("Date of birth must be a valid past date (YYYY-MM-DD).")

    for field in ["glucose", "haemoglobin", "cholesterol"]:
        if field in data and data[field] != "" and data[field] is not None:
            if not validate_positive_float(data[field]):
                errors.append(f"'{field}' must be a positive number.")

    return errors


# --- AI Health Analysis ---
def generate_health_remarks(patient: dict) -> str:
    """
    Call the Anthropic Claude API to generate a clinical health assessment
    based on the patient's blood test values.
    """
    if not ANTHROPIC_API_KEY:
        return generate_rule_based_remarks(patient)

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        prompt = f"""You are a clinical decision-support assistant. Based on the following blood test results, 
provide a concise health assessment (2-3 sentences max) highlighting:
1. Which values are normal or abnormal
2. Possible health risks or conditions suggested by the values
3. A general recommendation (consult doctor if concerned)

Patient: {patient['full_name']}, Age: {calculate_age(patient['date_of_birth'])} years
Blood Test Results:
- Fasting Glucose: {patient['glucose']} mg/dL (Normal: 70-99 mg/dL)
- Haemoglobin: {patient['haemoglobin']} g/dL (Normal: Men 13.5-17.5, Women 12-15.5 g/dL)
- Total Cholesterol: {patient['cholesterol']} mg/dL (Normal: <200 mg/dL)

Provide only the health assessment. Do not add disclaimers about not being a doctor."""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()

    except Exception as e:
        app.logger.error(f"Anthropic API error: {e}")
        return generate_rule_based_remarks(patient)


def calculate_age(dob_str: str) -> int:
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        today = date.today()
        return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    except Exception:
        return 0


def generate_rule_based_remarks(patient: dict) -> str:
    """Fallback rule-based health assessment when API key is not set."""
    issues = []
    recommendations = []

    glucose = float(patient["glucose"])
    haemoglobin = float(patient["haemoglobin"])
    cholesterol = float(patient["cholesterol"])
    age = calculate_age(patient["date_of_birth"])

    # Glucose assessment
    if glucose < 70:
        issues.append("hypoglycemia (low blood sugar)")
        recommendations.append("monitor glucose closely")
    elif 100 <= glucose <= 125:
        issues.append("pre-diabetic glucose levels")
        recommendations.append("lifestyle modifications advised")
    elif glucose > 125:
        issues.append("elevated glucose suggesting possible diabetes")
        recommendations.append("urgent diabetes screening recommended")

    # Haemoglobin assessment
    if haemoglobin < 12:
        issues.append("low haemoglobin indicating possible anaemia")
        recommendations.append("iron and nutritional assessment advised")
    elif haemoglobin > 17.5:
        issues.append("elevated haemoglobin")
        recommendations.append("further investigation needed")

    # Cholesterol assessment
    if 200 <= cholesterol <= 239:
        issues.append("borderline high cholesterol")
        recommendations.append("dietary changes recommended")
    elif cholesterol >= 240:
        issues.append("high cholesterol indicating cardiovascular risk")
        recommendations.append("lipid-lowering therapy consultation advised")

    if not issues:
        return (
            f"All blood parameters are within normal reference ranges. "
            f"Glucose ({glucose} mg/dL), Haemoglobin ({haemoglobin} g/dL), and "
            f"Cholesterol ({cholesterol} mg/dL) appear healthy. "
            f"Continue routine health monitoring."
        )

    return (
        f"Results indicate {', '.join(issues)}. "
        f"Recommendations: {'; '.join(recommendations)}. "
        f"Please consult a healthcare professional for a comprehensive evaluation."
    )


# --- Routes ---
@app.route("/")
def index():
    return render_template("index.html")


# CREATE
@app.route("/api/patients", methods=["POST"])
def create_patient():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    errors = validate_patient_data(data)
    if errors:
        return jsonify({"errors": errors}), 422

    # Check duplicate email
    if Patient.query.filter_by(email=data["email"].strip().lower()).first():
        return jsonify({"errors": ["A patient with this email already exists."]}), 409

    remarks = generate_health_remarks(data)

    patient = Patient(
        full_name     = data["full_name"].strip(),
        date_of_birth = data["date_of_birth"],
        email         = data["email"].strip().lower(),
        glucose       = float(data["glucose"]),
        haemoglobin   = float(data["haemoglobin"]),
        cholesterol   = float(data["cholesterol"]),
        remarks       = remarks,
    )
    db.session.add(patient)
    db.session.commit()
    return jsonify(patient.to_dict()), 201


# READ ALL
@app.route("/api/patients", methods=["GET"])
def list_patients():
    search = request.args.get("search", "").strip()
    query = Patient.query.order_by(Patient.created_at.desc())
    if search:
        like = f"%{search}%"
        query = query.filter(
            (Patient.full_name.ilike(like)) | (Patient.email.ilike(like))
        )
    patients = query.all()
    return jsonify([p.to_dict() for p in patients])


# READ ONE
@app.route("/api/patients/<int:patient_id>", methods=["GET"])
def get_patient(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        abort(404)
    return jsonify(patient.to_dict())


# UPDATE
@app.route("/api/patients/<int:patient_id>", methods=["PUT"])
def update_patient(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        abort(404)

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON payload"}), 400

    errors = validate_patient_data(data, is_update=True)
    if errors:
        return jsonify({"errors": errors}), 422

    # Check email uniqueness (exclude self)
    if "email" in data:
        existing = Patient.query.filter_by(email=data["email"].strip().lower()).first()
        if existing and existing.id != patient_id:
            return jsonify({"errors": ["Another patient with this email already exists."]}), 409

    for field in ["full_name", "date_of_birth", "email"]:
        if field in data:
            setattr(patient, field, data[field].strip() if isinstance(data[field], str) else data[field])

    for field in ["glucose", "haemoglobin", "cholesterol"]:
        if field in data:
            setattr(patient, field, float(data[field]))

    # Regenerate AI remarks when blood values change
    patient.remarks = generate_health_remarks(patient.to_dict())
    patient.updated_at = datetime.utcnow()

    db.session.commit()
    return jsonify(patient.to_dict())


# DELETE
@app.route("/api/patients/<int:patient_id>", methods=["DELETE"])
def delete_patient(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        abort(404)
    db.session.delete(patient)
    db.session.commit()
    return jsonify({"message": "Patient record deleted successfully."})


# REGENERATE AI REMARKS
@app.route("/api/patients/<int:patient_id>/analyze", methods=["POST"])
def analyze_patient(patient_id):
    patient = db.session.get(Patient, patient_id)
    if not patient:
        abort(404)
    patient.remarks = generate_health_remarks(patient.to_dict())
    patient.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"remarks": patient.remarks})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
