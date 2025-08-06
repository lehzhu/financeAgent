"""
Finance Agent v4: Three-Tool Architecture
- structured_data_lookup: For specific financial metrics from database
- document_search: For conceptual/narrative questions from FAISS
- python_calculator: For mathematical calculations
"""

import modal
import os
import sqlite3
from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from typing import List, Dict, Optional
import json
import re

# Define the Modal app
app = modal.App(
    "finance-agent-v4-new",
    image=modal.Image.debian_slim().pip_install(
        "langchain", "langchain-community", "langchain-openai",
        "faiss-cpu", "openai", "tiktoken", "sqlite3"
    ),
    secrets=[modal.Secret.from_name("openai-key-1")]
)

# Use the volume for persistent storage
volume = modal.Volume.from_name("finance-agent-storage")

# Configuration
NARRATIVE_TOP_K = 5  # Number of narrative chunks to retrieve
CHUNK_SIZE = 1500
CHUNK_OVERLAP = 300

# --- Structured Data Lookup Tool ---

class StructuredDataLookup:
    """Tool for querying specific financial metrics from SQLite database."""
    
    def __init__(self, db_path: str = "/data/costco_financial_data.db"):
        self.db_path = db_path
        
    def query(self, question: str) -> str:
        """Query structured financial data based on the question."""
        try:
            # Extract key information from the question
            query_info = self._extract_query_info(question)
            
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Build and execute query
            sql = self._build_sql_query(query_info)
            print(f"Executing SQL: {sql}")
            cursor.execute(sql)
            
            results = cursor.fetchall()
            conn.close()
            
            # Format results
            if results:
                return self._format_results(results, query_info)
            else:
                return "No data found for the specified query."
                
        except Exception as e:
            return f"Error querying structured data: {str(e)}"
    
    def _extract_query_info(self, question: str) -> Dict:
        """Extract metric, year, and other info from question."""
        question_lower = question.lower()
        
        # Common financial metrics mapping
        metric_mapping = {
            'revenue': ['total revenue', 'net sales', 'revenue'],
            'gross profit': ['gross profit', 'gross margin'],
            'net income': ['net income', 'net earnings', 'profit'],
            'operating income': ['operating income', 'operating profit'],
            'eps': ['earnings per share', 'eps'],
            'total assets': ['total assets', 'assets'],
            'total liabilities': ['total liabilities', 'liabilities'],
            'stockholders equity': ['stockholders equity', 'equity', 'shareholders equity'],
            'cash': ['cash and cash equivalents', 'cash'],
            'inventory': ['merchandise inventories', 'inventory'],
        }
        
        # Extract metric
        metric = None
        for key, patterns in metric_mapping.items():
            for pattern in patterns:
                if pattern in question_lower:
                    metric = key
                    break
            if metric:
                break
        
        # Extract year
        year = None
        year_match = re.search(r'20\d{2}', question)
        if year_match:
            year = int(year_match.group())
        
        return {'metric': metric, 'year': year}
    
    def _build_sql_query(self, query_info: Dict) -> str:
        """Build SQL query based on extracted information."""
        base_query = "SELECT item, fiscal_year, value, unit FROM financial_data"
        conditions = []
        
        if query_info['metric']:
            conditions.append(f"LOWER(item) LIKE '%{query_info['metric'].lower()}%'")
        
        if query_info['year']:
            conditions.append(f"fiscal_year = {query_info['year']}")
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        base_query += " ORDER BY fiscal_year DESC LIMIT 10"
        return base_query
    
    def _format_results(self, results: List, query_info: Dict) -> str:
        """Format SQL results into readable text."""
        if not results:
            return "No results found."
        
        formatted = []
        for item, year, value, unit in results:
            if unit == 'millions':
                formatted.append(f"{item} ({year}): ${value:,.0f} million")
            elif unit == 'percent':
                formatted.append(f"{item} ({year}): {value}%")
            elif unit == 'dollars':
                formatted.append(f"{item} ({year}): ${value:.2f}")
            else:
                formatted.append(f"{item} ({year}): {value} {unit}")
        
        return "\\n".join(formatted)

