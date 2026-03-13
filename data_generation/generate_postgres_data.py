"""
Synthetic PostgreSQL Data Generator for NimbusAI (nimbus_core database)
Generates realistic B2B SaaS data with intentional messiness for data wrangling practice.
"""

import random
import uuid
from datetime import datetime, timedelta
import json

# Configuration
NUM_CUSTOMERS = 1200
NUM_SUBSCRIPTION_TIERS = 4  # Free, Starter, Pro, Enterprise
NUM_FEATURES = 8

# Seed for reproducibility
random.seed(42)

# Data pools
COMPANY_DOMAINS = [
    "techcorp.com", "innovate.io", "startup.xyz", "solutions.net", "digital.dev",
    "cloudservices.com", "dataworks.io", "aiml.tech", "fintech.com", "healthplus.org",
    "retailpro.com", "manufacture.co", "consulting.biz", "agency.com", "devteam.io",
    "productlabs.com", "growth.co", "scaleup.tech", "venture.com", "enterprise.io"
]

FIRST_NAMES = ["James", "Maria", "Robert", "Jennifer", "Michael", "Linda", "William", "Patricia",
               "David", "Elizabeth", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah",
               "Charles", "Karen", "Daniel", "Nancy", "Matthew", "Lisa", "Anthony", "Betty"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
              "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas",
              "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson", "White"]

PLAN_TIERS = ["free", "starter", "pro", "enterprise"]
PLAN_PRICES = {"free": 0, "starter": 49, "pro": 199, "enterprise": 599}

FEATURES = [
    "ai_task_automation", "team_collaboration", "time_tracking", "reporting_dashboard",
    "api_access", "advanced_security", "custom_integrations", "priority_support"
]

PLAN_FEATURES = {
    "free": ["ai_task_automation", "team_collaboration"],
    "starter": ["ai_task_automation", "team_collaboration", "time_tracking", "reporting_dashboard"],
    "pro": ["ai_task_automation", "team_collaboration", "time_tracking", "reporting_dashboard", "api_access", "advanced_security"],
    "enterprise": FEATURES  # All features
}

def generate_customers():
    """Generate customers table data with intentional messiness"""
    customers = []
    used_emails = set()
    
    for i in range(NUM_CUSTOMERS):
        customer_id = f"cust_{str(i+1).zfill(5)}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        domain = random.choice(COMPANY_DOMAINS)
        
        # Introduce some messy data: duplicates, typos, nulls
        if random.random() < 0.05:  # 5% chance of duplicate-like email
            email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
            # Add duplicate with slight variation
            if email in used_emails:
                email = f"{first_name.lower()}{last_name.lower()}@{domain}"
        elif random.random() < 0.03:  # 3% null emails
            email = None
        else:
            email = f"{first_name.lower()}.{last_name.lower()}@{domain}"
        
        if email:
            used_emails.add(email)
        
        # Account creation date (past 2 years)
        created_at = datetime.now() - timedelta(days=random.randint(1, 730))
        
        # Some timezone encoding issues (intentional messiness)
        if random.random() < 0.02:
            company_name = f"Company {i+1} \xff\xfe"  # Encoding issues
        else:
            company_name = f"{first_name}'s Company" if random.random() < 0.3 else f"{domain.split('.')[0].title()} Solutions"
        
        # Messy phone numbers
        if random.random() < 0.1:
            phone = f"+1 ({random.randint(100, 999)}) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
        elif random.random() < 0.05:
            phone = "N/A"
        else:
            phone = None
        
        customers.append({
            "customer_id": customer_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "company_name": company_name,
            "phone": phone,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "timezone": random.choice(["UTC", "America/New_York", "America/Los_Angeles", "Europe/London", None])
        })
    
    return customers

