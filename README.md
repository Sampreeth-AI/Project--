# CareMatch AI — Duplicate Patient Record Resolver

A portfolio-ready Flask application that identifies likely duplicate patient records across fragmented healthcare data. It combines fuzzy demographic matching (RapidFuzz), semantic similarity (Azure OpenAI embeddings when configured), and transparent explanations for human review.

> Demo only. This project uses synthetic data and is not a clinical system. Do not upload protected health information to an unapproved environment.

## Highlights

- Clean, responsive analyst dashboard for importing records and reviewing matches
- CSV workflow powered by Pandas; accepts inconsistent name, DOB, phone, email and address formatting
- Weighted confidence model: name, DOB, contact details, and semantic record similarity
- Azure OpenAI embeddings supported with a dependency-free local n-gram cosine fallback
- Synthea-style synthetic demo records included—no real patient information
- MySQL-ready SQLAlchemy models; SQLite runs locally without setup
- Render deployment blueprint and API health endpoint

## Quick start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Open `http://127.0.0.1:5000`, choose **Load Synthea-style demo**, then **Run duplicate detection**.

## CSV format

`first_name` and `last_name` are required. The remaining fields are optional:

```csv
external_id,first_name,last_name,date_of_birth,gender,phone,email,address,source
MRN-104,Aisha,Khan,1988-04-16,Female,555-0101,aisha@example.test,18 Oak Lane,Hospital A
LEG-22,Aisha,Khan,16/04/1988,F,5550101,aishakhan@example.test,18 Oak Ln.,Legacy EHR
```

## Azure OpenAI setup (optional)

Set `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`, and `AZURE_OPENAI_CHAT_DEPLOYMENT` in `.env`. The deployment names must match deployments in your Azure resource. Azure produces both semantic similarity and concise reviewer explanations; without it, CareMatch uses a local character n-gram similarity and deterministic explanation so the demo remains runnable.

## MySQL

Create a database and set:

```env
DATABASE_URL=mysql+pymysql://USER:PASSWORD@localhost:3306/carematch
```

## API

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Render health check |
| GET | `/api/v1/dashboard` | Dashboard counters |
| POST | `/api/v1/patients/upload` | Upload CSV using `file` form data |
| POST | `/api/v1/demo-data` | Load synthetic demo records |
| POST | `/api/v1/resolve` | Calculate duplicate candidates |
| GET | `/api/v1/matches` | Get ranked matches and explanations |

## Deploy to Render

1. Push this project to a new GitHub repository.
2. In Render select **New → Blueprint** and connect that repository (it detects `render.yaml`).
3. Add `AZURE_OPENAI_*` secrets in the Render dashboard if using Azure embeddings.
4. For persistent production data, replace SQLite with a managed MySQL `DATABASE_URL`; free Render filesystems are ephemeral.

## Test

```powershell
python -m unittest discover -s tests
```
