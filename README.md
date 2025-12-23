# SentinelFlow 🚦

**Safe Agent-Based NLP System for Task Fulfillment**

SentinelFlow is a production-style, agent-based NLP system that converts natural language requests into **safe, auditable, multi-step actions** using tool orchestration, policy enforcement, and confirmation gates.

It is designed as a **portfolio-grade project** demonstrating:

- LLM planning + deterministic execution
- Tool calling with safety guarantees
- Stateful conversations
- Full audit logging
- Quantitative evaluation (heuristic vs LLM)

---

## Key Features

- **Agent Orchestrator** – coordinates planning, tools, memory, and policy
- **LLM Planner (optional)** – proposes structured plans (never executes)
- **Heuristic Planner (fallback)** – guarantees reliability
- **Tool Registry** – balance check, product search, purchase execution
- **Safety Layer** – confirmation tokens + idempotency
- **Session Memory** – supports multi-turn flows (select → confirm → execute)
- **Audit Logs** – every tool call is persisted
- **Evaluation Harness** – reproducible metrics & pass rates

---

## System Architecture

```
User
  ↓
FastAPI /chat
  ↓
Agent Orchestrator
  ├── Planner (LLM or Heuristic)
  ├── Policy Engine
  ├── Memory Store
  ├── Tool Registry
  ↓
Database (Users, Accounts, Products, Transactions, Audit Logs)
```

**Key Principle:**

> _LLMs suggest plans — the system enforces correctness._

---

## Quick Start

### 1. Install dependencies

```bash
poetry install
```

### 2. Run database migrations

```bash
poetry run alembic upgrade head
```

### 3. Seed synthetic data

```bash
poetry run uvicorn app.main:app --reload
```

Then visit:

```
POST http://127.0.0.1:8000/admin/seed
```

---

## Demo Script

You can run this entire demo via **FastAPI Swagger UI** (`/docs`)
or using `curl`.

---

### Demo 1: Check Balance

**Request**

```json
POST /chat
{
  "session_id": "demo-1",
  "user_id": "<USER_ID_FROM_SEED>",
  "message": "What is my balance?"
}
```

**Response**

```
Your balance is 1345.00 USD.
```

---

### Demo 2: Buy a Product (Multi-Step Agent Flow)

#### Step 1 — Search

```json
POST /chat
{
  "session_id": "demo-2",
  "user_id": "<USER_ID_FROM_SEED>",
  "message": "Buy me a keyboard"
}
```

**Response**

```
Here are matching products:
1) Mechanical Keyboard — 89.99 USD (stock: 12)

Reply with the option number (e.g., 1).
```

---

#### Step 2 — Select

```json
POST /chat
{
  "session_id": "demo-2",
  "user_id": "<USER_ID_FROM_SEED>",
  "message": "1"
}
```

**Response**

```
Please confirm you want to purchase 1 unit of Mechanical Keyboard.
Reply with: confirm <TOKEN>
```

---

#### Step 3 — Confirm

```json
POST /chat
{
  "session_id": "demo-2",
  "user_id": "<USER_ID_FROM_SEED>",
  "message": "confirm <TOKEN>"
}
```

**Response**

```
Purchase successful!
Remaining balance: 1255.01 USD
```

---

## Evaluation

SentinelFlow includes a **fully automated evaluation harness**.

### Run evals

```bash
python eval/run_eval.py
```

### Example Output

```
=== Eval Summary ===
Total: 5 | Passed: 5 | Pass rate: 100.00%
Latency p95: 2.55s
- heuristic: 2/2 (100%)
- llm: 3/3 (100%)
```

This proves:

- Deterministic correctness
- LLM planner reliability
- No unsafe executions

---

## 🔐 Safety Guarantees

- Purchases **never execute** without confirmation
- Idempotency keys prevent double spending
- Tool arguments are validated
- Orchestrator repairs malformed LLM plans
- Audit logs record every action

---

## 📂 Project Structure

```
app/
 ├── agent/        # planner, orchestrator, memory, policy
 ├── tools/        # search_products, check_balance, execute_purchase
 ├── api/          # FastAPI routes
 ├── db/           # models, sessions, migrations
 └── schemas/      # pydantic IO models

eval/
 ├── dataset.jsonl
 └── run_eval.py
```

---

## 🛠 Tech Stack

- **Python 3.11+**
- **FastAPI**
- **SQLAlchemy + Alembic**
- **Pydantic v2**
- **OpenAI Responses API**
- **Poetry**
- **SQLite / PostgreSQL**

---

## Why This Project Matters

SentinelFlow demonstrates **real-world agent design**, not toy demos:

- LLMs are _constrained_, not trusted
- Business rules live outside the model
- Failures are observable and testable
- Behavior is reproducible and evaluable

This architecture directly maps to:

- AI copilots
- Enterprise chat automation
- Fintech & e-commerce agents
- Production RAG + tool systems

---

## Next Steps (Planned)

- React / Next.js frontend demo
- Product search embeddings
- Auth + user roles
- Tracing UI (per-step timeline)
- Cloud deployment (Docker + Fly.io)
