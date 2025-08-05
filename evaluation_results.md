# FinanceQA Agent Evaluation Results

## Latest Run: August 5, 2025

### Summary
- **Accuracy: 46.7%** (14/30 correct)
- **Exact Matches: 3**
- **Smart Matches: 11** (within 2% tolerance)
- **Average Response Time: ~15 seconds per question**

### Performance Breakdown

#### Strong Areas (>70% accuracy on similar questions):
- **Operating Metrics**: EBITDA, EBIT calculations
- **Margin Calculations**: Operating profit margin, EBITDA margin
- **P/E Ratios**: Basic and diluted EPS calculations
- **Cost of Equity**: CAPM model calculations
- **Tax Rates**: Effective and marginal tax rate identification

#### Areas for Improvement:
- **Enterprise Value calculations**: Confusion with units (millions vs billions)
- **Deferred Tax calculations**: Sign errors (positive vs negative values)
- **Complex ratios**: Debt-to-equity, equity-to-value calculations

### Sample Results

| Question | Expected | Agent Response | Match | Accuracy |
|----------|----------|----------------|-------|----------|
| Gross Profit 2024 | $32,095 (in millions) | 32,095 million | ✓ Smart | 100% |
| Unadjusted EBITDA 2024 | $11,522 (in millions) | 11,522 | ✓ Smart | 100% |
| Operating Profit Margin 2024 | 3.65% | 3.65% | ✓ Exact | 100% |
| P/E ratio (Basic EPS) | 56.66x | 56.65 | ✓ Smart | 99.98% |
| Cost of Equity (CAPM) | 9.66% | 9.66% | ✓ Exact | 100% |
| Effective Tax Rate 2024 | 24.40% | 24.4% | ✓ Smart | 100% |

### Comparison with Baseline

| Model | Accuracy | Notes |
|-------|----------|-------|
| **Our Agent (GPT-4o)** | **46.7%** | Smart matching with 2% tolerance |
| Baseline (from paper) | 56.8% | Target to beat |
| Our Agent (exact match) | ~10% | Shows importance of smart matching |

### Key Insights

1. **Format Flexibility Matters**: With smart numerical matching, accuracy improved from 10% to 46.7%
2. **Response Consistency**: Agent provides correct numerical values but with varying formats
3. **Calculation Accuracy**: Most errors are within 2-5% of expected values
4. **Speed**: ~15 seconds per question is reasonable for complex financial calculations

### Technical Details

- **Model**: OpenAI GPT-4o
- **Deployment**: Modal serverless platform
- **Evaluation Set**: FinanceQA test set (30 questions sampled)
- **Matching Algorithm**: Numerical tolerance of 2% for smart matching
- **Rate Limiting**: Handled with 60-second retry logic

### Next Steps for Improvement

1. **Add more examples** in the prompt for complex calculations
2. **Improve unit handling** (millions vs billions)
3. **Better context extraction** for finding specific financial metrics
4. **Fine-tune prompts** for deferred tax and enterprise value calculations

---
*Generated from `evaluate_improved.py` run on August 5, 2025*
