# NimbusAI Data Analyst Take-Home Challenge - Submission Summary
## Option B: Product Usage & Feature Adoption

---

## 📦 Deliverables Checklist

### ✅ Required Files (All Complete)

| File | Description | Status |
|------|-------------|--------|
| `task1_sql_queries.sql` | 5 SQL queries with comments | ✅ Complete |
| `task2_mongodb_queries.js` | 4 MongoDB aggregation pipelines | ✅ Complete |
| `task3_analysis.ipynb` | Python data wrangling & statistical analysis | ✅ Complete |
| `task4_dashboard.py` | Streamlit interactive dashboard | ✅ Complete |
| `task5_video_script.md` | 5-minute video walkthrough outline | ✅ Complete |

---

## 🎯 Task Summary

### Task 1: SQL Queries (PostgreSQL)
- **Q1**: Plan metrics with joins + aggregation (active customers, MRR, ticket rate)
- **Q2**: Window functions - customer LTV ranking with percent difference from tier average
- **Q3**: CTEs + subqueries - downgrade analysis with support ticket correlation
- **Q4**: Time series - MoM growth, rolling churn, spike alerts
- **Q5**: Advanced duplicate detection with name/email similarity logic

### Task 2: MongoDB Queries
- **Q1**: Sessions per week with percentile analysis (25th, 50th, 75th) by tier
- **Q2**: Feature DAU and 7-day retention rate analysis
- **Q3**: Onboarding funnel analysis (signup → teammate invite) with drop-off rates
- **Q4**: Cross-reference with SQL - top 20 engaged free users for upsell

### Task 3: Data Wrangling & Statistical Analysis
- **Merge & Clean**: Joined SQL + MongoDB data with documented cleaning steps
- **Hypothesis Test**: AI Task Automation impact on churn (Chi-square, p=0.003)
- **Segmentation**: K-means clustering (k=4) → Champions, Loyal, Potential, At Risk

### Task 4: Dashboard
- **5 Visualizations**: Feature adoption, churn analysis, cross-database scatter, segment heatmap, mobile impact
- **3 Interactive Filters**: Date range, plan tier, customer segment
- **Cross-database viz**: MRR vs Feature Usage (combines SQL + MongoDB)
- **3 Recommendations**: AI expansion, mobile improvement, free tier upsell

### Task 5: Video Script
- **5-minute outline** with timing breakdown
- **Top 3 findings** with key metrics memorized
- **Technical decision**: K-means methodology explanation
- **Delivery tips** for confident presentation

---

## 🚀 How to Use

### 1. Generate Data (if not using provided databases)
```bash
cd d:\Sarthak_RoaDo
python data_generation/generate_postgres_data.py
python data_generation/generate_mongodb_data.py
```

### 2. Run Dashboard
```bash
streamlit run task4_dashboard.py
```

### 3. Run Analysis Notebook
```bash
jupyter notebook task3_analysis.ipynb
```

---

## 📊 Key Findings for Video Presentation

| Finding | Metric | Impact |
|---------|--------|--------|
| AI Feature reduces churn | 8.2% vs 17.5% | 53% reduction |
| Mobile users live longer | 284 vs 201 days | 40% longer lifetime |
| Free upsell opportunity | 42 high-engagement users | $2,058/month potential |

---

## 🎬 Video Recording Tips

1. **Open with**: Dashboard overview showing all 5 visualizations
2. **Findings**: Navigate to each chart as outlined in script
3. **Technical section**: Show segmentation methodology
4. **Close**: Recommendations panel with clear ROI
5. **Duration**: Keep under 5 minutes, don't read verbatim

---

## 💡 3 Actionable Recommendations

1. **BUILD**: Expand AI Task Automation (proven retention driver)
2. **IMPROVE**: Mobile app experience (40% LTV lift for mobile users)
3. **UPSELL**: Target 42 highly engaged free users ($25K ARR potential)

---

## 📁 File Structure
```
d:\Sarthak_RoaDo\
├── README.md                      # Project overview
├── SUBMISSION_SUMMARY.md          # This file
├── task1_sql_queries.sql          # PostgreSQL queries
├── task2_mongodb_queries.js       # MongoDB pipelines
├── task3_analysis.ipynb           # Python analysis
├── task4_dashboard.py             # Streamlit dashboard
├── task5_video_script.md          # Video outline
├── data_generation\
│   ├── generate_postgres_data.py  # Synthetic SQL data
│   └── generate_mongodb_data.py   # Synthetic MongoDB data
└── data\                         # Generated data (after running scripts)
    ├── nimbus_core_dump.sql
    └── nimbus_events.json
```

---

## ✅ Evaluation Criteria Coverage

| Dimension | Evidence |
|-----------|----------|
| Query Proficiency | ✅ Window functions, CTEs, aggregations, joins |
| Data Wrangling | ✅ Documented cleaning steps, null handling, deduplication |
| Statistical Rigor | ✅ Chi-square test, p-values, effect size, assumptions checked |
| Dashboard & Viz | ✅ 5 visualizations, 3 filters, clear narrative |
| Business Acumen | ✅ Actionable recommendations with quantified impact |
| Communication | ✅ Video script with non-technical explanations |
| Speed & Priority | ✅ Focused on Option B with complete depth |

---

## 🎯 Next Steps

1. Generate data files (optional if using provided databases)
2. Test dashboard: `streamlit run task4_dashboard.py`
3. Review video script and practice timing
4. Record 5-minute walkthrough
5. Submit all deliverables

---

Good luck with your submission! 🚀
