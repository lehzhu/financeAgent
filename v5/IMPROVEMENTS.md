# V5 Finance Agent - Improvements Summary

## Overview
V5 represents a significant improvement over V4, combining the working components from V4 with a more structured, deterministic approach to financial calculations and better routing logic.

## Key Improvements Over V4

### 1. **Enhanced Router** 
- **Smarter heuristics**: Uses weighted scoring across multiple keyword categories
- **Better pattern matching**: Distinguishes between calculation, structured lookup, and narrative questions
- **Assumption detection**: Identifies when calculations need special adjustments (non-GAAP, exclusions, etc.)

### 2. **Deterministic Finance Math Engine**
- **Precise calculations**: Uses Python's `Decimal` for exact arithmetic (no floating-point errors)
- **Extensive formula library**: 30+ financial formulas including:
  - Profitability metrics (margins, EBITDA, EBIT)
  - Growth calculations (YoY, CAGR)
  - Liquidity ratios (current, quick, working capital)
  - Leverage ratios (debt-to-equity, debt ratio)
  - Return metrics (ROE, ROA, ROIC)
  - Cash flow metrics (FCF, FCF conversion)
- **Traceable computations**: Every calculation step is logged for audit

### 3. **Structured Response Format**
- **Consistent JSON output**: All responses follow a strict schema
- **Type safety**: Explicit types (number, percent, text) with appropriate units
- **Execution trace**: Full visibility into routing and computation steps
- **Source tracking**: Clear attribution of data sources

### 4. **Complete Tool Integration**
- **Structured Data Lookup**: Enhanced SQL query builder with trend/comparison support
- **Narrative Search**: FAISS-based semantic search with metadata tracking
- **Calculator**: Fallback to V4's AST-based safe calculator when needed

### 5. **Better Error Handling**
- **Graceful fallbacks**: Each tool has error recovery
- **Detailed logging**: Comprehensive error tracking for debugging
- **Input validation**: Checks for required inputs before computation

## Architecture Comparison

### V4 Architecture
```
Question → GPT Router → Tool → GPT Formatter → Answer
```
- Heavy reliance on GPT-4o-mini for routing and formatting
- Tools return unstructured text
- Calculation extraction is unreliable

### V5 Architecture
```
Question → Heuristic Router → Deterministic Tool → JSON Formatter → Answer
```
- Lightweight heuristic router (no LLM needed)
- Tools return structured JSON
- Deterministic calculations with exact math

## Performance Expectations

### V4 Baseline (Current)
- Narrative: 100% accuracy
- Structured: 67% accuracy
- Calculations: 0% accuracy
- **Overall: ~50% accuracy**

### V5 Expected Improvements
- Narrative: 100% accuracy (maintained)
- Structured: 75-80% accuracy (better query building)
- Calculations: 60-80% accuracy (deterministic engine)
- **Target Overall: 70-80% accuracy**

## Deployment Instructions

### 1. Test Locally
```bash
# Run component tests
python3 v5/test_local.py
```

### 2. Deploy to Modal
```bash
# Deploy the v5 agent
modal deploy v5/deploy.py

# Test with a question
modal run v5/deploy.py --question "What was Costco's revenue in 2024?"
```

### 3. Run Evaluation
```bash
# Evaluate on FinanceQA dataset
modal run v5/evaluate_v5.py --dataset-path hf:AfterQuery/FinanceQA --limit 100
```

## Next Steps for Further Improvement

### Immediate (for 80%+ accuracy)
1. **Expand SQL metrics mapping** - Add more financial line items
2. **Implement metric aliases** - Handle variations in terminology
3. **Add calculation fallbacks** - If formula fails, try structured lookup
4. **Enhance narrative summarization** - Use LLM for better synthesis

### Medium-term (for 90%+ accuracy)
1. **Multi-step calculations** - Chain multiple formulas together
2. **Context awareness** - Use previous Q&A in session
3. **Company-specific adjustments** - Handle company accounting policies
4. **Time-series analysis** - Built-in trend calculations

### Long-term (for 95%+ accuracy)
1. **Learning from feedback** - Adjust routing based on accuracy
2. **Custom formula builder** - Parse natural language to formula
3. **Cross-validation** - Check answers against multiple sources
4. **Explanation generation** - Detailed reasoning for each answer

## Known Limitations

1. **Calculation complexity**: Currently handles single-formula calculations
2. **Data availability**: Limited to what's in SQLite/FAISS indices
3. **Context understanding**: No session memory between questions
4. **LLM dependency**: Still needs OpenAI for embeddings in narrative search

## Testing Checklist

- [x] Router correctly classifies questions
- [x] Finance math engine computes accurately
- [x] Structured lookup queries database
- [x] Narrative search retrieves documents
- [x] Orchestrator coordinates tools
- [x] JSON formatting is consistent
- [ ] Modal deployment works
- [ ] Evaluation shows improvement over V4

## Summary

V5 represents a pragmatic evolution of V4, keeping what works (the three-tool architecture) while fixing what doesn't (unreliable calculations, poor routing). The deterministic approach to financial calculations and structured JSON outputs make the system more reliable and debuggable.

The modular design allows for incremental improvements - each tool can be enhanced independently without breaking the others. This positions V5 as a solid foundation for achieving the 80% accuracy target and beyond.
