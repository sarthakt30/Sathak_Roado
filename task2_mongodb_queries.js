// MongoDB Aggregation Pipelines for NimbusAI
// Option B: Product Usage & Feature Adoption
// Using MongoDB shell syntax - tested on v6.0

// Q1: Sessions per week with percentile analysis
// Wanted to show distribution, not just averages - hence the p25/p50/p75

// Approach 1: Using pre-computed user_profiles (if available)
// This is cleaner since the data is already aggregated
db.user_profiles.aggregate([
    {
        $project: {
            customer_id: 1,
            plan_tier: 1,
            sessions_per_week: "$engagement_metrics.sessions_per_week_30d",
            avg_session_duration: "$engagement_metrics.avg_session_duration_seconds"
        }
    },
    {
        $group: {
            _id: "$plan_tier",
            avg_sessions_per_week: { $avg: "$sessions_per_week" },
            avg_session_duration: { $avg: "$avg_session_duration" },
            users_count: { $sum: 1 },
            durations: { $push: "$avg_session_duration" }
        }
    },
    // Calculate percentiles using array indexing
    {
        $project: {
            plan_tier: "$_id",
            avg_sessions_per_week: { $round: ["$avg_sessions_per_week", 2] },
            avg_session_duration: { $round: ["$avg_session_duration", 0] },
            users_count: 1,
            durations_sorted: { $sortArray: { input: "$durations", sortBy: 1 } }
        }
    },
    {
        $project: {
            plan_tier: 1,
            avg_sessions_per_week: 1,
            avg_session_duration: 1,
            users_count: 1,
            p25_duration: {
                $arrayElemAt: [
                    "$durations_sorted",
                    { $floor: { $multiply: [{ $subtract: [{ $size: "$durations_sorted" }, 1] }, 0.25] } }
                ]
            },
            p50_duration: {
                $arrayElemAt: [
                    "$durations_sorted",
                    { $floor: { $multiply: [{ $subtract: [{ $size: "$durations_sorted" }, 1] }, 0.50] } }
                ]
            },
            p75_duration: {
                $arrayElemAt: [
                    "$durations_sorted",
                    { $floor: { $multiply: [{ $subtract: [{ $size: "$durations_sorted" }, 1] }, 0.75] } }
                ]
            }
        }
    },
    {
        $project: {
            plan_tier: 1,
            avg_sessions_per_user_per_week: "$avg_sessions_per_week",
            user_count: "$users_count",
            p25_session_duration_minutes: { $round: [{ $divide: ["$p25_duration", 60] }, 1] },
            p50_session_duration_minutes: { $round: [{ $divide: ["$p50_duration", 60] }, 1] },
            p75_session_duration_minutes: { $round: [{ $divide: ["$p75_duration", 60] }, 1] }
        }
    },
    { $sort: { plan_tier: 1 } }
]);


// Q2: Feature DAU and retention analysis
// This one's a bit tricky - we need to track first use vs repeat use

// First, let's get DAU by feature
db.events.aggregate([
    {
        $match: {
            event_type: "feature_usage",
            timestamp: { $gte: new Date(Date.now() - 90 * 24 * 60 * 60 * 1000) }
        }
    },
    {
        $addFields: {
            usage_date: { $dateToString: { format: "%Y-%m-%d", date: { $toDate: "$timestamp" } } }
        }
    },
    {
        $group: {
            _id: { feature: "$feature", date: "$usage_date" },
            daily_users: { $addToSet: "$customer_id" },
            event_count: { $sum: 1 }
        }
    },
    {
        $group: {
            _id: "$_id.feature",
            avg_dau: { $avg: { $size: "$daily_users" } },
            total_events: { $sum: "$event_count" },
            days_tracked: { $sum: 1 }
        }
    },
    {
        $project: {
            feature: "$_id",
            avg_dau: { $round: ["$avg_dau", 0] },
            total_events: 1,
            days_tracked: 1
        }
    },
    { $sort: { avg_dau: -1 } }
]);

// Now for 7-day retention - did they come back within a week?
db.events.aggregate([
    { $match: { event_type: "feature_usage" } },
    { $sort: { customer_id: 1, feature: 1, timestamp: 1 } },
    {
        $group: {
            _id: { customer_id: "$customer_id", feature: "$feature" },
            first_use: { $first: "$timestamp" },
            last_use: { $last: "$timestamp" },
            use_count: { $sum: 1 },
            plan_tier: { $first: "$plan_tier" }
        }
    },
    {
        $addFields: {
            days_between: {
                $divide: [
                    { $subtract: [{ $toDate: "$last_use" }, { $toDate: "$first_use" }] },
                    1000 * 60 * 60 * 24
                ]
            }
        }
    },
    {
        $addFields: {
            retained_7d: { $lte: ["$days_between", 7] },
            used_multiple: { $gte: ["$use_count", 2] }
        }
    },
    {
        $group: {
            _id: "$feature",
            total_users: { $sum: 1 },
            retained_count: { $sum: { $cond: ["$retained_7d", 1, 0] } },
            avg_uses: { $avg: "$use_count" }
        }
    },
    {
        $project: {
            feature: "$_id",
            total_users: 1,
            retention_7d_rate: {
                $round: [{ $multiply: [{ $divide: ["$retained_count", "$total_users"] }, 100] }, 2]
            },
            avg_uses_per_user: { $round: ["$avg_uses", 2] }
        }
    },
    { $sort: { retention_7d_rate: -1 } }
]);


