# Architectural Decisions & Technical Interview Blueprint
## Multi-Agent Personal Data Analyst Team SaaS

This document summarizes the core architectural decisions, design patterns, and engineering tradeoffs made when designing and building the **Multi-Agent Personal Data Analyst Team** system.

---

## 1. Why a Sequential Multi-Agent Architecture?
Instead of sending a massive prompt to a single LLM asking it to clean, analyze, visualize, and summarize a dataset all at once, we split the responsibility across **4 distinct, specialized agents**:

1. **Data Cleaner Agent (Rule-based)**:
   - *Why*: Deterministic tasks (type conversions, deduplication, missing value imputation via median/mode, IQR outlier calculation) are best done with deterministic code (`pandas`/`numpy`), not LLMs which can hallucinate data mutations.
2. **Analyst Agent (Dual-mode: Statistical + Groq Llama 3 70B)**:
   - *Why*: Computes mathematical correlations, top-N categories, and time-series trends deterministically first, then passes statistical findings to Groq LLM for high-level business interpretation.
3. **Visualizer Agent (Rule-based)**:
   - *Why*: LLMs struggle to generate clean, syntax-perfect code reliably for complex plotting on the fly. Visualizer uses template-based `matplotlib` rendering with a dark theme and custom color palettes.
4. **Explainer Agent (Dual-mode: Markdown Template + Groq Llama 3 70B)**:
   - *Why*: Translates structured findings and image URLs into executive, plain-English Markdown summaries: **Overview → Key Insights → What This Means**.

---

## 2. Real-Time Status Engine: Why SSE over WebSockets?
We chose **Server-Sent Events (SSE)** via `sse-starlette` to stream real-time pipeline status updates from FastAPI to Next.js:
- **Unidirectional**: Agent progress flows strictly from Server → Client.
- **Protocol Overhead**: SSE runs over standard HTTP/2, multiplexes cleanly, and auto-reconnects natively via browser `EventSource` without needing complex WebSocket ping/pong frame management.

---

## 3. Storage Abstraction (Strategy Pattern)
`StorageBackend` is an abstract interface. The application uses `LocalStorage` in development (saving files into `./storage/uploads` and `./storage/charts`) and can be swapped to `S3Storage` by changing `STORAGE_BACKEND=s3` in environment configuration without modifying agent logic.

---

## 4. Authentication & User Sync Strategy
- Authentication is managed via **Clerk** (hosted auth).
- Webhook route `POST /api/webhooks/clerk` listens for `user.created` / `user.updated` / `user.deleted` events and syncs records to PostgreSQL asynchronously.
- Protected FastAPI endpoints verify Clerk JWT tokens against Clerk's public **JWKS (RS256)** key set.

---

## 5. Database Schema & Tier Rate Limiting
- **Users**: Synced from Clerk, tracks `tier` ("free" vs "pro") and `monthly_usage`.
- **Uploads**: Stores original metadata, file size, row/column counts, and S3 storage keys.
- **Jobs**: Tracks task status (`pending`, `cleaning`, `analyzing`, `visualizing`, `explaining`, `completed`, `failed`), progress percentage, and error tracebacks.
- **Reports**: Stores JSON summaries, list of generated chart image paths, and final Markdown report text.
