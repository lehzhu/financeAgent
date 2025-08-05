import modal
from openai import OpenAI
import os

# Define the Modal app with required dependencies
app = modal.App(
    "finance-agent",
    image=modal.Image.debian_slim().pip_install("openai"),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Examples for tactical questions (with context)
EXAMPLES_TACTICAL = """
Example 1:
Context: The company's EBIT for 2024 is $1,000, and the effective tax rate is 30%.
Question: Calculate NOPAT for 2024.
Answer:
NOPAT is calculated as EBIT * (1 - tax rate).
From the context, EBIT = $1,000, tax rate = 30%.
So, NOPAT = 1000 * (1 - 0.3) = 700.
Final Answer: 700

Example 2:
Context: The company reports total lease assets of $5,000 and variable lease costs of $100, with total lease costs of $1,000.
Question: Estimate variable lease assets for 2024.
Answer:
Since variable lease assets are not directly provided, we can assume that the ratio of variable lease assets to total lease assets is similar to the ratio of variable lease costs to total lease costs.
Ratio = variable lease costs / total lease costs = 100 / 1000 = 0.1
Therefore, variable lease assets = ratio * total lease assets = 0.1 * 5000 = 500.
Final Answer: 500
"""

# Examples for conceptual questions (no context)
EXAMPLES_CONCEPTUAL = """
Example 1:
Question: If a company has a 2x sales multiple and a 5x EBITDA multiple, what is its EBITDA margin?
Answer:
Let's denote sales as S, EBITDA as E.
The sales multiple is 2x, so enterprise value EV = 2S.
The EBITDA multiple is 5x, so EV = 5E.
Therefore, 2S = 5E, so E = (2/5)S.
The EBITDA margin is E / S = (2/5) = 0.4 or 40%.
Final Answer: 40%
"""

# Initialize OpenAI client with API key from Modal secret
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Function to handle tactical questions with context
def answer_tactical(context, question):
    prompt = f"""Here are some examples of how to answer similar questions:

{EXAMPLES_TACTICAL}

Now, based on the following context and question, provide your answer in a similar format.

Context: {context}

Question: {question}

Remember to state your final answer in the format: 'Final Answer: [answer]'"""
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o"
    )
    return chat_completion.choices[0].message.content

# Function to handle conceptual questions without context
def answer_conceptual(question):
    prompt = f"""Here are some examples of how to answer similar questions:

{EXAMPLES_CONCEPTUAL}

Now, think step by step to answer the following question. Provide your reasoning and then state the final answer in the format: 'Final Answer: [answer]'

Question: {question}"""
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="gpt-4o"
    )
    return chat_completion.choices[0].message.content

# Function to extract the final answer from the LLM response
def extract_final_answer(response):
    lines = response.split("\n")
    for line in reversed(lines):
        if line.startswith("Final Answer:"):
            return line.split(":", 1)[1].strip()
    return None

# Main function to process questions
@app.function(timeout=60)  # 60 second timeout per question
def process_question(question, context=None):
    if context:
        response = answer_tactical(context, question)
    else:
        response = answer_conceptual(question)
    final_answer = extract_final_answer(response)
    return final_answer

# Local entrypoint for testing individual questions
@app.local_entrypoint()
def main(
    question: str = "Calculate NOPAT for 2024.",
    context: str = "The company's EBIT for 2024 is $1,000, and the effective tax rate is 30%.",
):
    result = process_question.remote(question, context)
    print(result)