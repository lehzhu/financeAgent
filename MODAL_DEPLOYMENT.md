# Modal Deployment Guide

## How Modal Works

Modal is a **serverless platform** that allows you to run Python functions in the cloud without managing infrastructure. When you deploy to Modal, your functions become accessible from anywhere, not just your local machine.

## Deployment Options

### 1. `modal run` (Development/Testing)
- **What it does**: Runs your function once and exits
- **Use case**: Testing, one-off jobs, debugging
- **Access**: Only during execution
- **Cost**: Pay per execution time

```bash
modal run agent.py --question "What is EBITDA?"
```

### 2. `modal deploy` (Production)
- **What it does**: Creates persistent endpoints that stay alive
- **Use case**: Production APIs, web services
- **Access**: 24/7 from anywhere via HTTP endpoints
- **Cost**: Pay for uptime + execution

```bash
modal deploy agent.py
```

After deployment, Modal provides:
- **Web endpoint**: `https://your-app.modal.run/`
- **API access**: Can be called from any application
- **Dashboard**: Monitor at `https://modal.com/apps/`

## Web Deployment Architecture

### Current Setup (Basic)
```
Local Machine → Modal CLI → Modal Cloud → Function Execution
```

### Production Setup (Recommended)
```
Web Client → API Gateway → Modal Function → Response
```

To create a web interface:

1. **Deploy the Modal function**:
```bash
modal deploy agent_v2.py
```

2. **Get your endpoint URL** from Modal dashboard

3. **Create a simple web frontend** (example):
```python
# web_app.py
import streamlit as st
import requests

MODAL_ENDPOINT = "https://your-app.modal.run/process_question"

question = st.text_input("Enter your finance question:")
if st.button("Get Answer"):
    response = requests.post(MODAL_ENDPOINT, json={"question": question})
    st.write(response.json()["answer"])
```

## Secrets Management

Modal secrets are stored securely in the cloud:

```bash
# Set secret once (stored in Modal cloud)
modal secret create openai-key-1 OPENAI_API_KEY=sk-xxx

# Available to all deployments automatically
# No need to manage .env files in production
```

## Triggering Without Local Machine

Once deployed with `modal deploy`, your functions can be triggered:

### 1. **Via HTTP API**
```python
import requests
response = requests.post(
    "https://your-app.modal.run/endpoint",
    json={"question": "What is Costco's revenue?"}
)
```

### 2. **Via Modal SDK from anywhere**
```python
import modal
fn = modal.Function.from_name("finance-agent", "process_question")
result = fn.remote("What is EBITDA?")
```

### 3. **Via Scheduled Jobs**
```python
@app.function(schedule=modal.Period(hours=1))
def hourly_update():
    # Runs every hour automatically
    pass
```

### 4. **Via Webhooks**
Set up webhooks from services like GitHub, Slack, etc. to trigger your functions.

## Cost Optimization

### Current Architecture (v1)
- Single large GPT-4o call for everything
- ~$0.01-0.02 per question

### Agentic Architecture (v2)
- Router: GPT-4o-mini ($0.0003 per call)
- Tools: Free (calculator) or cached (document search)
- Final synthesis: GPT-4o only when needed
- **Total: ~$0.003-0.005 per question (80% cost reduction)**

## Production Deployment Checklist

1. **Deploy the function**:
```bash
modal deploy agent_v2.py
```

2. **Test the endpoint**:
```bash
curl -X POST https://your-app.modal.run/process_question \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Costco revenue?"}'
```

3. **Monitor in Modal Dashboard**:
- View logs: `https://modal.com/apps/your-workspace/finance-agent`
- Check usage and costs
- Set up alerts

4. **Scale as needed**:
```python
@app.function(
    cpu=2,  # More CPU for faster processing
    memory=2048,  # More memory for large documents
    keep_warm=1  # Keep 1 instance always warm
)
```

## Alternative: Full Web App Deployment

For a complete web solution without needing Modal CLI:

1. **Use Vercel/Netlify for frontend** (React/Next.js app)
2. **Modal handles the backend** (your Python functions)
3. **Users access via web browser** - no installation needed

This gives you a production-ready finance Q&A system accessible from any browser!

## Summary

- **Development**: Use `modal run` for testing
- **Production**: Use `modal deploy` for persistent endpoints
- **Access**: Functions available 24/7 via HTTP once deployed
- **No local dependency**: After deployment, accessible from anywhere
- **Secrets**: Managed centrally in Modal cloud
- **Cost effective**: Agentic approach reduces API costs by 80%
