import producer_server
import os


def run_kafka_server():
    input_file = "police-department-calls-for-service.json"

    producer = producer_server.ProducerServer(
        input_file=input_file,
        topic="com.udacity.sf-crime.police.calls",
        bootstrap_servers="127.0.0.1:9092",
    )
    return producer


def feed():
    producer = run_kafka_server()
    try:
        producer.generate_data()
    except KeyboardInterrupt as e:
        producer.close()


if __name__ == "__main__":
    feed()
