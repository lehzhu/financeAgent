"""
Deployment wrapper for Finance Agent v4
"""

# All imports happen inside Modal functions to avoid local dependency issues

import modal

# Define the Modal app
app = modal.App(
    "finance-agent-v4-new",
    image=modal.Image.debian_slim().pip_install(
        "langchain", "langchain-community", "langchain-openai",
        "faiss-cpu", "openai", "tiktoken"
    ),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Use the volume for persistent storage
volume = modal.Volume.from_name("finance-agent-storage")

# Import the actual implementation inside Modal environment
with app.image.imports():
    from main_v4_new import (
        router_agent_v4,
        calculation_agent_v4,
        final_answer_agent_v4,
        process_question_v4,
        web_endpoint_v4,
        main
    )

# Re-export the functions with proper decorators
router_agent_v4 = app.function()(router_agent_v4)
calculation_agent_v4 = app.function()(calculation_agent_v4)
final_answer_agent_v4 = app.function()(final_answer_agent_v4)

process_question_v4 = app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)(process_question_v4)

web_endpoint_v4 = app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)(web_endpoint_v4)

main = app.local_entrypoint()(main)
