#!/usr/bin/env python3
"""
Standalone FinanceQA benchmark evaluation.
Tests the agent against the real FinanceQA dataset.
"""

import modal
from datasets import load_dataset
import re
import time
import json
from datetime import datetime
import os

# Define the Modal app with all required dependencies
app = modal.App(
    "finance-benchmark-standalone",
    image=modal.Image.debian_slim().pip_install(
        "datasets", "openai", "langchain", "langchain-community", 
        "langchain-openai", "faiss-cpu", "tiktoken", "zeroentropy"
    ),
    secrets=[
        modal.Secret.from_name("openai-key-1"),
        modal.Secret.from_name("ZEROENTROPY")
    ]
)

# Use the volume for knowledge base
volume = modal.Volume.from_name("finance-agent-storage")

def extract_number(text):
    """Extract numerical value from text, handling various formats."""
    if text is None:
        return None
    
    # Convert to string and clean
    text = str(text).strip()
    
    # Remove common prefixes/suffixes
    text = text.replace("$", "").replace(",", "").replace("%", "")
    text = text.replace("(in millions)", "").replace("million", "")
    text = text.replace("billion", "000").replace("x", "")
    
    # Try to find a number
    numbers = re.findall(r'-?\d+\.?\d*', text)
    if numbers:
        try:
            return float(numbers[0])
        except:
            return None
    return None

def answers_match(expected, got, tolerance=0.02):
    """Check if answers match with some tolerance for numerical values."""
    if expected == got:
        return True
    
    # Try numerical comparison
    expected_num = extract_number(expected)
    got_num = extract_number(got)
    
    if expected_num is not None and got_num is not None:
        # Allow 2% tolerance for numerical answers
        if abs(expected_num - got_num) / max(abs(expected_num), 0.01) < tolerance:
            return True
    
    # Check for Yes/No questions
    expected_lower = str(expected).lower().strip()
    got_lower = str(got).lower().strip()
    
    if expected_lower in ["yes", "no"]:
        if expected_lower in got_lower:
            return True
    
    # Check if the expected answer is contained in the response
    if expected_lower in got_lower:
        return True
    
    return False