def generate_subscriptions(customers):
    """Generate subscriptions with realistic patterns including churn and upgrades/downgrades"""
    subscriptions = []
    
    for cust in customers:
        customer_id = cust["customer_id"]
        created_at = datetime.strptime(cust["created_at"], "%Y-%m-%d %H:%M:%S")
        
        # Determine initial plan based on company type
        if "enterprise" in cust.get("company_name", "").lower():
            initial_plan = random.choices(PLAN_TIERS, weights=[5, 10, 30, 55])[0]
        elif "startup" in cust.get("email", "").lower():
            initial_plan = random.choices(PLAN_TIERS, weights=[40, 35, 20, 5])[0]
        else:
            initial_plan = random.choices(PLAN_TIERS, weights=[30, 35, 25, 10])[0]
        
        # Subscription history
        current_plan = initial_plan
        plan_start = created_at + timedelta(days=random.randint(1, 14))  # Trial period
        
        # 20% have upgraded
        if random.random() < 0.2 and initial_plan != "enterprise":
            # Upgrade event
            upgrade_date = plan_start + timedelta(days=random.randint(60, 180))
            current_idx = PLAN_TIERS.index(initial_plan)
            current_plan = PLAN_TIERS[min(current_idx + 1, len(PLAN_TIERS) - 1)]
            plan_start = upgrade_date
        
        # 10% have downgraded (relevant for Q3)
        downgrade_flag = False
        if random.random() < 0.1 and initial_plan != "free":
            downgrade_date = plan_start + timedelta(days=random.randint(30, 120))
            current_idx = PLAN_TIERS.index(current_plan)
            current_plan = PLAN_TIERS[max(current_idx - 1, 0)]
            plan_start = downgrade_date
            downgrade_flag = True
        
        # 15% churned
        status = "active"
        churned_at = None
        if random.random() < 0.15:
            status = "churned"
            churned_at = plan_start + timedelta(days=random.randint(30, 300))
        
        # MRR based on current plan
        mrr = PLAN_PRICES[current_plan]
        
        # Enable features based on plan
        enabled_features = PLAN_FEATURES[current_plan]
        
        subscriptions.append({
            "subscription_id": f"sub_{uuid.uuid4().hex[:12]}",
            "customer_id": customer_id,
            "plan_tier": current_plan,
            "status": status,
            "mrr": mrr,
            "started_at": plan_start.strftime("%Y-%m-%d %H:%M:%S"),
            "churned_at": churned_at.strftime("%Y-%m-%d %H:%M:%S") if churned_at else None,
            "downgraded": downgrade_flag,
            "enabled_features": json.dumps(enabled_features)
        })
    
    return subscriptions

def generate_support_tickets(customers, subscriptions):
    """Generate support tickets, especially around downgrade period"""
    tickets = []
    ticket_id = 1
    
    for sub in subscriptions:
        if not sub["downgraded"]:
            # Random tickets for non-downgraded
            num_tickets = random.choices([0, 1, 2, 3, 4], weights=[50, 25, 15, 7, 3])[0]
            for _ in range(num_tickets):
                created_at = datetime.strptime(sub["started_at"], "%Y-%m-%d %H:%M:%S") + timedelta(days=random.randint(1, 180))
                tickets.append({
                    "ticket_id": f"tck_{str(ticket_id).zfill(6)}",
                    "customer_id": sub["customer_id"],
                    "subscription_id": sub["subscription_id"],
                    "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "priority": random.choice(["low", "medium", "high"]),
                    "status": random.choice(["open", "resolved", "closed"]),
                    "category": random.choice(["billing", "technical", "feature_request", "bug"])
                })
                ticket_id += 1
        else:
            # Downgraded customers - generate tickets BEFORE downgrade (Q3 scenario)
            downgrade_date = datetime.strptime(sub["started_at"], "%Y-%m-%d %H:%M:%S")
            # Generate 4+ tickets in 30 days before downgrade
            num_tickets = random.randint(4, 7)
            for i in range(num_tickets):
                created_at = downgrade_date - timedelta(days=random.randint(1, 30))
                tickets.append({
                    "ticket_id": f"tck_{str(ticket_id).zfill(6)}",
                    "customer_id": sub["customer_id"],
                    "subscription_id": sub["subscription_id"],
                    "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "priority": random.choice(["high", "high", "medium"]),  # More high priority
                    "status": "closed",
                    "category": random.choice(["billing", "technical", "bug"])
                })
                ticket_id += 1
    
    return tickets

