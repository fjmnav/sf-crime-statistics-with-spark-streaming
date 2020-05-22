from kafka import KafkaProducer
import json
import time
import logging

logger = logging.getLogger(__name__)

class ProducerServer(KafkaProducer):

    def __init__(self, input_file, topic, **kwargs):
        super().__init__(**kwargs)
        self.input_file = input_file
        self.topic = topic

    def generate_data(self):
        with open(self.input_file) as f:
            # This is asking for an OOM. Data files shouldn't be multiline
            calls = json.load(f)
            for call in calls:
                message = self.dict_to_binary(call)
                self.send(self.topic, message)
                logger.info(f"Call {call} Sent to Topic {self.topic}!")
                time.sleep(1)

    def dict_to_binary(self, json_dict):
        return json.dumps(json_dict).encode("utf-8")

    def close(self):
        """Prepares the producer for exit by cleaning up the producer"""
        logger.info("flushing producer...")
        self.flush(5)
