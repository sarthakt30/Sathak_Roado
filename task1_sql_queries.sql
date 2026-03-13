-- SQL Queries for NimbusAI Take-Home
-- Focus: Product Usage & Feature Adoption (Option B)
-- Author: Data Analyst Intern Candidate

-- I structured these to answer the core business questions:
-- 1. What's our revenue/ticket situation by plan?
-- 2. Who are our best customers?
-- 3. Why are people downgrading?
-- 4. How is churn trending?
-- 5. Do we have duplicate accounts?

-- ============================================================================
-- Q1: Plan performance metrics (active customers, MRR, ticket rate)
-- This one's a bit complex because we need to handle subscriptions that span
-- multiple months - used a series generator to create month boundaries
-- ============================================================================

with active_subs as (
    select 
        s.subscription_id,
        s.customer_id,
        s.plan_tier,
        s.mrr,
        -- effective period for this analysis
        greatest(s.started_at, current_date - interval '6 months') as start_dt,
        least(coalesce(s.churned_at, current_date), current_date) as end_dt
    from subscriptions s
    where s.started_at <= current_date 
      and (s.churned_at is null or s.churned_at >= current_date - interval '6 months')
),
month_range as (
    -- grab last 6 months
    select generate_series(
        date_trunc('month', current_date - interval '5 months'),
        date_trunc('month', current_date),
        interval '1 month'
    ) as month_start
),
sub_month_activity as (
    -- cross join to explode subscriptions across months
    select 
        a.subscription_id,
        a.customer_id,
        a.plan_tier,
        a.mrr,
        m.month_start
    from active_subs a
    cross join month_range m
    where a.start_dt <= m.month_start + interval '1 month'
      and a.end_dt >= m.month_start
),
tickets_by_month as (
    select 
        customer_id,
        date_trunc('month', created_at) as ticket_month,
        count(*) as ticket_cnt
    from support_tickets
    where created_at >= current_date - interval '6 months'
    group by 1, 2
)
select 
    sm.plan_tier,
    sm.month_start::date as month,
    count(distinct sm.customer_id) as active_customers,
    round(avg(sm.mrr), 2) as avg_mrr,
    round(
        coalesce(sum(coalesce(t.ticket_cnt, 0))::numeric / nullif(count(distinct sm.customer_id), 0), 0),
        2
    ) as tickets_per_customer
from sub_month_activity sm
left join tickets_by_month t 
    on sm.customer_id = t.customer_id and sm.month_start = t.ticket_month
group by 1, 2
order by 1, 2;


-- ============================================================================
-- Q2: Customer LTV ranking with tier comparison
-- Used window functions here to avoid self-joins - much cleaner
-- ============================================================================

with customer_ltv as (
    select 
        c.customer_id,
        c.email,
        c.company_name,
        s.plan_tier,
        sum(i.amount) as total_ltv,
        count(i.invoice_id) as invoice_count,
        min(i.created_at) as first_payment,
        max(i.created_at) as last_payment
    from customers c
    join subscriptions s on c.customer_id = s.customer_id
    join invoices i on s.subscription_id = i.subscription_id
    where i.status = 'paid'
    group by 1, 2, 3, 4
),
ranked as (
    select 
        customer_id,
        email,
        company_name,
        plan_tier,
        total_ltv,
        invoice_count,
        -- rank within tier
        rank() over (partition by plan_tier order by total_ltv desc) as tier_rank,
        -- percentile is handy for bucketing
        percent_rank() over (partition by plan_tier order by total_ltv) as percentile,
        -- tier avg for comparison
        avg(total_ltv) over (partition by plan_tier) as tier_avg,
        -- for market share calc
        sum(total_ltv) over (partition by plan_tier) as tier_total
    from customer_ltv
)
select 
    customer_id,
    email,
    company_name,
    plan_tier,
    total_ltv,
    tier_rank,
    round((percentile * 100)::numeric, 1) as percentile,
    round(((total_ltv - tier_avg) / tier_avg * 100)::numeric, 2) as pct_diff_from_avg,
    round((total_ltv / tier_total * 100)::numeric, 2) as pct_of_tier_revenue
from ranked
order by plan_tier, tier_rank;


-- ============================================================================
-- Q3: Downgrade analysis - correlation with support tickets
-- This is for the VP who wants to know if support issues cause downgrades
-- ============================================================================

