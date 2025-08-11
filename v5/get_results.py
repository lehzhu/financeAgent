#!/usr/bin/env python3
"""
Retrieve and display evaluation results from Modal volume
"""

import modal
import json

app = modal.App("get-results")
volume = modal.Volume.from_name("financeagent-v5-results")

@app.function(volumes={"/root/results": volume})
def retrieve_results(path: str = "/root/results/results.json"):
    """Retrieve results from Modal volume."""
    import os
    
    # List all files in the results directory
    if os.path.exists("/root/results"):
        print("Files in results directory:")
        for root, dirs, files in os.walk("/root/results"):
            for file in files:
                filepath = os.path.join(root, file)
                print(f"  - {filepath}")
    
    # Try to read the results file
    if os.path.exists(path):
        with open(path, "r") as f:
            results = json.load(f)
        
        print(f"\nFound results at {path}")
        print(f"Number of results: {len(results)}")
        
        # Analyze results
        correct = 0
        errors = 0
        
        for i, result in enumerate(results):
            print(f"\n--- Result {i+1} ---")
            print(f"ID: {result.get('id', 'N/A')}")
            
            # Get the answer
            if 'final_answer' in result:
                answer = result['final_answer']
                print(f"Answer Type: {answer.get('type', 'N/A')}")
                print(f"Answer Value: {answer.get('value', 'N/A')[:100]}")
            
            # Check trace
            if 'trace' in result and result['trace']:
                print(f"Execution Path: {result['trace'][0] if result['trace'] else 'N/A'}")
            
            # Check for errors
            if 'error' in result or (isinstance(result.get('final_answer', {}).get('value'), str) and 
                                      'error' in result.get('final_answer', {}).get('value', '').lower()):
                errors += 1
        
        # Summary statistics
        print("\n" + "="*60)
        print("EVALUATION SUMMARY")
        print("="*60)
        print(f"Total Questions: {len(results)}")
        print(f"Errors: {errors}")
        print(f"Success Rate: {(len(results) - errors) / len(results) * 100:.1f}%")
        
        return results
    else:
        print(f"No results file found at {path}")
        return None

@app.local_entrypoint()
def main():
    """Retrieve and display evaluation results."""
    results = retrieve_results.remote()
    
    if results:
        # Save locally
        output_file = "evaluation_results.json"
        with open(output_file, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved locally to {output_file}")

if __name__ == "__main__":
    with app.run():
        main()
