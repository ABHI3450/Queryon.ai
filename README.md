# Multi-Agent Personal Data Analyst Team SaaS

A production-ready SaaS application where users upload CSV or Excel files. A sequential pipeline of 4 specialized AI agents processes the dataset and generates an executive report with publication-quality charts and plain-English summaries.

---

## 🌟 Key Features
- **4 Autonomous Agents**:
  1. **Data Cleaner Agent**: Deduplication, schema standardization to `snake_case`, median/mode missing value imputation, and IQR outlier detection.
  2. **Analyst Agent**: Correlation detection, top-N category distributions, and time-series trends. Enhanced with Groq Llama 3 70B reasoning.
  3. **Visualizer Agent**: Publication-quality dark-themed graphics (Bar, Line, Scatter, Donut Pie) rendered via `matplotlib`.
  4. **Explainer Agent**: Plain-English report generation formatted as **Overview → Key Insights → What This Means**.
- **Real-Time Job Tracking**: Server-Sent Events (SSE) stream status updates to Next.js UI as each agent finishes.
- **Authentication**: Clerk Hosted Auth + Webhook sync to PostgreSQL.
- **Dual-mode LLM Engine**: Fully functional in offline/rule-based mode without API keys; upgrades automatically when `GROQ_API_KEY` is present.

---

## 🛠️ Quick Start (Local Development)

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Unix:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```
Backend server will start at `http://localhost:8000`. Swagger API docs available at `http://localhost:8000/docs`.

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:3000` in your browser.

---

## 🐳 Docker Deployment
Run the full stack (PostgreSQL, FastAPI backend, Next.js frontend) with Docker Compose:

```bash
docker-compose up --build
```

---

## 🧪 Running Tests
Execute the backend pytest suite:
```bash
cd backend
pytest tests/ -v
```
