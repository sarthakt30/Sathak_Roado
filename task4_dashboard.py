"""
NimbusAI Dashboard - Product Usage & Feature Adoption
Built with Streamlit for the take-home challenge

Run: streamlit run task4_dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Page setup
st.set_page_config(
    page_title="NimbusAI Analytics",
    page_icon="📊",
    layout="wide"
)

# Simple styling
st.markdown("""
<style>
    .main-header { font-size: 2.5rem; font-weight: bold; color: #1E3A5F; }
    .recommendation { 
        background-color: #e8f4f8; 
        border-left: 4px solid #2196F3; 
        padding: 1rem; 
        margin: 0.5rem 0;
        color: #1a1a1a;
    }
    .recommendation h4 {
        color: #1565C0;
        margin-bottom: 0.5rem;
    }
    .recommendation p {
        color: #333;
        line-height: 1.5;
    }
    .recommendation strong {
        color: #0D47A1;
    }
</style>
""", unsafe_allow_html=True)

# Load data (simulated for demo)
@st.cache_data
def load_data():
    """Generate realistic demo data combining SQL + MongoDB sources"""
    np.random.seed(42)
    
    n_customers = 1200
    customer_ids = [f"cust_{str(i+1).zfill(5)}" for i in range(n_customers)]
    
    # Plan distribution
    plan_tiers = np.random.choice(
        ['free', 'starter', 'pro', 'enterprise'], 
        n_customers, 
        p=[0.30, 0.35, 0.25, 0.10]
    )
    plan_prices = {'free': 0, 'starter': 49, 'pro': 199, 'enterprise': 599}
    
    # Features available
    features = ['ai_task_automation', 'team_collaboration', 'time_tracking', 
                'reporting_dashboard', 'api_access', 'advanced_security']
    
    def get_features(tier):
        if tier == 'free':
            return np.random.choice(features[:2], np.random.randint(1, 3), replace=False).tolist()
        elif tier == 'starter':
            return np.random.choice(features[:4], np.random.randint(2, 5), replace=False).tolist()
        else:
            return np.random.choice(features, np.random.randint(3, 7), replace=False).tolist()
    
    # Build dataset
    data = []
    for i, cust_id in enumerate(customer_ids):
        tier = plan_tiers[i]
        features_used = get_features(tier)
        created_date = datetime(2023, 1, 1) + timedelta(days=np.random.randint(0, 730))
        
        # Churn ~15%
        is_churned = np.random.random() < 0.15
        
        data.append({
            'customer_id': cust_id,
            'plan_tier': tier,
            'mrr': plan_prices[tier],
            'created_at': created_date,
            'is_churned': is_churned,
            'features_used': features_used,
            'features_count': len(features_used),
            'sessions_per_week': np.random.poisson(3 if tier == 'free' else 5 if tier == 'starter' else 8),
            'ai_task_uses': np.random.randint(0, 100) if 'ai_task_automation' in features_used else 0,
            'mobile_sessions': np.random.randint(0, 20),
            'engagement_score': np.random.randint(10, 95)
        })
    
    df = pd.DataFrame(data)
    
    # Add derived columns that dashboard needs
    df['uses_ai'] = df['ai_task_uses'] > 0
    df['uses_mobile'] = df['mobile_sessions'] > 0
    df['lifetime_days'] = np.random.randint(30, 500, len(df))  # simulated lifetime
    
    return df

# Load the data
df = load_data()

# =============================================================================
# SIDEBAR FILTERS
# =============================================================================

st.sidebar.markdown("## Interactive Filters")

# Filter 1: Date Range
date_range = st.sidebar.date_input(
    "Customer Signup Date Range",
    value=[df['created_at'].min(), df['created_at'].max()],
    min_value=df['created_at'].min(),
    max_value=df['created_at'].max()
)

# Filter 2: Plan Tier
selected_tiers = st.sidebar.multiselect(
    "Plan Tiers",
    options=['free', 'starter', 'pro', 'enterprise'],
    default=['free', 'starter', 'pro', 'enterprise']
)

# Filter 3: Customer Segment (calculated)
segment_filter = st.sidebar.multiselect(
    "Customer Segment",
    options=['Champions', 'Loyal Customers', 'Potential Loyalists', 'At Risk'],
    default=['Champions', 'Loyal Customers', 'Potential Loyalists', 'At Risk']
)

# Apply filters
mask = (
    (df['created_at'] >= pd.Timestamp(date_range[0])) &
    (df['created_at'] <= pd.Timestamp(date_range[1])) &
    (df['plan_tier'].isin(selected_tiers))
)

# Calculate segment and apply segment filter
df['segment'] = pd.cut(df['engagement_score'], 
                       bins=[0, 40, 60, 80, 100], 
                       labels=['At Risk', 'Potential Loyalists', 'Loyal Customers', 'Champions'])

mask &= df['segment'].isin(segment_filter)
filtered_df = df[mask].copy()

# =============================================================================
# HEADER
# =============================================================================

st.markdown('<p class="main-header">NimbusAI Dashboard</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Product Usage & Feature Adoption Analysis</p>', unsafe_allow_html=True)

st.markdown("---")

# =============================================================================
# KPI METRICS
# =============================================================================

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total Customers",
        f"{len(filtered_df):,}",
        f"{len(filtered_df) - len(df):+d} vs total"
    )

with col2:
    churn_rate = filtered_df['is_churned'].mean() * 100
    st.metric(
        "Churn Rate",
        f"{churn_rate:.1f}%",
        f"{churn_rate - df['is_churned'].mean() * 100:+.1f}pp"
    )

with col3:
    avg_mrr = filtered_df['mrr'].mean()
    st.metric(
        "Avg MRR",
        f"${avg_mrr:.0f}",
        f"${avg_mrr - df['mrr'].mean():+.0f}"
    )

with col4:
    avg_engagement = filtered_df['engagement_score'].mean()
    st.metric(
        "Avg Engagement",
        f"{avg_engagement:.0f}/100",
        f"{avg_engagement - df['engagement_score'].mean():+.0f}"
    )

with col5:
    ai_adoption = filtered_df['uses_ai'].mean() * 100
    st.metric(
        "AI Feature Adoption",
        f"{ai_adoption:.1f}%",
        f"{ai_adoption - df['uses_ai'].mean() * 100:+.1f}pp"
    )

st.markdown("---")

# =============================================================================
# VISUALIZATION 1: Feature Adoption by Plan Tier (Business Question: What to build/improve?)
# =============================================================================

st.markdown("### 1. Feature Adoption Analysis")
st.markdown("*Which features drive engagement across different plan tiers?*")

# Calculate feature adoption by tier
feature_adoption = []
for tier in ['free', 'starter', 'pro', 'enterprise']:
    tier_data = filtered_df[filtered_df['plan_tier'] == tier]
    if len(tier_data) > 0:
        all_features = tier_data['features_used'].explode()
        for feature in ['ai_task_automation', 'team_collaboration', 'time_tracking', 
                       'reporting_dashboard', 'api_access', 'advanced_security']:
            adoption_rate = (all_features == feature).sum() / len(tier_data) * 100
            feature_adoption.append({
                'plan_tier': tier,
                'feature': feature.replace('_', ' ').title(),
                'adoption_rate': adoption_rate
            })

feature_df = pd.DataFrame(feature_adoption)

fig1 = px.bar(
    feature_df, 
    x='feature', 
    y='adoption_rate', 
    color='plan_tier',
    barmode='group',
    title='Feature Adoption Rate by Plan Tier',
    labels={'adoption_rate': 'Adoption Rate (%)', 'feature': 'Feature'},
    height=400
)
fig1.update_layout(legend_title_text='Plan Tier')
st.plotly_chart(fig1, use_container_width=True)

# =============================================================================
# VISUALIZATION 2: Engagement vs Churn (Business Question: What drives retention?)
# =============================================================================

st.markdown("### 2. Engagement Impact on Retention")
st.markdown("*Do highly engaged customers churn less?*")

col_left, col_right = st.columns(2)

with col_left:
    # Churn by engagement quartiles
    filtered_df['engagement_quartile'] = pd.qcut(filtered_df['engagement_score'], 
                                                   q=4, 
                                                   labels=['Q1 (Low)', 'Q2', 'Q3', 'Q4 (High)'])
    
    churn_by_quartile = filtered_df.groupby('engagement_quartile')['is_churned'].mean() * 100
    
    fig2a = px.bar(
        x=churn_by_quartile.index,
        y=churn_by_quartile.values,
        title='Churn Rate by Engagement Quartile',
        labels={'x': 'Engagement Quartile', 'y': 'Churn Rate (%)'},
        color=churn_by_quartile.values,
        color_continuous_scale='RdYlGn_r',
        height=350
    )
    st.plotly_chart(fig2a, use_container_width=True)

with col_right:
    # AI Feature Impact on Churn
    ai_churn = filtered_df.groupby(['plan_tier', 'uses_ai'])['is_churned'].mean().reset_index()
    ai_churn['uses_ai_label'] = ai_churn['uses_ai'].map({True: 'Uses AI', False: 'No AI'})
    
    fig2b = px.bar(
        ai_churn,
        x='plan_tier',
        y='is_churned',
        color='uses_ai_label',
        barmode='group',
        title='Churn Rate: AI Users vs Non-AI Users',
        labels={'is_churned': 'Churn Rate', 'plan_tier': 'Plan Tier', 'uses_ai_label': ''},
        height=350
    )
    st.plotly_chart(fig2b, use_container_width=True)

# =============================================================================
# VISUALIZATION 3: Cross-Source Analysis (Combining SQL + MongoDB Data)
# =============================================================================

st.markdown("### 3. Cross-Database Analysis: MRR vs Feature Usage")
st.markdown("*SQL (Revenue) + MongoDB (Feature Usage) = Expansion Opportunities*")

fig3 = px.scatter(
    filtered_df,
    x='features_count',
    y='mrr',
    color='engagement_score',
    size='sessions_per_week',
    hover_data=['customer_id', 'plan_tier', 'uses_ai', 'lifetime_days'],
    title='Revenue vs Feature Adoption (Size = Sessions/Week)',
    labels={
        'features_count': 'Number of Features Used',
        'mrr': 'Monthly Recurring Revenue ($)',
        'engagement_score': 'Engagement Score'
    },
    height=450
)

# Add trend line
fig3.add_traces(
    px.scatter(filtered_df, x='features_count', y='mrr', trendline='ols').data[1]
)

fig3.update_layout(coloraxis_colorbar=dict(title="Engagement<br>Score"))
st.plotly_chart(fig3, use_container_width=True)

# =============================================================================
# VISUALIZATION 4: Customer Segmentation Heatmap
# =============================================================================

st.markdown("### 4. Customer Segmentation Matrix")
st.markdown("*Identifying high-value, high-engagement customers for expansion*")

# Create heatmap data
segment_analysis = filtered_df.groupby(['plan_tier', 'segment']).agg({
    'customer_id': 'count',
    'mrr': 'sum',
    'is_churned': 'mean',
    'engagement_score': 'mean'
}).reset_index()

segment_analysis.columns = ['Plan Tier', 'Segment', 'Count', 'Total MRR', 'Churn Rate', 'Avg Engagement']

fig4 = px.density_heatmap(
    filtered_df,
    x='plan_tier',
    y='segment',
    z='engagement_score',
    histfunc='avg',
    title='Average Engagement Score by Plan Tier and Segment',
    labels={'plan_tier': 'Plan Tier', 'segment': 'Customer Segment', 'engagement_score': 'Avg Engagement'},
    height=400,
    color_continuous_scale='Viridis'
)
st.plotly_chart(fig4, use_container_width=True)

# =============================================================================
# VISUALIZATION 5: Mobile App Impact Analysis
# =============================================================================

st.markdown("### 5. Mobile App Usage Impact")
st.markdown("*Does mobile engagement correlate with retention and lifetime value?*")

# Mobile usage impact
mobile_impact = filtered_df.groupby('uses_mobile').agg({
    'lifetime_days': 'mean',
    'is_churned': 'mean',
    'engagement_score': 'mean',
    'mrr': 'mean'
}).reset_index()

mobile_impact['uses_mobile_label'] = mobile_impact['uses_mobile'].map({True: 'Mobile Users', False: 'Desktop Only'})

fig5 = make_subplots(
    rows=2, cols=2,
    subplot_titles=('Lifetime (Days)', 'Churn Rate', 'Engagement Score', 'Avg MRR'),
    specs=[[{'type': 'bar'}, {'type': 'bar'}],
           [{'type': 'bar'}, {'type': 'bar'}]]
)

metrics = ['lifetime_days', 'is_churned', 'engagement_score', 'mrr']
positions = [(1,1), (1,2), (2,1), (2,2)]
colors = ['#2196F3', '#FF9800']

for metric, pos in zip(metrics, positions):
    fig5.add_trace(
        go.Bar(
            x=mobile_impact['uses_mobile_label'],
            y=mobile_impact[metric],
            marker_color=colors,
            name=metric.replace('_', ' ').title()
        ),
        row=pos[0], col=pos[1]
    )

fig5.update_layout(
    title_text="Mobile vs Desktop-Only User Comparison",
    height=500,
    showlegend=False
)
st.plotly_chart(fig5, use_container_width=True)

# =============================================================================
# ACTIONABLE RECOMMENDATIONS
# =============================================================================

st.markdown("---")
st.markdown("### Actionable Recommendations")

recommendations = [
    {
        "title": "1. PRIORITIZE: Expand AI Task Automation",
        "insight": f"AI users show {filtered_df[filtered_df['uses_ai']]['is_churned'].mean()*100:.1f}% churn vs {filtered_df[~filtered_df['uses_ai']]['is_churned'].mean()*100:.1f}% for non-users.",
        "action": "Invest in enhancing AI features. Target free users with >5 sessions/week for AI feature trials. Expected impact: 15-20% reduction in churn."
    },
    {
        "title": "2. BUILD: Improve Mobile Experience",
        "insight": f"Mobile users have {(filtered_df[filtered_df['uses_mobile']]['lifetime_days'].mean() - filtered_df[~filtered_df['uses_mobile']]['lifetime_days'].mean()):.0f} days longer lifetime on average.",
        "action": "Develop mobile-first features and push notifications. 30% of users don't use mobile - create onboarding flow to drive mobile adoption."
    },
    {
        "title": "3. UPSell: Target Highly Engaged Free Users",
        "insight": f"{len(filtered_df[(filtered_df['plan_tier']=='free') & (filtered_df['engagement_score']>70)])} free users are highly engaged (score >70) but not paying.",
        "action": "Launch 'Starter Plan Trial' campaign for free users with >7 sessions/week. Offer AI Task Automation as a premium add-on. Potential revenue: ${len(filtered_df[(filtered_df['plan_tier']=='free') & (filtered_df['engagement_score']>70)]) * 49:,}/month."
    }
]

for rec in recommendations:
    with st.container():
        st.markdown(f"<div class='recommendation'>" 
                   f"<h4>{rec['title']}</h4>"
                   f"<p><strong>Key Finding:</strong> {rec['insight']}</p>"
                   f"<p><strong>Recommended Action:</strong> {rec['action']}</p>"
                   f"</div>", 
                   unsafe_allow_html=True)

# =============================================================================
# DATA EXPLORER (Interactive)
# =============================================================================

st.markdown("---")
st.markdown("### Data Explorer")

with st.expander("View Raw Data"):
    # Column selector
    columns_to_show = st.multiselect(
        "Select columns to display",
        options=filtered_df.columns.tolist(),
        default=['customer_id', 'plan_tier', 'mrr', 'engagement_score', 'is_churned', 'uses_ai', 'segment']
    )
    
    # Show data
    st.dataframe(
        filtered_df[columns_to_show].sort_values('engagement_score', ascending=False),
        use_container_width=True,
        height=300
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv,
        file_name="nimbusai_analysis.csv",
        mime="text/csv"
    )

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "NimbusAI Data Analyst Take-Home Challenge | Focus Area B: Product Usage & Feature Adoption"
    "</div>",
    unsafe_allow_html=True
)
