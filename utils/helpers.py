import random
from datetime import timedelta
from decimal import Decimal

def random_date(start_date, end_date):
    delta_days = (end_date - start_date).days
    return start_date + timedelta(days=random.randint(0, delta_days))

def seasonal_sales_multiplier(month: int) -> float:
    if month in [10, 11, 12]:
        return 1.25
    elif month in [1, 2]:
        return 0.90
    return 1.00

def calculate_tax(amount: Decimal) -> Decimal:
    return (amount * Decimal("0.18")).quantize(Decimal("0.01"))

def choose_sale_status():
    return random.choices(
        ["paid", "partially_paid", "generated"],
        weights=[60, 25, 15],
        k=1
    )[0]

def choose_receivable_status():
    return random.choices(
        ["closed", "partial", "pending"],
        weights=[60, 25, 15],
        k=1
    )[0]

def choose_payable_status():
    return random.choices(
        ["paid", "partial", "pending"],
        weights=[55, 25, 20],
        k=1
    )[0]

def decimal_amount(min_val, max_val):
    return Decimal(str(round(random.uniform(min_val, max_val), 2)))