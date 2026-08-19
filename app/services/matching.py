"""Patient matching engine: RapidFuzz + optional Azure OpenAI embeddings."""
import math
import os
import re
from collections import Counter
from datetime import datetime
from itertools import combinations

from rapidfuzz.fuzz import ratio


def normalize(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def normalize_dob(value):
    """Align common EHR date formats before comparing dates of birth."""
    raw = str(value or "").strip()
    for pattern in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, pattern).strftime("%Y%m%d")
        except ValueError:
            continue
    return normalize(raw)


def _text(patient):
    return " ".join(str(patient.get(k) or "") for k in ("first_name", "last_name", "date_of_birth", "phone", "email", "address"))


def _local_embedding_score(left, right):
    """Explainable character n-gram cosine fallback when Azure isn't configured."""
    def grams(text):
        text = f"  {normalize(text)}  "
        return Counter(text[i:i + 3] for i in range(max(0, len(text) - 2)))
    a, b = grams(_text(left)), grams(_text(right))
    denominator = math.sqrt(sum(x * x for x in a.values()) * sum(x * x for x in b.values()))
    return 100 * sum(a[k] * b.get(k, 0) for k in a) / denominator if denominator else 0


def azure_embedding_score(left, right):
    """Use Azure embeddings only when fully configured; otherwise remain runnable locally."""
    if not all(os.getenv(key) for key in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_EMBEDDING_DEPLOYMENT")):
        return _local_embedding_score(left, right)
    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"], api_key=os.environ["AZURE_OPENAI_API_KEY"], api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"))
        vectors = client.embeddings.create(model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"], input=[_text(left), _text(right)]).data
        a, b = vectors[0].embedding, vectors[1].embedding
        return 100 * sum(x * y for x, y in zip(a, b)) / (math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b)))
    except Exception:
        return _local_embedding_score(left, right)


def ai_explanation(left, right, metrics, fallback):
    """Optional Azure OpenAI explanation layer; never blocks the review workflow."""
    if not all(os.getenv(key) for key in ("AZURE_OPENAI_ENDPOINT", "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_CHAT_DEPLOYMENT")):
        return fallback
    try:
        from openai import AzureOpenAI
        client = AzureOpenAI(azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"], api_key=os.environ["AZURE_OPENAI_API_KEY"], api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01"))
        prompt = ("Compare these two synthetic patient records for a human reviewer. Do not recommend an automatic merge. "
                  "Give one concise, plain-language sentence describing evidence and uncertainty. "
                  f"Record A: {left}. Record B: {right}. Scores (0-100): {metrics}.")
        response = client.chat.completions.create(model=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"], temperature=0,
            messages=[{"role": "system", "content": "You are a careful healthcare data-quality assistant."}, {"role": "user", "content": prompt}])
        return response.choices[0].message.content.strip() or fallback
    except Exception:
        return fallback


def score_pair(left, right):
    name = ratio(normalize(left["first_name"] + left["last_name"]), normalize(right["first_name"] + right["last_name"]))
    left_dob, right_dob = normalize_dob(left.get("date_of_birth")), normalize_dob(right.get("date_of_birth"))
    dob = 100 if left_dob and left_dob == right_dob else ratio(left_dob, right_dob)
    contacts = [ratio(normalize(left.get(field)), normalize(right.get(field))) for field in ("phone", "email", "address") if left.get(field) and right.get(field)]
    contact = max(contacts, default=0)
    embedding = azure_embedding_score(left, right)
    confidence = name * .38 + dob * .27 + contact * .15 + embedding * .20
    decision = "High confidence" if confidence >= 86 else "Review" if confidence >= 70 else "Low confidence"
    evidence = []
    if name >= 85: evidence.append("names are highly similar")
    if dob == 100: evidence.append("dates of birth match")
    if contact >= 90: evidence.append("a contact detail closely matches")
    if embedding >= 78: evidence.append("record context is semantically aligned")
    explanation = ("Likely duplicate because " + ", ".join(evidence) + ".") if evidence else "Weak overlap; retain as separate records unless further evidence is available."
    explanation = ai_explanation(left, right, {"name": round(name, 1), "dob": round(dob, 1), "contact": round(contact, 1), "semantic": round(embedding, 1), "confidence": round(confidence, 1)}, explanation)
    return {"confidence": confidence, "name_score": name, "dob_score": dob, "contact_score": contact, "embedding_score": embedding, "decision": decision, "explanation": explanation}


def find_matches(patients, threshold=70):
    return [(left, right, score) for left, right in combinations(patients, 2)
            if (score := score_pair(left, right))["confidence"] >= threshold]
