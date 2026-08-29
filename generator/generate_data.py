"""
FinFlow Synthetic Data Generator

Usage:
    python generate_data.py --preset SMALL
    python generate_data.py --preset MEDIUM
    python generate_data.py --customers 5000 --transactions 50000
"""

import argparse
import os
import random
import uuid

import psycopg2
from psycopg2.extras import execute_batch
from faker import Faker
from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk as os_bulk
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv
from config import (
    PRESETS,
    QUALITY_ISSUES,
    CURRENCIES,
    CHANNELS,
    PAYMENT_METHODS,
    COUNTRIES,
)



PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

fake = Faker()
Faker.seed(42)
random.seed(42)


# ============================================================
# PostgreSQL Connection
# ============================================================

def get_pg_conn():
    """Create PostgreSQL connection."""

    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "finflow"),
        user=os.getenv("POSTGRES_USER", "finflow_admin"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


# ============================================================
# OpenSearch Connection
# ============================================================

def get_os_client():
    """Create OpenSearch client."""

    return OpenSearch(
        hosts=[
            {
                "host": os.getenv("OPENSEARCH_HOST", "localhost"),
                "port": int(os.getenv("OPENSEARCH_PORT", 9200)),
            }
        ],
        use_ssl=False,
    )


# ============================================================
# Customers
# ============================================================

def generate_customers(conn, count):
    """Generate and insert synthetic customers."""

    print(f"Generating {count:,} customers...")

    cur = conn.cursor()
    customers = []

    for _ in tqdm(range(count)):
        customer_id = str(uuid.uuid4())

        created_at = fake.date_time_between(
            start_date="-2y",
            end_date="now",
        )

        customers.append(
            (
                customer_id,
                fake.name(),
                f"customer_{_}_{uuid.uuid4().hex[:8]}@example.com",
                f"+233{random.randint(200000000, 599999999)}",
                f"GHA-{random.randint(1000000000, 9999999999)}",
                random.choice(
                    [
                        "BASIC",
                        "STANDARD",
                        "ENHANCED",
                        "PREMIUM",
                    ]
                ),
                random.choices(
                    [
                        "ACTIVE",
                        "SUSPENDED",
                        "CLOSED",
                        "PENDING",
                    ],
                    weights=[85, 5, 5, 5],
                )[0],
                random.choice(COUNTRIES),
                created_at,
                created_at,
            )
        )

    execute_batch(
        cur,
        """
        INSERT INTO customers (
            customer_id,
            full_name,
            email,
            phone,
            national_id,
            kyc_tier,
            status,
            country,
            created_at,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        )
        """,
        customers,
        page_size=1000,
    )

    conn.commit()

    print(f"✓ Inserted {count:,} customers.")

    return [customer[0] for customer in customers]


# ============================================================
# Merchants
# ============================================================

def generate_merchants(conn, count):
    """Generate and insert synthetic merchants."""

    print(f"Generating {count:,} merchants...")

    cur = conn.cursor()
    merchants = []

    categories = [
        "RETAIL",
        "FOOD",
        "TRANSPORT",
        "UTILITIES",
        "TELECOMS",
        "HEALTH",
        "EDUCATION",
        "GOVERNMENT",
        "OTHER",
    ]

    for _ in tqdm(range(count)):
        merchant_id = str(uuid.uuid4())

        created_at = fake.date_time_between(
            start_date="-2y",
            end_date="now",
        )

        merchants.append(
            (
                merchant_id,
                fake.company(),
                random.choice(categories),
                random.choice(
                    [
                        "T+0",
                        "T+1",
                        "T+2",
                        "WEEKLY",
                    ]
                ),
                round(random.uniform(0.005, 0.035), 4),
                random.choices(
                    [
                        "ACTIVE",
                        "SUSPENDED",
                        "DEACTIVATED",
                    ],
                    weights=[90, 7, 3],
                )[0],
                random.choice(COUNTRIES),
                created_at,
                created_at,
            )
        )

    execute_batch(
        cur,
        """
        INSERT INTO merchants (
            merchant_id,
            business_name,
            category,
            settlement_freq,
            fee_rate,
            status,
            country,
            created_at,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s
        )
        """,
        merchants,
        page_size=1000,
    )

    conn.commit()

    print(f"✓ Inserted {count:,} merchants.")

    return [merchant[0] for merchant in merchants]


# ============================================================
# Transactions
# ============================================================

def generate_transactions(
    conn,
    count,
    customer_ids,
    merchant_ids,
):
    """Generate and insert synthetic transactions."""

    print(
        f"Generating {count:,} transactions "
        "(source-valid data)..."
    )

    cur = conn.cursor()

    batch = []

    for _ in tqdm(range(count)):

        transaction_id = str(uuid.uuid4())

        idempotency_key = (
            f"IDEM-{transaction_id[:12]}"
        )

        customer_id = random.choice(customer_ids)
        merchant_id = random.choice(merchant_ids)

        amount = round(
            random.lognormvariate(3.5, 1.5),
            4,
        )

        # Source DB constraint requires amount > 0.
        amount = max(amount, 0.01)
        amount = min(amount, 50000)

        fee_rate = round(
            random.uniform(0.005, 0.03),
            4,
        )

        fee = round(
            amount * fee_rate,
            4,
        )

        channel = random.choice(CHANNELS)
        payment_method = random.choice(PAYMENT_METHODS)

        created_at = fake.date_time_between(
            start_date="-1y",
            end_date="now",
        )

        status = "SUCCESS"

        if random.random() < QUALITY_ISSUES["failed_txn_rate"]:
            status = random.choice(
                [
                    "FAILED",
                    "EXPIRED",
                    "REVERSED",
                ]
            )

        suspicious = (
            random.random()
            < QUALITY_ISSUES["suspicious_txn_rate"]
        )

        if suspicious:
            amount = round(
                random.uniform(5000, 50000),
                4,
            )

            fee = round(
                amount * fee_rate,
                4,
            )

        # PostgreSQL CHECK constraint only permits
        # the currencies defined in the source schema.
        currency = random.choices(
            CURRENCIES,
            weights=[60, 15, 10, 5, 5, 5],
        )[0]

        # We do not create late-arriving timestamps
        # outside the source data window here.
        #
        # Late-arriving data will be simulated later
        # in the ingestion layer.

        risk_score = None
        is_flagged = False

        if amount > 3000 or status == "FAILED":

            risk_score = random.randint(
                30,
                100,
            )

            is_flagged = risk_score > 70

        failure_reason = None

        if status == "FAILED":
            failure_reason = random.choice(
                [
                    "Insufficient funds",
                    "Issuer declined",
                    "Risk check failed",
                    "Invalid payment credentials",
                ]
            )

        batch.append(
            (
                transaction_id,
                idempotency_key,
                customer_id,
                merchant_id,
                str(amount),
                currency,
                str(fee),
                channel,
                payment_method,
                status,
                failure_reason,
                fake.ipv4(),
                random.choice(
                    [
                        "ANDROID",
                        "IOS",
                        "WEB",
                        "USSD",
                    ]
                ),
                risk_score,
                is_flagged,
                created_at,
                created_at,
            )
        )

        if len(batch) >= 5000:

            _insert_txn_batch(
                cur,
                batch,
            )

            conn.commit()

            batch = []

    if batch:

        _insert_txn_batch(
            cur,
            batch,
        )

        conn.commit()

    print(
        f"✓ Inserted {count:,} transactions."
    )


def _insert_txn_batch(cur, batch):
    """Insert a transaction batch."""

    execute_batch(
        cur,
        """
        INSERT INTO transactions (
            transaction_id,
            idempotency_key,
            customer_id,
            merchant_id,
            amount,
            currency,
            fee,
            channel,
            payment_method,
            status,
            failure_reason,
            source_ip,
            device_type,
            risk_score,
            is_flagged,
            created_at,
            updated_at
        )
        VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s
        )
        ON CONFLICT (idempotency_key)
        DO NOTHING
        """,
        batch,
        page_size=1000,
    )


# ============================================================
# OpenSearch Events
# ============================================================

def generate_opensearch_events(
    os_client,
    customer_ids,
    count,
):
    """Generate synthetic events in OpenSearch."""

    print(
        f"Generating {count:,} OpenSearch events..."
    )

    actions = []

    event_types = [
        "LOGIN_SUCCESS",
        "LOGIN_FAILED",
        "LOGOUT",
        "PASSWORD_CHANGE",
        "MFA_ENABLED",
    ]

    indexes = [
        "finflow-login-events",
        "finflow-fraud-signals",
        "finflow-device-events",
        "finflow-app-events",
    ]

    for _ in tqdm(range(count)):

        index = random.choice(indexes)

        customer_id = random.choice(
            customer_ids
        )

        event_id = str(uuid.uuid4())

        doc = {
            "event_id": event_id,
            "customer_id": customer_id,
            "event_type": random.choice(
                event_types
            ),
            "timestamp": fake.date_time_between(
                start_date="-6M",
                end_date="now",
            ).isoformat(),
        }

        # ----------------------------------------------------
        # Login Events
        # ----------------------------------------------------

        if index == "finflow-login-events":

            doc.update(
                {
                    "device_type": random.choice(
                        [
                            "ANDROID",
                            "IOS",
                            "WEB",
                        ]
                    ),
                    "device_id": str(
                        uuid.uuid4()
                    ),
                    "ip_address": fake.ipv4(),
                    "country": random.choice(
                        COUNTRIES
                    ),
                    "city": fake.city(),
                    "success": random.random() > 0.1,
                    "failure_reason": None,
                    "user_agent": fake.user_agent(),
                }
            )

        # ----------------------------------------------------
        # Fraud Signals
        # ----------------------------------------------------

        elif index == "finflow-fraud-signals":

            doc.update(
                {
                    "signal_id": str(
                        uuid.uuid4()
                    ),
                    "transaction_id": str(
                        uuid.uuid4()
                    ),
                    "signal_type": random.choice(
                        [
                            "VELOCITY",
                            "AMOUNT",
                            "GEO",
                            "DEVICE",
                        ]
                    ),
                    "severity": random.choice(
                        [
                            "LOW",
                            "MEDIUM",
                            "HIGH",
                            "CRITICAL",
                        ]
                    ),
                    "score": random.randint(
                        0,
                        100,
                    ),
                    "details": {
                        "source": "synthetic_generator"
                    },
                }
            )

        # ----------------------------------------------------
        # Device Events
        # ----------------------------------------------------

        elif index == "finflow-device-events":

            doc.update(
                {
                    "device_id": str(
                        uuid.uuid4()
                    ),
                    "device_type": random.choice(
                        [
                            "ANDROID",
                            "IOS",
                            "WEB",
                        ]
                    ),
                    "os_version": random.choice(
                        [
                            "Android 13",
                            "Android 14",
                            "iOS 17",
                            "iOS 18",
                        ]
                    ),
                    "app_version": random.choice(
                        [
                            "1.0.0",
                            "1.1.0",
                            "1.2.0",
                            "2.0.0",
                        ]
                    ),
                    "event_type": random.choice(
                        [
                            "DEVICE_REGISTERED",
                            "DEVICE_LOGIN",
                            "DEVICE_REMOVED",
                        ]
                    ),
                    "latitude": float(
                        fake.latitude()
                    ),
                    "longitude": float(
                        fake.longitude()
                    ),
                }
            )

        # ----------------------------------------------------
        # Application Events
        # ----------------------------------------------------

        elif index == "finflow-app-events":

            doc.update(
                {
                    "screen": random.choice(
                        [
                            "LOGIN",
                            "HOME",
                            "PAYMENTS",
                            "WALLET",
                            "LOANS",
                            "PROFILE",
                        ]
                    ),
                    "action": random.choice(
                        [
                            "VIEW",
                            "CLICK",
                            "SUBMIT",
                            "SUCCESS",
                            "FAILED",
                        ]
                    ),
                    "metadata": {
                        "source": "synthetic_generator"
                    },
                    "session_id": str(
                        uuid.uuid4()
                    ),
                }
            )

        actions.append(
            {
                "_index": index,
                "_source": doc,
            }
        )

        if len(actions) >= 2000:

            os_bulk(
                os_client,
                actions,
            )

            actions = []

    if actions:

        os_bulk(
            os_client,
            actions,
        )

    print(
        f"✓ Inserted {count:,} events into OpenSearch."
    )


# ============================================================
# Main
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description="FinFlow Data Generator"
    )

    parser.add_argument(
        "--preset",
        choices=[
            "SMALL",
            "MEDIUM",
            "LARGE",
        ],
        default="SMALL",
    )

    parser.add_argument(
        "--customers",
        type=int,
    )

    parser.add_argument(
        "--transactions",
        type=int,
    )

    parser.add_argument(
        "--merchants",
        type=int,
    )

    parser.add_argument(
        "--events",
        type=int,
    )

    args = parser.parse_args()

    preset = PRESETS[args.preset]

    num_customers = (
        args.customers
        or preset["customers"]
    )

    num_transactions = (
        args.transactions
        or preset["transactions"]
    )

    num_merchants = (
        args.merchants
        or preset["merchants"]
    )

    num_events = (
        args.events
        or preset["events"]
    )

    print()
    print("=" * 60)
    print(
        f"FinFlow Data Generator ({args.preset})"
    )
    print("=" * 60)

    print(
        f"Customers:    {num_customers:>10,}"
    )

    print(
        f"Merchants:    {num_merchants:>10,}"
    )

    print(
        f"Transactions: {num_transactions:>10,}"
    )

    print(
        f"OS Events:    {num_events:>10,}"
    )

    print("=" * 60)
    print()

    # --------------------------------------------------------
    # PostgreSQL
    # --------------------------------------------------------

    print("Connecting to PostgreSQL...")

    conn = get_pg_conn()

    print("✓ PostgreSQL connection established.")
    print()

    customer_ids = generate_customers(
        conn,
        num_customers,
    )

    merchant_ids = generate_merchants(
        conn,
        num_merchants,
    )

    generate_transactions(
        conn,
        num_transactions,
        customer_ids,
        merchant_ids,
    )

    conn.close()

    print()
    print("✓ PostgreSQL generation complete.")
    print()

    # --------------------------------------------------------
    # OpenSearch
    # --------------------------------------------------------

    print("Connecting to OpenSearch...")

    os_client = get_os_client()

    print("✓ OpenSearch connection established.")
    print()

    generate_opensearch_events(
        os_client,
        customer_ids,
        num_events,
    )

    print()
    print("=" * 60)
    print("Generation Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()