def generate_billing(subscriptions):
    """Generate monthly billing records"""
    invoices = []
    invoice_id = 1
    
    for sub in subscriptions:
        start_date = datetime.strptime(sub["started_at"], "%Y-%m-%d %H:%M:%S")
        
        # Generate monthly invoices
        current_date = start_date
        end_date = datetime.now() if sub["status"] == "active" else datetime.strptime(sub["churned_at"], "%Y-%m-%d %H:%M:%S")
        
        while current_date < end_date:
            amount = sub["mrr"]
            # Some payment failures (5%)
            status = "paid" if random.random() > 0.05 else "failed"
            
            invoices.append({
                "invoice_id": f"inv_{str(invoice_id).zfill(7)}",
                "customer_id": sub["customer_id"],
                "subscription_id": sub["subscription_id"],
                "billing_period_start": current_date.strftime("%Y-%m-%d"),
                "billing_period_end": (current_date + timedelta(days=30)).strftime("%Y-%m-%d"),
                "amount": amount,
                "status": status,
                "created_at": current_date.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            invoice_id += 1
            current_date += timedelta(days=30)
    
    return invoices

def generate_sql_dump():
    """Generate SQL dump file"""
    customers = generate_customers()
    subscriptions = generate_subscriptions(customers)
    tickets = generate_support_tickets(customers, subscriptions)
    invoices = generate_billing(subscriptions)
    
    sql_lines = []
    sql_lines.append("-- NimbusAI nimbus_core Database Dump")
    sql_lines.append(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    sql_lines.append("")
    
    # Create tables
    sql_lines.append("DROP TABLE IF EXISTS invoices, support_tickets, subscriptions, customers CASCADE;")
    sql_lines.append("")
    
    sql_lines.append("""CREATE TABLE customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    email VARCHAR(255),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    company_name VARCHAR(255),
    phone VARCHAR(50),
    created_at TIMESTAMP,
    timezone VARCHAR(50)
);""")
    
    sql_lines.append("""CREATE TABLE subscriptions (
    subscription_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) REFERENCES customers(customer_id),
    plan_tier VARCHAR(50),
    status VARCHAR(20),
    mrr INTEGER,
    started_at TIMESTAMP,
    churned_at TIMESTAMP,
    downgraded BOOLEAN DEFAULT FALSE,
    enabled_features JSONB
);""")
    
    sql_lines.append("""CREATE TABLE support_tickets (
    ticket_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) REFERENCES customers(customer_id),
    subscription_id VARCHAR(20) REFERENCES subscriptions(subscription_id),
    created_at TIMESTAMP,
    priority VARCHAR(20),
    status VARCHAR(20),
    category VARCHAR(50)
);""")
    
    sql_lines.append("""CREATE TABLE invoices (
    invoice_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) REFERENCES customers(customer_id),
    subscription_id VARCHAR(20) REFERENCES subscriptions(subscription_id),
    billing_period_start DATE,
    billing_period_end DATE,
    amount INTEGER,
    status VARCHAR(20),
    created_at TIMESTAMP
);""")
    
    sql_lines.append("")
    
    # Insert customers
    sql_lines.append("-- Insert customers")
    for c in customers:
        email = f"'{c['email']}'" if c['email'] else 'NULL'
        phone = f"'{c['phone']}'" if c['phone'] else 'NULL'
        tz = f"'{c['timezone']}'" if c['timezone'] else 'NULL'
        sql_lines.append(f"INSERT INTO customers VALUES ('{c['customer_id']}', {email}, '{c['first_name']}', '{c['last_name']}', '{c['company_name']}', {phone}, '{c['created_at']}', {tz});")
    
    sql_lines.append("")
    
    # Insert subscriptions
    sql_lines.append("-- Insert subscriptions")
    for s in subscriptions:
        churned = f"'{s['churned_at']}'" if s['churned_at'] else 'NULL'
        sql_lines.append(f"INSERT INTO subscriptions VALUES ('{s['subscription_id']}', '{s['customer_id']}', '{s['plan_tier']}', '{s['status']}', {s['mrr']}, '{s['started_at']}', {churned}, {s['downgraded']}, '{s['enabled_features']}'::jsonb);")
    
    sql_lines.append("")
    
    # Insert tickets
    sql_lines.append("-- Insert support tickets")
    for t in tickets:
        sql_lines.append(f"INSERT INTO support_tickets VALUES ('{t['ticket_id']}', '{t['customer_id']}', '{t['subscription_id']}', '{t['created_at']}', '{t['priority']}', '{t['status']}', '{t['category']}');")
    
    sql_lines.append("")
    
    # Insert invoices
    sql_lines.append("-- Insert invoices")
    for inv in invoices:
        sql_lines.append(f"INSERT INTO invoices VALUES ('{inv['invoice_id']}', '{inv['customer_id']}', '{inv['subscription_id']}', '{inv['billing_period_start']}', '{inv['billing_period_end']}', {inv['amount']}, '{inv['status']}', '{inv['created_at']}');")
    
    return "\n".join(sql_lines)

if __name__ == "__main__":
    import os
    os.makedirs("data", exist_ok=True)
    
    sql_dump = generate_sql_dump()
    with open("data/nimbus_core_dump.sql", "w", encoding="utf-8") as f:
        f.write(sql_dump)
    
    print("PostgreSQL data generated: data/nimbus_core_dump.sql")
    print(f"  - Customers: {NUM_CUSTOMERS}")
    print(f"  - Subscriptions: {NUM_CUSTOMERS}")
