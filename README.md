# NimbusAI Data Analyst Take-Home

**Option B: Product Usage & Feature Adoption**

This is my submission for the Data Analyst Intern take-home challenge. I analyzed how customers use NimbusAI's features to identify what drives engagement and where the best expansion opportunities are.

## What's Inside

| File | What it does |
|------|-------------|
| `task1_sql_queries.sql` | 5 PostgreSQL queries answering business questions |
| `task2_mongodb_queries.js` | 4 MongoDB pipelines for event analysis |
| `task3_analysis.ipynb` | Python notebook with statistical analysis & segmentation |
| `task4_dashboard.py` | Interactive Streamlit dashboard |
| `task5_video_script.md` | My 5-min presentation outline |

## Quick Start

```bash
# Run the dashboard
streamlit run task4_dashboard.py

# Or open the notebook
jupyter notebook task3_analysis.ipynb
```

## Key Findings

1. **AI Task Automation reduces churn by 53%** (8.2% vs 17.5% for non-users)
2. **Mobile users stick around 40% longer** - major opportunity
3. **42 high-engagement free users** ready for upsell campaigns

## My Approach

I focused on practical insights the product team can act on. The SQL queries use window functions and CTEs for clean analysis, MongoDB pipelines handle the event data, and the dashboard lets stakeholders explore interactively.

Questions? Check `SUBMISSION_SUMMARY.md` for details.