// Q3: Onboarding funnel analysis
// signup → first_login → workspace_created → first_project → invited_teammate
// Let's build this step by step

// Step 1: Create a collection with each user's funnel progress
// (I prefer doing this in stages vs one massive pipeline)
db.events.aggregate([
    { $match: { event_type: "onboarding_step" } },
    { $sort: { customer_id: 1, step_order: 1 } },
    {
        $group: {
            _id: "$customer_id",
            plan_tier: { $first: "$plan_tier" },
            signup_at: {
                $min: { $cond: [{ $eq: ["$step", "signup"] }, { $toDate: "$timestamp" }, null] }
            },
            login_at: {
                $min: { $cond: [{ $eq: ["$step", "first_login"] }, { $toDate: "$timestamp" }, null] }
            },
            workspace_at: {
                $min: { $cond: [{ $eq: ["$step", "workspace_created"] }, { $toDate: "$timestamp" }, null] }
            },
            project_at: {
                $min: { $cond: [{ $eq: ["$step", "first_project"] }, { $toDate: "$timestamp" }, null] }
            },
            invite_at: {
                $min: { $cond: [{ $eq: ["$step", "invited_teammate"] }, { $toDate: "$timestamp" }, null] }
            }
        }
    },
    // Calculate conversion flags and time gaps
    {
        $project: {
            customer_id: "$_id",
            plan_tier: 1,
            reached_signup: { $ne: ["$signup_at", null] },
            reached_login: { $ne: ["$login_at", null] },
            reached_workspace: { $ne: ["$workspace_at", null] },
            reached_project: { $ne: ["$project_at", null] },
            reached_invite: { $ne: ["$invite_at", null] },
            // Time between steps (in minutes)
            signup_to_login_mins: {
                $cond: [
                    { $and: ["$signup_at", "$login_at"] },
                    { $divide: [{ $subtract: ["$login_at", "$signup_at"] }, 1000 * 60] },
                    null
                ]
            },
            login_to_workspace_mins: {
                $cond: [
                    { $and: ["$login_at", "$workspace_at"] },
                    { $divide: [{ $subtract: ["$workspace_at", "$login_at"] }, 1000 * 60] },
                    null
                ]
            }
        }
    },
    // Store for funnel analysis
    {
        $merge: {
            into: "funnel_analysis",
            on: "_id",
            whenMatched: "replace",
            whenNotMatched: "insert"
        }
    }
]);

// Step 2: Calculate funnel metrics
db.funnel_analysis.aggregate([
    {
        $group: {
            _id: null,
            total_signups: { $sum: { $cond: ["$reached_signup", 1, 0] } },
            reached_login: { $sum: { $cond: ["$reached_login", 1, 0] } },
            reached_workspace: { $sum: { $cond: ["$reached_workspace", 1, 0] } },
            reached_project: { $sum: { $cond: ["$reached_project", 1, 0] } },
            reached_invite: { $sum: { $cond: ["$reached_invite", 1, 0] } },
            // Collect times for median calc
            signup_to_login_times: { $push: "$signup_to_login_mins" }
        }
    },
    {
        $project: {
            funnel: {
                signup: {
                    count: "$total_signups",
                    drop_off: 0,
                    conversion_rate: 100
                },
                first_login: {
                    count: "$reached_login",
                    drop_off: { $subtract: ["$total_signups", "$reached_login"] },
                    conversion_rate: {
                        $round: [{ $multiply: [{ $divide: ["$reached_login", "$total_signups"] }, 100] }, 1]
                    }
                },
                workspace_created: {
                    count: "$reached_workspace",
                    drop_off: { $subtract: ["$reached_login", "$reached_workspace"] },
                    conversion_from_prev: {
                        $round: [{ $multiply: [{ $divide: ["$reached_workspace", "$reached_login"] }, 100] }, 1]
                    }
                },
                first_project: {
                    count: "$reached_project",
                    drop_off: { $subtract: ["$reached_workspace", "$reached_project"] },
                    conversion_from_prev: {
                        $round: [{ $multiply: [{ $divide: ["$reached_project", "$reached_workspace"] }, 100] }, 1]
                    }
                },
                invited_teammate: {
                    count: "$reached_invite",
                    drop_off: { $subtract: ["$reached_project", "$reached_invite"] },
                    conversion_from_prev: {
                        $round: [{ $multiply: [{ $divide: ["$reached_invite", "$reached_project"] }, 100] }, 1]
                    }
                }
            },
            // Note: median calc would need $function or app-side processing
            time_samples: "$signup_to_login_times"
        }
    }
]);


