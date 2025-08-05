PRD: FinanceQA AI Agent
Project Overview
Build an agentic AI system to achieve >60% accuracy on the FinanceQA benchmark, surpassing the current 54.1% baseline through enhanced retrieval and multi-step reasoning.
Timeline: 4-8 hours development, 1 week submission
Target: Beat 54.1% baseline on FinanceQA evaluation dataset
Focus: Thought process and implementation over raw score


The FinanceQA Challenge
Benchmark Structure
FinanceQA evaluates AI on three financial analysis task types:

Basic Tactical (~65% current best)

Calculate financial metrics from 10-K documents
Requires exact accounting standard compliance
Examples: Operating margin, ROE, debt ratios


Assumption-Based (~8.4% current accuracy)

Handle incomplete information scenarios
Generate defensible financial assumptions
Most challenging category for current LLMs


Conceptual (~60% current performance)

Financial reasoning and principle application
Relationship understanding between metrics
Professional judgment questions



Key Requirements

Exact-match accuracy: No partial credit
GAAP compliance: Follow accounting standards precisely
Primary source analysis: Work directly with 10-K documents
Professional-grade precision: Single errors invalidate results

Solution Architecture
Core Components
Query → Planning Agent → Enhanced RAG → Tool Execution → Verification → Answer
1. Planning Agent

Classify question type (basic/assumption/conceptual)
Identify required data points and calculations
Generate step-by-step solution plan
Detect missing information for assumption questions

2. Enhanced RAG System

Stage 1: Semantic search across financial documents (top 50)
Stage 2: ZeroEntropy reranking for precision (top 10)
Stage 3: Context assembly with cross-references

3. Financial Tools

GAAP-compliant calculator
Standard financial formulas library
Assumption generation engine
Data extraction utilities

4. Verification Engine

Sanity check calculations
Validate accounting compliance
Cross-reference internal consistency
Assess assumption reasonableness

Implementation Plan
Phase 1: RAG Foundation (2-3 hours)

Integrate ZeroEntropy reranker
Build financial document corpus
Implement semantic search pipeline
Create context assembly logic

Phase 2: Agent Core (2-3 hours)

Build planning agent with task classification
Implement financial calculator with GAAP rules
Create assumption generation for missing data
Add multi-step reasoning execution

Phase 3: Polish & Evaluate (1-2 hours)

Add verification and self-correction
Test on FinanceQA sample questions
Optimize accuracy and edge cases
Document approach and results

Technical Specifications
Required Components

LLM: GPT-4 or Claude Sonnet for reasoning
Reranker: ZeroEntropy API for document relevance
Vector DB: Chroma/FAISS for semantic search
Framework: LangChain or custom implementation

Data Sources

Financial documents (10-K filings)
GAAP accounting rules
Industry standard assumptions
Financial formula definitions

Success Metrics

Primary: >60% overall FinanceQA accuracy
Basic Tactical: >75% (leverage strong retrieval)
Assumption-Based: >25% (5x current baseline)
Conceptual: >70% (domain knowledge boost)

Code Architecture
Agent Class Structure
pythonclass FinanceQAAgent:
    def __init__(self):
        self.planner = TaskPlanner()
        self.retriever = EnhancedRAG()
        self.calculator = FinancialCalculator()
        self.assumption_engine = AssumptionGenerator()
        self.verifier = AccuracyVerifier()
    
    def solve(self, question: str) -> str:
        # 1. Plan solution approach
        plan = self.planner.create_plan(question)
        
        # 2. Retrieve relevant context
        context = self.retriever.get_context(question)
        
        # 3. Execute calculation/reasoning
        result = self.execute_plan(plan, context)
        
        # 4. Verify and self-correct
        verified_result = self.verifier.validate(result)
        
        return verified_result
Key Methods

classify_question_type(): Identify basic/assumption/conceptual
extract_financial_data(): Parse numbers from documents
generate_assumptions(): Handle missing data scenarios
calculate_metrics(): Apply GAAP-compliant formulas
verify_accuracy(): Multi-layer validation

Risk Mitigation
Technical Risks

API Rate Limits: Implement caching and fallbacks
Calculation Errors: Extensive validation and testing
Missing Context: Robust assumption generation
Format Compliance: Strict output formatting

Success Dependencies

ZeroEntropy reranker availability and performance
Quality financial document preprocessing
Accurate assumption generation logic
Comprehensive GAAP rule implementation

Evaluation Strategy
Testing Approach

Sample 50 FinanceQA questions across all categories
Measure exact-match accuracy per category
Analyze failure modes and common errors
Iterate on weak areas (especially assumptions)

Success Criteria

Working agent that processes all FinanceQA question types
Clear documentation of design decisions
Measurable improvement over 54.1% baseline
Robust handling of edge cases and missing data

Future Improvements
Short-term (1-2 weeks)

Fine-tune assumption generation with expert validation
Add more specialized financial tools and APIs
Implement multi-model ensemble approach

Long-term (1-3 months)

Custom embeddings trained on financial corpus
Real-time market data integration
Advanced reasoning with financial domain models

Deliverables
Code Deliverables

Complete agent implementation
Financial tools and calculators
RAG system with ZeroEntropy integration
Evaluation scripts and results

Documentation

Agent design overview
Key trade-offs and decisions
Benchmark evaluation results
Future improvement suggestions

Optional

Docker containerization
Cloud deployment setup
Performance optimization analysis


Quick Start Commands
bash# Install dependencies
pip install -r requirements.txt

# Run evaluation
python evaluate_agent.py --dataset financeqa --output results.json

# Test single question
python agent.py --question "What is the operating margin for 2024?"
This PRD provides clear structure and implementation guidance while maintaining flexibility for different technical approaches within the 4-8 hour development window.