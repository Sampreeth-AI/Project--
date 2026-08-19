import io
import os
import unittest

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
from app import create_app, db


class ResolverApiTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        with self.app.app_context():
            db.drop_all()
            db.create_all()

    def test_upload_and_resolve_duplicate_patients(self):
        csv = b"first_name,last_name,date_of_birth,phone,email\nAisha,Khan,1988-04-16,555-0101,aisha@example.test\nAisha,Khan,16/04/1988,5550101,aisha@example.test\n"
        response = self.client.post("/api/v1/patients/upload", data={"file": (io.BytesIO(csv), "patients.csv")})
        self.assertEqual(response.status_code, 200)
        response = self.client.post("/api/v1/resolve", json={"threshold": 70})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["matches"], 1)
        self.assertEqual(len(self.client.get("/api/v1/matches").json), 1)


if __name__ == "__main__":
    unittest.main()