# --- Narrative Document Search Tool ---

class NarrativeDocumentSearch:
    """Tool for searching narrative/conceptual content using FAISS."""
    
    def __init__(self):
        # Initialize FAISS for narrative content
        embeddings = OpenAIEmbeddings()
        self.kb = FAISS.load_local("/data/narrative_kb_index", embeddings, allow_dangerous_deserialization=True)
        self.retriever = self.kb.as_retriever(search_kwargs={"k": NARRATIVE_TOP_K})
    
    def search(self, query: str) -> str:
        """Search narrative documents for conceptual information."""
        print(f"Searching narrative content for: {query}")
        
        try:
            # Retrieve relevant documents
            docs = self.retriever.get_relevant_documents(query)
            
            if not docs:
                return "No relevant narrative content found."
            
            # Combine the top results
            combined_text = "\\n---\\n".join([doc.page_content for doc in docs])
            
            # Add context about the source
            return f"From the narrative sections of the 10-K:\\n\\n{combined_text}"
            
        except Exception as e:
            return f"Error searching narrative content: {str(e)}"

# --- Enhanced Calculator Tool (from previous implementation) ---

class EnhancedCalculator:
    """Safe mathematical calculator using AST parsing."""
    
    def calculate(self, expression: str) -> str:
        """Execute safe mathematical calculations using AST parsing."""
        import ast
        import operator
        import math
        
        # Define allowed operations
        allowed_operations = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }
        
        # Define allowed functions
        allowed_functions = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sum': sum,
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'ceil': math.ceil,
            'floor': math.floor,
        }
        
        # Define allowed constants
        allowed_names = {
            'pi': math.pi,
            'e': math.e,
        }
        
        def safe_eval(node):
            """Recursively evaluate AST nodes safely."""
            if isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                if type(node.op) in allowed_operations:
                    left = safe_eval(node.left)
                    right = safe_eval(node.right)
                    return allowed_operations[type(node.op)](left, right)
                else:
                    raise ValueError(f"Operation {type(node.op).__name__} not allowed")
            elif isinstance(node, ast.UnaryOp):
                if type(node.op) in allowed_operations:
                    operand = safe_eval(node.operand)
                    return allowed_operations[type(node.op)](operand)
                else:
                    raise ValueError(f"Unary operation {type(node.op).__name__} not allowed")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in allowed_functions:
                    args = [safe_eval(arg) for arg in node.args]
                    return allowed_functions[node.func.id](*args)
                else:
                    func_name = node.func.id if isinstance(node.func, ast.Name) else "unknown"
                    raise ValueError(f"Function '{func_name}' not allowed")
            elif isinstance(node, ast.Name):
                if node.id in allowed_names:
                    return allowed_names[node.id]
                else:
                    raise ValueError(f"Name '{node.id}' not allowed")
            elif isinstance(node, ast.List):
                return [safe_eval(elem) for elem in node.elts]
            elif isinstance(node, ast.Tuple):
                return tuple(safe_eval(elem) for elem in node.elts)
            else:
                raise ValueError(f"AST node type {type(node).__name__} not allowed")
        
        try:
            expr = expression.strip()
            tree = ast.parse(expr, mode='eval')
            result = safe_eval(tree.body)
            
            if isinstance(result, float):
                if result == int(result):
                    return str(int(result))
                else:
                    return f"{result:.10g}"
            else:
                return str(result)
                
        except SyntaxError as e:
            return f"Syntax error in expression: {str(e)}"
        except ValueError as e:
            return f"Security error: {str(e)}"
        except ZeroDivisionError:
            return "Error: Division by zero"
        except Exception as e:
            return f"Calculation error: {str(e)}"

# --- Finance Tools Manager ---

