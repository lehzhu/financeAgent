import modal

# Test app without OpenAI calls
app = modal.App("finance-agent-test")

# Mock function to test the logic without API calls
@app.function()
def answer_tactical_mock(context, question):
    # Mock response for testing
    if "NOPAT" in question and "EBIT" in context:
        return "NOPAT is calculated as EBIT * (1 - tax rate).\nFrom the context, EBIT = $1,000, tax rate = 30%.\nSo, NOPAT = 1000 * (1 - 0.3) = 700.\nFinal Answer: 700"
    return "Mock response for testing - API quota issue resolved!"

# Function to extract the final answer from the LLM response
def extract_final_answer(response):
    lines = response.split("\n")
    for line in lines:
        if line.startswith("Final Answer:"):
            return line.split(":", 1)[1].strip()
    return None

# Test function
@app.function()
def process_question_test(question, context):
    response = answer_tactical_mock.remote(context, question)
    final_answer = extract_final_answer(response)
    return final_answer if final_answer else "Could not determine the answer."

@app.local_entrypoint()
def main(
    question: str = "Calculate NOPAT for 2024.",
    context: str = "The company's EBIT for 2024 is $1,000, and the effective tax rate is 30%."
):
    result = process_question_test.remote(question, context)
    print(f"Test Result: {result}")
