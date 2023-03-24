from kafka import KafkaConsumer, KafkaProducer
from django.conf import settings
import json

class Kafka(object):
    def produceKafkaEvent(self, topic, value):
        producer = KafkaProducer(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        producer.send(topic, json.dumps(value).encode('utf-8'))
        producer.flush()
        producer.close()

    def consumeKafkaEvent(self, topic):
        consumer = KafkaConsumer(topic, 
                                 group_id="my_group", # needed for consumer.commit()
                                 bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS, 
                                 value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                                 auto_offset_reset='earliest',
                                 enable_auto_commit=True,
                                 consumer_timeout_ms=200
                                )
        msg = []
        consumer.poll()
        for message in consumer:
            msg.append(message.value) 
        consumer.commit()
        consumer.close()
        return msg



