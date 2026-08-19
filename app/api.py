import io
from datetime import datetime

import pandas as pd
from flask import Blueprint, jsonify, request

from app import db
from app.models import DuplicateMatch, Patient
from app.services.matching import find_matches

api = Blueprint("api", __name__)
REQUIRED = {"first_name", "last_name"}


@api.get("/health")
def health():
    return {"status": "ok", "service": "carematch-ai"}


@api.get("/dashboard")
def dashboard():
    return jsonify({"patients": Patient.query.count(), "matches": DuplicateMatch.query.count(),
                    "high_confidence": DuplicateMatch.query.filter_by(decision="High confidence").count()})


@api.get("/matches")
def matches():
    return jsonify([match.to_dict() for match in DuplicateMatch.query.order_by(DuplicateMatch.confidence.desc()).all()])


@api.post("/patients/upload")
def upload_patients():
    file = request.files.get("file")
    if not file or not file.filename.lower().endswith(".csv"):
        return jsonify({"error": "Upload a CSV file."}), 400
    try:
        frame = pd.read_csv(io.BytesIO(file.read())).fillna("")
    except Exception:
        return jsonify({"error": "The file could not be read as CSV."}), 400
    frame.columns = [str(column).strip().lower().replace(" ", "_") for column in frame.columns]
    if not REQUIRED.issubset(frame.columns):
        return jsonify({"error": "CSV requires first_name and last_name columns."}), 400
    allowed = {"external_id", "first_name", "last_name", "date_of_birth", "gender", "phone", "email", "address"}
    patients = [Patient(**{key: str(row.get(key, "")).strip() or None for key in allowed}, source=str(row.get("source", "CSV upload")).strip() or "CSV upload") for row in frame.to_dict("records")]
    db.session.add_all(patients)
    db.session.commit()
    return jsonify({"imported": len(patients)})


@api.post("/demo-data")
def demo_data():
    samples = [
        ("SYN-1001", "Aisha", "Khan", "1988-04-16", "Female", "555-0101", "aisha.khan@example.test", "18 Oak Lane", "Synthea demo"),
        ("EXT-883", "Aisha", "Khan", "16/04/1988", "F", "5550101", "aishakhan@example.test", "18 Oak Ln.", "Legacy EHR"),
        ("SYN-1002", "Daniel", "Rodriguez", "1975-11-02", "Male", "555-0102", "daniel.r@example.test", "421 North Street", "Synthea demo"),
        ("EXT-120", "Danial", "Rodriguez", "11/02/1975", "M", "555 0102", "daniel.r@example.test", "421 N Street", "Claims system"),
        ("SYN-1003", "Meera", "Shah", "1992-08-20", "Female", "555-0103", "meera.shah@example.test", "9 Lake View", "Synthea demo"),
        ("SYN-1004", "Oliver", "Wilson", "1984-01-05", "Male", "555-0104", "oliver.w@example.test", "77 Pine Road", "Synthea demo"),
    ]
    db.session.add_all([Patient(external_id=a, first_name=b, last_name=c, date_of_birth=d, gender=e, phone=f, email=g, address=h, source=i) for a,b,c,d,e,f,g,h,i in samples])
    db.session.commit()
    return jsonify({"imported": len(samples)})


@api.post("/resolve")
def resolve():
    threshold = float((request.get_json(silent=True) or {}).get("threshold", 70))
    threshold = min(max(threshold, 0), 100)
    DuplicateMatch.query.delete()
    patients = [patient.to_dict() for patient in Patient.query.all()]
    matches = find_matches(patients, threshold)
    for left, right, score in matches:
        db.session.add(DuplicateMatch(patient_a_id=left["id"], patient_b_id=right["id"], **score))
    db.session.commit()
    return jsonify({"evaluated": len(patients), "matches": len(matches), "threshold": threshold})


@api.delete("/reset")
def reset():
    DuplicateMatch.query.delete()
    Patient.query.delete()
    db.session.commit()
    return "", 204
