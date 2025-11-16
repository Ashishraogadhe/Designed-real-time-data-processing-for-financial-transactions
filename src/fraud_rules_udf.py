from pyspark.sql.types import BooleanType
from pyspark.sql.functions import udf

def is_suspicious(amount, country, merchant_category, device_id, txn_count_last_hour):
    if amount is None:
        return False

    # Simple rule examples
    if amount > 10000:
        return True
    if country not in ("US", "GB", "CA", "DE") and amount > 3000:
        return True
    if merchant_category == "CRYPTO" and amount > 2000:
        return True
    if txn_count_last_hour is not None and txn_count_last_hour > 20:
        return True

    return False

is_suspicious_udf = udf(is_suspicious, BooleanType())