with downgrades as (
    select 
        s.customer_id,
        s.subscription_id,
        s.plan_tier as current_plan,
        s.started_at as downgrade_date,
        s.mrr as current_mrr,
        -- get previous plan from lag (assuming subscription history pattern)
        lag(s.plan_tier) over (partition by s.customer_id order by s.started_at) as prev_plan,
        lag(s.mrr) over (partition by s.customer_id order by s.started_at) as prev_mrr
    from subscriptions s
    where s.downgraded = true
      and s.started_at >= current_date - interval '90 days'
),
pre_downgrade_tickets as (
    select 
        d.customer_id,
        d.subscription_id,
        d.current_plan,
        d.prev_plan,
        d.downgrade_date,
        d.current_mrr,
        d.prev_mrr,
        count(t.ticket_id) as tickets_30d_before,
        count(case when t.priority = 'high' then 1 end) as high_prio_tickets
    from downgrades d
    left join support_tickets t 
        on d.customer_id = t.customer_id
        and t.created_at >= d.downgrade_date - interval '30 days'
        and t.created_at < d.downgrade_date
    group by 1, 2, 3, 4, 5, 6, 7
)
select 
    p.customer_id,
    c.email,
    c.company_name,
    p.prev_plan,
    p.current_plan,
    p.downgrade_date::date,
    p.prev_mrr,
    p.current_mrr,
    (p.prev_mrr - p.current_mrr) as mrr_lost,
    p.tickets_30d_before,
    p.high_prio_tickets,
    round((p.tickets_30d_before::numeric / 30 * 7), 2) as tickets_per_week,
    case 
        when p.tickets_30d_before >= 5 then 'Critical Risk'
        when p.tickets_30d_before >= 4 then 'High Risk'
        when p.high_prio_tickets >= 2 then 'Medium Risk'
        else 'Low Risk'
    end as risk_flag
from pre_downgrade_tickets p
join customers c on p.customer_id = c.customer_id
where p.tickets_30d_before > 3
order by p.tickets_30d_before desc, mrr_lost desc;


-- ============================================================================
-- Q4: Churn trends and MoM growth
-- Rolling averages help smooth out noise in monthly churn rates
-- ============================================================================

with monthly_new as (
    select 
        plan_tier,
        date_trunc('month', started_at) as month,
        count(*) as new_subs
    from subscriptions
    group by 1, 2
),
monthly_churned as (
    select 
        plan_tier,
        date_trunc('month', churned_at) as month,
        count(*) as churned_subs
    from subscriptions
    where churned_at is not null
    group by 1, 2
),
monthly_active_base as (
    select 
        plan_tier,
        date_trunc('month', d) as month,
        count(case when started_at <= d and (churned_at is null or churned_at > d) then 1 end) as active_count
    from subscriptions
    cross join generate_series(
        (select min(date_trunc('month', started_at)) from subscriptions),
        current_date,
        interval '1 month'
    ) as d
    group by 1, 2
),
combined as (
    select 
        coalesce(n.plan_tier, c.plan_tier, a.plan_tier) as plan_tier,
        coalesce(n.month, c.month, a.month) as month,
        coalesce(n.new_subs, 0) as new_subs,
        coalesce(c.churned_subs, 0) as churned_subs,
        coalesce(a.active_count, 0) as active_end_month
    from monthly_new n
    full outer join monthly_churned c on n.plan_tier = c.plan_tier and n.month = c.month
    full outer join monthly_active_base a on coalesce(n.plan_tier, c.plan_tier) = a.plan_tier 
        and coalesce(n.month, c.month) = a.month
),
with_calcs as (
    select 
        plan_tier,
        month::date,
        new_subs,
        churned_subs,
        active_end_month,
        -- MoM growth
        lag(new_subs) over (partition by plan_tier order by month) as last_month_new,
        case when lag(new_subs) over (partition by plan_tier order by month) > 0 
            then round(((new_subs - lag(new_subs) over (partition by plan_tier order by month)) 
                 / lag(new_subs) over (partition by plan_tier order by month)::numeric * 100), 2)
            else null 
        end as mom_growth_pct,
        -- Churn rate
        case when active_end_month + churned_subs > 0 
            then round((churned_subs::numeric / (active_end_month + churned_subs) * 100), 2)
            else 0 
        end as churn_rate_pct,
        -- Rolling 3mo avg
        avg(case when active_end_month + churned_subs > 0 
            then (churned_subs::numeric / (active_end_month + churned_subs) * 100) 
            else 0 end) over (
            partition by plan_tier 
            order by month 
            rows between 2 preceding and current row
        ) as rolling_3m_avg
    from combined
    where month is not null
)
select 
    plan_tier,
    month,
    new_subs,
    coalesce(mom_growth_pct, 0) as mom_growth_pct,
    churned_subs,
    round(churn_rate_pct, 2) as churn_rate_pct,
    round(rolling_3m_avg, 2) as rolling_3m_avg_churn,
    case 
        when churn_rate_pct > 2 * rolling_3m_avg and rolling_3m_avg > 0 
        then '⚠️ SPIKE'
        else 'OK'
    end as alert
from with_calcs
order by 1, 2;


