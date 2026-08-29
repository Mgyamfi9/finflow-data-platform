"""Data generation volume and quality configuration."""

PRESETS = {
    'SMALL': {
        'customers': 1_000,
        'transactions': 10_000,
        'merchants': 100,
        'loans': 500,
        'events': 5_000,
    },

    'MEDIUM': {
        'customers': 10_000,
        'transactions': 100_000,
        'merchants': 500,
        'loans': 5_000,
        'events': 50_000,
    },

    'LARGE': {
        'customers': 100_000,
        'transactions': 1_000_000,
        'merchants': 2_000,
        'loans': 50_000,
        'events': 500_000,
    },
}

QUALITY_ISSUES = {
    'duplicate_rate': 0.01,           # 1%
    'missing_customer_rate': 0.005,   # 0.5%
    'invalid_currency_rate': 0.003,   # 0.3%
    'negative_amount_rate': 0.002,    # 0.2%
    'null_timestamp_rate': 0.003,     # 0.3%
    'failed_txn_rate': 0.08,           # 8%
    'suspicious_txn_rate': 0.03,      # 3%
    'late_arriving_rate': 0.02,       # 2%
}

CURRENCIES = [
    'GHS',
    'USD',
    'EUR',
    'GBP',
    'NGN',
    'XOF',
]

CHANNELS = [
    'CARD',
    'MOBILE_MONEY',
    'BANK_TRANSFER',
    'QR',
    'USSD',
    'WALLET',
    'POS',
]

PAYMENT_METHODS = [
    'VISA',
    'MASTERCARD',
    'MOMO_MTN',
    'MOMO_VODAFONE',
    'MOMO_AIRTELTIGO',
    'BANK',
    'WALLET',
    'QR',
]

COUNTRIES = [
    'GHA',
    'NGA',
    'CIV',
    'SEN',
    'CMR',
    'KEN',
]
