from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, window, count
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
from fraud_rules_udf import is_suspicious_udf
from config import config

spark = (
    SparkSession.builder
    .appName("RealtimeTransactions")
    .getOrCreate()
)

schema = StructType([
    StructField("txn_id", StringType()),
    StructField("customer_id", StringType()),
    StructField("country", StringType()),
    StructField("merchant_category", StringType()),
    StructField("device_id", StringType()),
    StructField("amount", DoubleType()),
    StructField("txn_time", TimestampType()),
])

eh_conf = {
    "eventhubs.connectionString": config.event_hub_connection_string
}

raw_stream = (
    spark.readStream.format("eventhubs")
    .options(**eh_conf)
    .load()
)

parsed = (
    raw_stream
    .select(from_json(col("body").cast("string"), schema).alias("data"))
    .select("data.*")
)

# Sliding window to compute transaction counts per device
txn_counts = (
    parsed
    .withWatermark("txn_time", "5 minutes")
    .groupBy(
        window(col("txn_time"), "1 hour", "5 minutes"),
        col("device_id")
    )
    .agg(count("*").alias("txn_count_last_hour"))
)

joined = (
    parsed.alias("p")
    .join(
        txn_counts.alias("c"),
        (col("p.device_id") == col("c.device_id")) &
        (col("p.txn_time").between(col("c.window.start"), col("c.window.end"))),
        "left"
    )
    .select(
        col("p.*"),
        col("txn_count_last_hour")
    )
)

scored = joined.withColumn(
    "is_suspicious",
    is_suspicious_udf(
        col("amount"),
        col("country"),
        col("merchant_category"),
        col("device_id"),
        col("txn_count_last_hour")
    )
)

# Write full stream
transactions_query = (
    scored.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{config.checkpoint_path}/transactions")
    .start(config.transactions_path)
)

# Write fraud alerts only
alerts = scored.where(col("is_suspicious") == True)

alerts_query = (
    alerts.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", f"{config.checkpoint_path}/fraud_alerts")
    .start(config.fraud_alerts_path)
)

spark.streams.awaitAnyTermination()