// Q4: Cross-reference with SQL data - find top engaged free users
// These are our upsell targets

// My engagement scoring approach:
// 40% sessions per week (frequency)
// 30% feature diversity (depth)
// 20% session duration (intensity)
// 10% recency (currency)
// Total 0-100 scale

db.user_profiles.aggregate([
    { $match: { plan_tier: "free" } },
    // Calculate days since last active
    {
        $addFields: {
            days_since_active: {
                $divide: [
                    { $subtract: [new Date(), { $toDate: "$last_active_at" }] },
                    1000 * 60 * 60 * 24
                ]
            }
        }
    },
    // Score components (capped at max)
    {
        $addFields: {
            session_score: {
                $min: [{ $multiply: ["$engagement_metrics.sessions_per_week_30d", 8] }, 40]
            },
            feature_score: {
                $min: [{ $multiply: ["$engagement_metrics.features_used_count", 6] }, 30]
            },
            duration_score: {
                $min: [{ $divide: ["$engagement_metrics.avg_session_duration_seconds", 180] }, 20]
            },
            recency_score: {
                $max: [0, { $subtract: [10, { $divide: ["$days_since_active", 3] }] }]
            }
        }
    },
    // Total score
    {
        $addFields: {
            engagement_score: {
                $add: ["$session_score", "$feature_score", "$duration_score", "$recency_score"]
            }
        }
    },
    { $sort: { engagement_score: -1 } },
    { $limit: 20 },
    {
        $project: {
            customer_id: 1,
            engagement_score: { $round: ["$engagement_score", 1] },
            metrics: {
                sessions_per_week: "$engagement_metrics.sessions_per_week_30d",
                features_used: "$engagement_metrics.features_used_count",
                avg_session_minutes: { $round: [{ $divide: ["$engagement_metrics.avg_session_duration_seconds", 60] }, 1] }
            },
            days_since_active: { $round: ["$days_since_active", 0] },
            // Priority flag
            upsell_priority: {
                $switch: {
                    branches: [
                        { case: { $gte: ["$engagement_score", 80] }, then: "HIGH" },
                        { case: { $gte: ["$engagement_score", 60] }, then: "MEDIUM" }
                    ],
                    default: "LOW"
                }
            },
            // Suggested tier based on usage
            suggested_tier: {
                $switch: {
                    branches: [
                        { case: { $gte: ["$engagement_metrics.features_used_count", 5] }, then: "pro" },
                        { case: { $gte: ["$engagement_metrics.features_used_count", 3] }, then: "starter" }
                    ],
                    default: "starter"
                }
            }
        }
    }
]);

// Alternative: Calculate from raw events (if user_profiles doesn't exist)
// This is slower but doesn't require pre-aggregation
db.events.aggregate([
    { $match: { plan_tier: "free" } },
    {
        $group: {
            _id: "$customer_id",
            event_count: { $sum: 1 },
            sessions: { $sum: { $cond: [{ $eq: ["$event_type", "session_start"] }, 1, 0] } },
            features: { $addToSet: "$feature" },
            days: { $addToSet: { $substr: ["$timestamp", 0, 10] } },
            first_at: { $min: { $toDate: "$timestamp" } },
            last_at: { $max: { $toDate: "$timestamp" } },
            avg_duration: { $avg: "$metadata.duration_seconds" }
        }
    },
    {
        $project: {
            customer_id: "$_id",
            total_events: "$event_count",
            session_count: "$sessions",
            feature_count: { $size: "$features" },
            active_days: { $size: "$days" },
            avg_duration: { $ifNull: ["$avg_duration", 0] },
            // Scores
            freq_score: { $min: [{ $multiply: [{ $size: "$days" }, 4] }, 40] },
            depth_score: { $min: [{ $multiply: [{ $size: "$features" }, 7.5] }, 30] },
            dur_score: { $min: [{ $divide: [{ $ifNull: ["$avg_duration", 0] }, 180] }, 20] }
        }
    },
    {
        $addFields: {
            engagement_score: { $add: ["$freq_score", "$depth_score", "$dur_score"] }
        }
    },
    { $sort: { engagement_score: -1 } },
    { $limit: 20 },
    {
        $project: {
            customer_id: 1,
            engagement_score: { $round: ["$engagement_score", 1] },
            metrics: {
                events: "$total_events",
                sessions: "$session_count",
                features: "$feature_count",
                active_days: "$active_days"
            },
            priority: {
                $cond: [
                    { $gte: ["$engagement_score", 75] },
                    "HIGH - Immediate outreach",
                    { $cond: [{ $gte: ["$engagement_score", 55] }, "MEDIUM - Nurture campaign", "LOW - Monitor"] }
                ]
            }
        }
    }
]);