class FinanceToolsV4:
    """Manager for all three finance tools."""
    
    def __init__(self):
        self.structured_data = StructuredDataLookup()
        self.narrative_search = NarrativeDocumentSearch()
        self.calculator = EnhancedCalculator()
    
    def structured_data_lookup(self, question: str) -> str:
        """Query structured financial data."""
        return self.structured_data.query(question)
    
    def document_search(self, query: str) -> str:
        """Search narrative content."""
        return self.narrative_search.search(query)
    
    def python_calculator(self, expression: str) -> str:
        """Perform calculations."""
        return self.calculator.calculate(expression)

# --- Enhanced Router Agent ---

@app.function()
def router_agent_v4(question: str) -> str:
    """Enhanced router that chooses between three specialized tools."""
    client = OpenAI()
    
    prompt = f"""You are a routing agent. Think step-by-step to choose the best tool for this financial question.
    
Available Tools:
1. structured_data_lookup: Use for questions seeking specific numbers from financial statements
   - Examples: "What was revenue in 2024?", "Show me net income for the last 3 years", "What is the total assets?"
   
2. document_search: Use for conceptual or qualitative questions about strategy, risks, operations
   - Examples: "What are the main risk factors?", "Describe the business strategy", "What products does Costco sell?"
   
3. python_calculator: Use for explicit mathematical calculations
   - Examples: "Calculate 15% of 1 million", "What's the growth rate if revenue went from 100M to 150M?"

Question: {question}

Analyze step-by-step:
1. Is this asking for a specific financial number/metric? → structured_data_lookup
2. Is this asking about concepts, strategy, or qualitative information? → document_search
3. Is this asking to calculate something? → python_calculator

Choose the MOST appropriate tool. Respond with ONLY the tool name."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    tool = response.choices[0].message.content.strip().lower()
    print(f"Router selected: {tool}")
    return tool

# --- Calculation Agent ---

@app.function()
def calculation_agent_v4(question: str, context: str = None) -> str:
    """Extracts mathematical expressions from questions."""
    client = OpenAI()
    
    prompt = f"""Extract the mathematical calculation from this question. Think step-by-step.
    
Question: {question}
{f"Context: {context}" if context else ""}

Think step-by-step:
1. Identify all numbers mentioned in the question
2. Determine what mathematical operation is needed
3. Construct the expression using Python syntax

You can use:
- Basic operators: +, -, *, /, //, %, **
- Functions: sqrt(), abs(), round(), min(), max(), sum(), log(), log10(), exp()
- Trigonometric: sin(), cos(), tan()
- Rounding: ceil(), floor()
- Constants: pi, e

Return ONLY the mathematical expression to calculate.
If no calculation is needed, return "NO_CALCULATION".

Examples:
- "What is 30% of 1000?" → "1000 * 0.3"
- "Calculate growth rate from $100M to $150M" → "((150 - 100) / 100) * 100"

Expression:"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

# --- Final Answer Agent ---

@app.function()
def final_answer_agent_v4(question: str, tool_result: str, tool_type: str) -> str:
    """Formats the final answer with structured output."""
    client = OpenAI()
    
    # Add context based on tool type
    tool_context = {
        "structured_data_lookup": "The data comes from audited financial statements.",
        "document_search": "The information comes from the narrative sections of the 10-K filing.",
        "python_calculator": "The calculation was performed using the provided mathematical expression."
    }
    
    prompt = f"""You are a financial analyst providing a final answer. Think step-by-step.
    
Question: {question}
Tool Used: {tool_type}
Tool Result: {tool_result}
Context: {tool_context.get(tool_type, "")}

INSTRUCTIONS:
1. First, analyze the tool result to extract the key information
2. Think step-by-step about what the question is asking
3. Formulate your answer following these STRICT rules:

FORMATTING RULES:
- For NUMERICAL answers: Always present the final numerical answer in this EXACT format:
  {{"answer": <number>, "unit": "<unit>"}}
  Examples:
  {{"answer": 254123, "unit": "millions of USD"}}
  {{"answer": 23.5, "unit": "percent"}}
  {{"answer": 1250000, "unit": "shares"}}
  
- For YES/NO questions: Start your answer with exactly "Yes" or "No" (capital first letter), then explain.
  
- For OTHER questions: Be direct and specific. State the main answer in the first sentence.

IMPORTANT:
- For structured data results, present the exact numbers from the database
- For narrative results, synthesize the key points concisely
- For calculations, show both the expression and the result
- Always end numerical answers with the JSON format specified above

Think step-by-step, then provide your answer:"""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    
    return response.choices[0].message.content.strip()

