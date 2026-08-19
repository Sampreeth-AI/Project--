from datetime import datetime, timezone

from app import db


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    external_id = db.Column(db.String(100), nullable=True, index=True)
    first_name = db.Column(db.String(120), nullable=False, index=True)
    last_name = db.Column(db.String(120), nullable=False, index=True)
    date_of_birth = db.Column(db.String(32), nullable=True, index=True)
    gender = db.Column(db.String(32), nullable=True)
    phone = db.Column(db.String(64), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    source = db.Column(db.String(100), nullable=False, default="upload")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self):
        return {"id": self.id, "external_id": self.external_id, "name": self.full_name,
                "first_name": self.first_name, "last_name": self.last_name,
                "date_of_birth": self.date_of_birth, "gender": self.gender,
                "phone": self.phone, "email": self.email, "address": self.address,
                "source": self.source}


class DuplicateMatch(db.Model):
    __tablename__ = "duplicate_matches"

    id = db.Column(db.Integer, primary_key=True)
    patient_a_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    patient_b_id = db.Column(db.Integer, db.ForeignKey("patients.id"), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    name_score = db.Column(db.Float, nullable=False)
    dob_score = db.Column(db.Float, nullable=False)
    contact_score = db.Column(db.Float, nullable=False)
    embedding_score = db.Column(db.Float, nullable=False)
    decision = db.Column(db.String(32), nullable=False, default="Review")
    explanation = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    patient_a = db.relationship("Patient", foreign_keys=[patient_a_id])
    patient_b = db.relationship("Patient", foreign_keys=[patient_b_id])

    def to_dict(self):
        return {"id": self.id, "patient_a": self.patient_a.to_dict(), "patient_b": self.patient_b.to_dict(),
                "confidence": round(self.confidence, 1), "name_score": round(self.name_score, 1),
                "dob_score": round(self.dob_score, 1), "contact_score": round(self.contact_score, 1),
                "embedding_score": round(self.embedding_score, 1), "decision": self.decision,
                "explanation": self.explanation}
