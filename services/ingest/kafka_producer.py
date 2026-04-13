import json
from datetime import date
from confluent_kafka import Producer
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC

_producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})


def _serialize(obj):
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Not serializable: {type(obj)}")


def publish_records(records: list[dict]) -> None:
    for record in records:
        _producer.produce(
            KAFKA_TOPIC,
            key=f"{record['ticker']}:{record['date']}",
            value=json.dumps(record, default=_serialize).encode(),
        )
    _producer.flush()