-- ============================================================================
-- Q5: Duplicate account detection
-- This gets messy - we look at email domains, name similarity, overlapping subs
-- Real world: you'd probably use a proper fuzzy matching library
-- ============================================================================

with domains as (
    select 
        customer_id,
        email,
        lower(substring(email from position('@' in email) + 1)) as domain,
        lower(company_name) as company_name,
        created_at
    from customers
    where email is not null
),
-- same domain matches (exclude big email providers)
same_domain as (
    select 
        d1.customer_id as id1,
        d2.customer_id as id2,
        d1.email as email1,
        d2.email as email2,
        d1.domain,
        d1.company_name as name1,
        d2.company_name as name2,
        'Same Domain' as match_type,
        case 
            when d1.company_name = d2.company_name then 100
            when d1.company_name like '%' || d2.company_name || '%' then 80
            when d2.company_name like '%' || d1.company_name || '%' then 80
            else 50
        end as score
    from domains d1
    join domains d2 on d1.domain = d2.domain and d1.customer_id < d2.customer_id
    where d1.domain not in ('gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com')
),
-- similar names, different domains (possible typos/variants)
name_sim as (
    select 
        c1.customer_id as id1,
        c2.customer_id as id2,
        c1.email as email1,
        c2.email as email2,
        lower(substring(c1.email from position('@' in c1.email) + 1)) as domain1,
        lower(substring(c2.email from position('@' in c2.email) + 1)) as domain2,
        lower(c1.company_name) as name1,
        lower(c2.company_name) as name2,
        'Name Similarity' as match_type,
        case 
            when regexp_replace(lower(c1.company_name), '[^a-z0-9]', '', 'g') = 
                 regexp_replace(lower(c2.company_name), '[^a-z0-9]', '', 'g') then 95
            when c1.company_name like '%' || c2.company_name || '%' then 85
            when c2.company_name like '%' || c1.company_name || '%' then 85
            when split_part(lower(c1.company_name), ' ', 1) = split_part(lower(c2.company_name), ' ', 1) then 70
            else 40
        end as score
    from customers c1
    join customers c2 on c1.customer_id < c2.customer_id
    where c1.email is not null and c2.email is not null
      and (c1.company_name like '%' || c2.company_name || '%'
           or c2.company_name like '%' || c1.company_name || '%'
           or split_part(lower(c1.company_name), ' ', 1) = split_part(lower(c2.company_name), ' ', 1))
      and lower(substring(c1.email from position('@' in c1.email) + 1)) != 
          lower(substring(c2.email from position('@' in c2.email) + 1))
),
-- overlapping active periods (potential account sharing)
overlap as (
    select 
        s1.customer_id as id1,
        s2.customer_id as id2,
        c1.email as email1,
        c2.email as email2,
        'Overlapping Subs' as match_type,
        60 as score
    from subscriptions s1
    join subscriptions s2 on s1.customer_id < s2.customer_id
    join customers c1 on s1.customer_id = c1.customer_id
    join customers c2 on s2.customer_id = c2.customer_id
    where s1.started_at <= coalesce(s2.churned_at, current_date)
      and s2.started_at <= coalesce(s1.churned_at, current_date)
),
all_matches as (
    select * from same_domain
    union select * from name_sim
    union select id1, id2, email1, email2, null, null, null, null, match_type, score from overlap
),
best_matches as (
    select distinct on (id1, id2)
        id1 as customer_id_1,
        id2 as customer_id_2,
        email1,
        email2,
        domain,
        name1 as company_name_1,
        name2 as company_name_2,
        match_type,
        score as similarity_score
    from all_matches
    order by id1, id2, score desc
)
select 
    b.customer_id_1,
    b.customer_id_2,
    b.email1,
    b.email2,
    b.domain,
    b.company_name_1,
    b.company_name_2,
    b.match_type,
    b.similarity_score,
    s1.plan_tier as plan_1,
    s2.plan_tier as plan_2,
    case 
        when b.similarity_score >= 90 then 'HIGH - Review now'
        when b.similarity_score >= 70 then 'MEDIUM - Investigate'
        else 'LOW - Weak match'
    end as priority
from best_matches b
left join subscriptions s1 on b.customer_id_1 = s1.customer_id
left join subscriptions s2 on b.customer_id_2 = s2.customer_id
where b.similarity_score >= 60
order by b.similarity_score desc;


-- ============================================================================
-- Bonus: Quick feature adoption check for Option B
-- ============================================================================

select 
    s.plan_tier,
    jsonb_array_elements_text(s.enabled_features) as feature,
    count(*) as customers_with_feature,
    round(count(*)::numeric / sum(count(*)) over (partition by s.plan_tier) * 100, 1) as adoption_pct
from subscriptions s
where s.status = 'active'
group by 1, 2
order by 1, 3 desc;