@app.function(
    volumes={"/data": volume},
    timeout=3600  # 60 minutes for full evaluation
)
def run_benchmark(test_size=20):
    """
    Run the official FinanceQA benchmark evaluation.
    
    Args:
        test_size: Number of questions to test (default: 20, max: 148)
    """
    import openai
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain.chains import create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    
    # Initialize OpenAI client
    openai.api_key = os.environ.get("OPENAI_API_KEY")
    
    # Load the FinanceQA test set
    print("Loading FinanceQA dataset...")
    dataset = load_dataset("AfterQuery/FinanceQA", split="test")
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings()
    
    # Load the FAISS index from the volume
    vectorstore = None
    if os.path.exists("/data/finance_knowledge_base"):
        print("Loading knowledge base from volume...")
        vectorstore = FAISS.load_local("/data/finance_knowledge_base", embeddings, allow_dangerous_deserialization=True)
    
    # Define the enhanced agent function
    def process_question_enhanced(question, context=""):
        """Process a finance question using enhanced agents."""
        
        # Truncate context if too long (keep first 4000 chars to stay under token limit)
        if len(context) > 4000:
            context = context[:4000] + "...[truncated]"
        
        # Create the chain for RAG if vectorstore exists
        if vectorstore:
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            
            # Create prompt
            prompt = ChatPromptTemplate.from_template("""
            You are a financial analysis expert. Answer the question based on the context provided.
            If the question requires calculations, show your work step by step.
            
            Context from documents:
            {context}
            
            Additional context (if any):
            {additional_context}
            
            Question: {input}
            
            Provide a precise, numerical answer when possible. For yes/no questions, answer clearly with yes or no.
            """)
            
            # Create chain
            llm = ChatOpenAI(model_name="gpt-4", temperature=0)
            document_chain = create_stuff_documents_chain(llm, prompt)
            retrieval_chain = create_retrieval_chain(retriever, document_chain)
            
            # Get answer with RAG
            result = retrieval_chain.invoke({
                "input": question,
                "additional_context": context
            })
            
            answer = result.get("answer", "")
        else:
            # Fallback to direct GPT-4 without RAG
            llm = ChatOpenAI(model_name="gpt-4", temperature=0)
            
            prompt = f"""
            You are a financial analysis expert. Answer this question precisely.
            
            Context: {context}
            Question: {question}
            
            Provide a concise, numerical answer when possible. For yes/no questions, answer clearly with yes or no.
            """
            
            response = llm.invoke(prompt)
            answer = response.content
        
        # Extract the final answer (look for numbers or yes/no)
        # First look for patterns like "$X,XXX" or "X million"
        import re
        
        # Try to find monetary values
        money_pattern = r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion))?'
        money_matches = re.findall(money_pattern, answer)
        if money_matches:
            # Return the last monetary value found
            return money_matches[-1]
        
        # Try to find standalone numbers
        number_pattern = r'\b\d+[,\d]*(?:\.\d+)?\b'
        number_matches = re.findall(number_pattern, answer)
        if number_matches:
            # Look for numbers with context
            for match in reversed(number_matches):
                # Skip years like 2024, 2023
                if len(match) == 4 and match.startswith('20'):
                    continue
                return match
        
        # Look for yes/no answers
        if 'yes' in answer.lower():
            return 'yes'
        if 'no' in answer.lower():
            return 'no'
        
        # Fallback to looking for lines with numbers
        lines = answer.split('\n')
        for line in reversed(lines):
            if line.strip() and any(char.isdigit() for char in line):
                # Extract just the number from the line
                nums = re.findall(r'\$?[\d,]+(?:\.\d+)?', line)
                if nums:
                    return nums[0]
        
        return answer.strip()
    
    # Limit test_size to dataset size
    test_size = min(test_size, len(dataset))
    
    correct = 0
    errors = 0
    close_matches = 0
    
    results_by_type = {
        "tactical": {"correct": 0, "total": 0},
        "calculation": {"correct": 0, "total": 0},
        "conceptual": {"correct": 0, "total": 0}
    }
    
    all_results = []
    
    print("="*70)
    print("FINANCEQA BENCHMARK EVALUATION")
    print("="*70)
    print(f"Testing {test_size} questions from official dataset")
    print(f"Total dataset size: {len(dataset)} questions")
    print(f"Target accuracy: 56.8% (baseline from paper)")
    print("="*70)
    print()
    
    for i in range(test_size):
        row = dataset[i]
        question = row["question"]
        context = row.get("context", "")
        expected = row["answer"]
        
        # Determine question type
        if any(word in question.lower() for word in ["calculate", "compute", "what is the", "how much"]):
            q_type = "calculation" if "calculate" in question.lower() else "tactical"
        else:
            q_type = "conceptual"
        
        results_by_type[q_type]["total"] += 1
        
        try:
            print(f"[{i+1}/{test_size}] Type: {q_type.upper()}")
            print(f"Q: {question[:80]}...")
            if context:
                print(f"Context: {context[:100]}...")
            
            start_time = time.time()
            
            # Call our agent
            result = process_question_enhanced(question, context)
            
            elapsed = time.time() - start_time
            
            # Check if answers match
            exact_match = (result == expected)
            smart_match = answers_match(expected, result)
            
            if smart_match:
                correct += 1
                results_by_type[q_type]["correct"] += 1
                if not exact_match:
                    close_matches += 1
            
            # Show results
            print(f"Expected: {expected}")
            print(f"Got:      {result[:100]}..." if len(result) > 100 else f"Got:      {result}")
            
            # Show numerical comparison if applicable
            exp_num = extract_number(expected)
            got_num = extract_number(result)
            if exp_num is not None and got_num is not None:
                diff = abs(exp_num - got_num) / max(abs(exp_num), 0.01) * 100
                print(f"Numbers:  {exp_num} vs {got_num} (diff: {diff:.2f}%)")
            
            match_type = '✓ EXACT' if exact_match else '✓ SMART' if smart_match else '✗ FAIL'
            print(f"Result:   {match_type}")
            print(f"Time:     {elapsed:.1f}s")
            print(f"Running:  {(correct/(i+1)*100):.1f}% accurate")
            print("-"*70)
            
            # Store result
            all_results.append({
                "question": question,
                "context": context,
                "expected": expected,
                "got": result,
                "type": q_type,
                "match": smart_match,
                "exact": exact_match,
                "time": elapsed
            })
            
            # Pause to avoid rate limits
            if (i + 1) % 5 == 0:
                time.sleep(2)
                
        except Exception as e:
            errors += 1
            print(f"ERROR: {str(e)[:200]}")
            print("-"*70)
            
            all_results.append({
                "question": question,
                "type": q_type,
                "error": str(e),
                "match": False
            })
            
            if "rate_limit" in str(e).lower():
                print("Waiting 60 seconds for rate limit...")
                time.sleep(60)
    
    # Calculate final results
    overall_accuracy = (correct / test_size * 100) if test_size > 0 else 0
    
    print("\n" + "="*70)
    print("BENCHMARK RESULTS")
    print("="*70)
    
    # Results by type
    for q_type, stats in results_by_type.items():
        if stats["total"] > 0:
            accuracy = (stats["correct"] / stats["total"]) * 100
            print(f"\n{q_type.upper()}:")
            print(f"  Correct: {stats['correct']}/{stats['total']}")
            print(f"  Accuracy: {accuracy:.1f}%")
    
    print(f"\nOVERALL:")
    print(f"  Questions tested: {test_size}")
    print(f"  Correct answers:  {correct} ({overall_accuracy:.1f}%)")
    print(f"    - Exact matches: {correct - close_matches}")
    print(f"    - Smart matches: {close_matches}")
    print(f"  Errors: {errors}")
    
    print("\n" + "="*70)
    print("COMPARISON WITH BASELINE")
    print("="*70)
    print(f"Our Agent:     {overall_accuracy:.1f}%")
    print(f"Target (paper): 56.8%")
    print(f"Gap:           {56.8 - overall_accuracy:.1f}%")
    
    if overall_accuracy >= 56.8:
        print("\n🎉 SUCCESS! We beat the baseline!")
    elif overall_accuracy >= 50:
        print("\n✅ Good performance, approaching baseline")
    else:
        print("\n⚠️ Below 50%, needs improvement")
    
    # Save detailed results
    results_file = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": test_size,
            "correct": correct,
            "accuracy": overall_accuracy,
            "exact_matches": correct - close_matches,
            "smart_matches": close_matches,
            "errors": errors
        },
        "by_type": results_by_type,
        "target": 56.8,
        "gap": 56.8 - overall_accuracy,
        "detailed": all_results
    }
    
    with open("/data/benchmark_results.json", "w") as f:
        json.dump(results_file, f, indent=2)
    
    print(f"\nDetailed results saved to benchmark_results.json")
    print("="*70)
    
    return overall_accuracy

@app.local_entrypoint()
def main(test_size: int = 20):
    """
    Run the benchmark evaluation.
    
    Args:
        test_size: Number of questions to test (default: 20)
    """
    print(f"\nStarting FinanceQA benchmark with {test_size} questions...")
    accuracy = run_benchmark.remote(test_size)
    print(f"\nFinal accuracy: {accuracy:.1f}%")
    return accuracy
