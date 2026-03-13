"""
Synthetic MongoDB Data Generator for NimbusAI (nimbus_events database)
Generates user activity logs, feature usage, sessions, clickstream, and NPS data.
"""

import random
import uuid
from datetime import datetime, timedelta
import json

# Configuration
NUM_USERS = 1200
NUM_EVENTS = 50000

# Seed for reproducibility
random.seed(42)

# Features available in the platform
FEATURES = [
    "ai_task_automation", "team_collaboration", "time_tracking", "reporting_dashboard",
    "api_access", "advanced_security", "custom_integrations", "priority_support"
]

ONBOARDING_STEPS = ["signup", "first_login", "workspace_created", "first_project", "invited_teammate"]

# Customer IDs from PostgreSQL data (will match)
def generate_customer_ids(n):
    return [f"cust_{str(i+1).zfill(5)}" for i in range(n)]

def random_timestamp(start, end):
    """Generate random timestamp between start and end"""
    delta = end - start
    random_delta = timedelta(seconds=random.randint(0, int(delta.total_seconds())))
    return start + random_delta

def generate_events(customer_ids):
    """Generate MongoDB events collection"""
    events = []
    now = datetime.now()
    six_months_ago = now - timedelta(days=180)
    
    # Plan tier distribution (matches PostgreSQL data)
    plan_weights = {"free": 0.30, "starter": 0.35, "pro": 0.25, "enterprise": 0.10}
    
    for _ in range(NUM_EVENTS):
        customer_id = random.choice(customer_ids)
        
        # Determine plan tier based on weights
        plan_tier = random.choices(list(plan_weights.keys()), weights=list(plan_weights.values()))[0]
        
        # Event timestamp (weighted towards more recent)
        event_time = random_timestamp(six_months_ago, now)
        
        # Event types
        event_type = random.choice([
            "session_start", "session_end", "feature_usage", "page_view", 
            "onboarding_step", "nps_response", "login", "logout"
        ])
        
        event = {
            "_id": str(uuid.uuid4()),
            "customer_id": customer_id,
            "event_type": event_type,
            "timestamp": event_time.isoformat(),
            "plan_tier": plan_tier,
            "metadata": {}
        }
        
        # Add event-specific data
        if event_type == "feature_usage":
            feature = random.choice(FEATURES)
            event["feature"] = feature
            event["metadata"] = {
                "duration_seconds": random.randint(30, 3600),
                "actions_count": random.randint(1, 50),
                "context": random.choice(["desktop", "mobile", "web"])
            }
            
        elif event_type in ["session_start", "session_end"]:
            session_duration = random.randint(60, 7200)  # 1 min to 2 hours
            event["session_id"] = str(uuid.uuid4())[:8]
            event["metadata"] = {
                "duration_seconds": session_duration if event_type == "session_end" else None,
                "device": random.choice(["desktop", "mobile", "tablet"]),
                "browser": random.choice(["chrome", "safari", "firefox", "edge"]),
                "os": random.choice(["windows", "macos", "ios", "android", "linux"])
            }
            
        elif event_type == "page_view":
            event["metadata"] = {
                "page": random.choice(["/dashboard", "/projects", "/analytics", "/settings", "/team", "/integrations"]),
                "referrer": random.choice(["direct", "google", "email", "social", None]),
                "time_on_page_seconds": random.randint(10, 600)
            }
            
        elif event_type == "onboarding_step":
            step = random.choice(ONBOARDING_STEPS)
            step_index = ONBOARDING_STEPS.index(step)
            event["step"] = step
            event["step_order"] = step_index + 1
            event["metadata"] = {
                "completed": random.random() > 0.1,  # 90% completion rate
                "time_since_previous_step_minutes": random.randint(1, 1440) if step_index > 0 else 0
            }
            
        elif event_type == "nps_response":
            # NPS score (0-10)
            # Higher tiers tend to give higher scores
            base_score = {"free": 6, "starter": 7, "pro": 8, "enterprise": 8}
            score = min(10, max(0, base_score[plan_tier] + random.randint(-2, 2)))
            event["metadata"] = {
                "nps_score": score,
                "category": "promoter" if score >= 9 else "passive" if score >= 7 else "detractor"
            }
            
        elif event_type == "login":
            event["metadata"] = {
                "login_method": random.choice(["email_password", "sso", "google_oauth", "github_oauth"]),
                "mfa_used": random.random() > 0.7 if plan_tier in ["pro", "enterprise"] else False
            }
        
        events.append(event)
    
    return events

def generate_user_profiles(customer_ids):
    """Generate user profile documents with aggregated stats"""
    profiles = []
    now = datetime.now()
    
    for customer_id in customer_ids:
        plan_tier = random.choice(["free", "starter", "pro", "enterprise"])
        
        # Engagement score calculation
        # Based on: sessions per week, features used, days since last login
        sessions_per_week = random.choices(
            [0, 1, 2, 3, 5, 10, 20], 
            weights=[5, 10, 20, 25, 20, 15, 5]
        )[0]
        
        # Calculate engagement score (0-100)
        # - Sessions per week (max 40 points)
        # - Features diversity (max 30 points)  
        # - NPS category (max 30 points)
        session_score = min(40, sessions_per_week * 4)
        features_used = random.randint(1, len(FEATURES))
        feature_score = min(30, features_used * 4)
        nps_score = random.choice([10, 20, 30])  # Simplified
        
        engagement_score = session_score + feature_score + nps_score
        
        profile = {
            "_id": customer_id,
            "customer_id": customer_id,
            "plan_tier": plan_tier,
            "created_at": (now - timedelta(days=random.randint(30, 730))).isoformat(),
            "last_active_at": (now - timedelta(days=random.randint(0, 30))).isoformat(),
            "engagement_metrics": {
                "total_sessions": random.randint(10, 1000),
                "sessions_per_week_30d": sessions_per_week,
                "avg_session_duration_seconds": random.randint(300, 3600),
                "features_used_count": features_used,
                "features_used_list": random.sample(FEATURES, features_used),
                "nps_last_score": random.randint(0, 10) if random.random() > 0.3 else None
            },
            "engagement_score": engagement_score,
            "segment": "highly_engaged" if engagement_score >= 70 else "moderately_engaged" if engagement_score >= 40 else "at_risk"
        }
        
        profiles.append(profile)
    
    return profiles

if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    
    customer_ids = generate_customer_ids(NUM_USERS)
    
    # Generate events
    events = generate_events(customer_ids)
    
    # Generate user profiles  
    profiles = generate_user_profiles(customer_ids)
    
    # Save as JSONL (one document per line for mongoimport)
    with open("data/nimbus_events.json", "w") as f:
        # Combine events and profiles with a type field
        for event in events:
            event["doc_type"] = "event"
            f.write(json.dumps(event) + "\n")
        
        for profile in profiles:
            profile["doc_type"] = "user_profile"
            f.write(json.dumps(profile) + "\n")
    
    print(f"MongoDB data generated: data/nimbus_events.json")
    print(f"  - Events: {NUM_EVENTS}")
    print(f"  - User Profiles: {NUM_USERS}")
    print(f"  - Total documents: {NUM_EVENTS + NUM_USERS}")