# --- Main Workflow ---

@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def process_question_v4(question: str) -> str:
    """
    Enhanced workflow with three specialized tools:
    1. structured_data_lookup - for financial metrics
    2. document_search - for narrative/conceptual content
    3. python_calculator - for calculations
    """
    
    print("\\n" + "="*60)
    print("FINANCE AGENT V4: Three-Tool Architecture")
    print("="*60)
    
    # 1. Route to the appropriate tool
    tool_choice = router_agent_v4.remote(question)
    
    # 2. Initialize tools
    tools = FinanceToolsV4()
    
    # 3. Execute the selected tool
    if tool_choice == "structured_data_lookup":
        tool_result = tools.structured_data_lookup(question)
        
    elif tool_choice == "document_search":
        tool_result = tools.document_search(question)
        
    elif tool_choice == "python_calculator":
        calc_expr = calculation_agent_v4.remote(question)
        if calc_expr != "NO_CALCULATION":
            tool_result = f"Expression: {calc_expr}\\nResult: {tools.python_calculator(calc_expr)}"
        else:
            tool_result = "No calculation could be extracted from the question"
    
    else:
        # Fallback
        tool_result = "Unable to determine the appropriate tool for this question."
        tool_choice = "unknown"
    
    # 4. Generate final answer
    final_answer = final_answer_agent_v4.remote(question, tool_result, tool_choice)
    
    return final_answer

# --- Web Endpoint ---

@app.function(
    volumes={"/data": volume},
    secrets=[modal.Secret.from_name("openai-key-1")],
    timeout=120
)
def web_endpoint_v4(request: dict) -> dict:
    """HTTP endpoint for the three-tool finance agent."""
    question = request.get("question", "")
    
    if not question:
        return {"error": "No question provided"}
    
    try:
        answer = process_question_v4.remote(question)
        return {
            "question": question,
            "answer": answer,
            "version": "v4-three-tools",
            "status": "success"
        }
    except Exception as e:
        return {
            "question": question,
            "error": str(e),
            "version": "v4-three-tools",
            "status": "error"
        }

# --- Local Testing ---

@app.local_entrypoint()
def main(question: str = None):
    """Test the three-tool finance agent locally."""
    
    test_questions = [
        # Structured data questions
        "What was Costco's revenue in 2024?",
        "Show me net income for the last 3 years",
        "What is the gross profit margin?",
        
        # Narrative/conceptual questions
        "What are Costco's main risk factors?",
        "Describe Costco's business strategy",
        "What products does Costco sell?",
        
        # Calculation questions
        "Calculate 15% of 254 billion",
        "What's the growth rate if revenue increased from 230 billion to 254 billion?",
        "If gross margin is 11% and revenue is 254 billion, what is gross profit?",
    ]
    
    if question:
        # Test single question
        print(f"\\nQuestion: {question}")
        answer = process_question_v4.remote(question)
        print(f"\\nAnswer: {answer}")
    else:
        # Test all example questions
        print("\\n" + "="*60)
        print("TESTING THREE-TOOL FINANCE AGENT V4")
        print("="*60)
        
        for q in test_questions:
            print(f"\\nQuestion: {q}")
            answer = process_question_v4.remote(q)
            print(f"Answer: {answer}")
            print("-" * 40)
