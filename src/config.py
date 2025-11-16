from dataclasses import dataclass

@dataclass
class StreamConfig:
    event_hub_connection_string: str = "<EVENT_HUB_CONNECTION_STRING>"
    event_hub_name: str = "transactions"
    checkpoint_path: str = "abfss://finance@yourstorageaccount.dfs.core.windows.net/checkpoints/transactions"
    transactions_path: str = "abfss://finance@yourstorageaccount.dfs.core.windows.net/silver/transactions_stream"
    fraud_alerts_path: str = "abfss://finance@yourstorageaccount.dfs.core.windows.net/gold/fraud_alerts"

config = StreamConfig()
