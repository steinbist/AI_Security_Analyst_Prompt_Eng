# AI_Security_Analyst_Prompt_Eng# 🛡️ AI Security Analyst Assistant  
*Prompt-only Security Log Analyzer (FastAPI + Streamlit + OpenAI)*  

---

## 📘 Overview
**AI Security Analyst Assistant (AISA)** is an end-to-end prototype that demonstrates how OpenAI models can analyze security-related text—such as access logs, visitor events, or policy statements—without fine-tuning or vector retrieval.  
It exposes a REST API built with **FastAPI** and a local **Streamlit** web UI.

The assistant evaluates each event or narrative and returns a **risk assessment**, **summary**, or **policy alignment** in structured JSON or Markdown.

---

## ⚙️ Architecture

AI_SECURITY_ANALYST_PROMPT_ENG/
│
├── app/
│ ├── main.py # FastAPI entry point
│ ├── route/analyze_route.py # REST endpoints
│ ├── services/analyze_service.py
│ ├── data/db_config.py # SQLite + audit logging
│ ├── schemas/analyze_schema.py
│ ├── prompts/system_prompt.txt
│ └── ui/streamlit_app.py # Streamlit front-end
│
├── .env # API key & model name (not committed)
├── requirements.txt
└── README.md


---

## 🚀 Quick Start (PowerShell on Windows)

### 1️⃣ Create and activate virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
OPENAI_MODEL=gpt-3.5-turbo

irm "http://127.0.0.1:8000/health"

.\.venv\Scripts\Activate.ps1
streamlit run app/ui/streamlit_app.py


## Example Input

A visitor with a Confidential clearance tried to enter Gate 4 and was denied.
Please provide a risk analysis for this visitor.


## Example Output

{
  "data": {
    "type": "risk_assessment",
    "summary": "Visitor with Confidential clearance attempted entry at Gate 4 (Top Secret facility).",
    "findings": [
      {
        "id": "F-001",
        "title": "Clearance mismatch",
        "severity": "Medium",
        "risk_score": 0.65,
        "likelihood": "Probable",
        "impact": "Moderate",
        "confidence": 0.92,
        "recommendation": "Notify security desk and verify visitor’s clearance record.",
        "entities": {
          "users": ["Visitor"],
          "locations": ["Gate 4"]
        }
      }
    ]
  }
}


## SQLite Audit Log

python - << 'PY'
import sqlite3, pathlib
db = pathlib.Path("app/data/app.db")
if db.exists():
    con = sqlite3.connect(db)
    for row in con.execute("select id, created_at, model, output_format, substr(input_preview,1,60) from analyses order by id desc limit 5"):
        print(row)
    con.close()
else:
    print("No database found.")
PY

## Packages

fastapi
uvicorn[standard]
openai>=1.40.0
pydantic>=2.6
python-dotenv
requests
streamlit

🧑‍💻 Author
Tim Steinbis
Full-Stack / AI Integration Engineer
Vista, CA

⚠️ Disclaimer

This tool is for demonstration and educational purposes only.
