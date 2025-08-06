import modal

app = modal.App("test-functions")

@app.function()
def test_deployed_apps():
    """Test what functions are available in deployed apps"""
    
    app_names = [
        "finance-agent-v4-enhanced",
        "finance-agent-v4", 
        "finance-agent-main",
        "finance-agent-v3"
    ]
    
    function_names = [
        "process_question_v4",
        "process_question",
        "main",
        "handle_request",
        "web_endpoint_v4"
    ]
    
    for app_name in app_names:
        print(f"\n{'='*60}")
        print(f"Testing app: {app_name}")
        print('='*60)
        
        for func_name in function_names:
            try:
                func = modal.Function.from_name(app_name, func_name)
                print(f"✓ Found function: {func_name}")
                
                # Try to call it with a simple test
                if "process" in func_name or "handle" in func_name:
                    try:
                        result = func.remote("What is 2+2?")
                        print(f"  - Test call successful! Result: {str(result)[:100]}...")
                    except Exception as e:
                        print(f"  - Test call failed: {str(e)[:100]}...")
                        
            except Exception as e:
                if "not found" not in str(e).lower():
                    print(f"✗ Error with {func_name}: {str(e)[:100]}...")

@app.local_entrypoint()
def main():
    test_deployed_apps.remote()
