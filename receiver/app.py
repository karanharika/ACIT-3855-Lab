import connexion
from connexion import NoContent
import requests
import yaml
import logging
import logging.config
import datetime
import json
from pykafka import KafkaClient
import os
import time

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Enviornment")
    app_conf_file = "/config/app_conf.yaml"
    log_conf_file = "/config/log_conf.yaml"
else:
    print("In Dev Enviornment")
    app_conf_file = "app_conf.yaml"
    log_conf_file = "log_conf.yaml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info(f"App Conf File: {app_conf_file}")
logger.info(f"Log Conf File: {log_conf_file}")

current_retry_count = 0
hostname = f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}'

while current_retry_count < app_config["events"]["max_retries"]:
    logger.info(f"Trying to connect to Kafka. Try Number: {current_retry_count}")
    try:
        client = KafkaClient(hosts=hostname)
        topic = client.topics[str.encode(app_config["events"]["topic"])]
        producer = topic.get_sync_producer()
        break

    except:
        logger.error("Connection of Reciever service failed to Kafka")
        time.sleep(app_config["app_settings"]["sleep_time"])
        current_retry_count += 1

def req_gate(body):
    """ This function is for event request """

    logger.info("Received event req_gate request with a unique id of " + str(body['truck_id']))

    msg = {"type": "req_gate",
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "payload": body}
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    logger.info("Processed event req_gate request with a unique id of " + str(body['truck_id']) + " " + "201")
    return NoContent, 201


def assign_gate(body):
    """ This function is for 2nd event request """

    logger.info("Received event assign_gate request with a unique id of " + str(body['truck_id']))

    msg = {"type": "assign_gate",
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "payload": body}
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    logger.info("Processed event assign_gate request with a unique id of " + str(body['truck_id']) + " " + "201")
    return NoContent, 201


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml")

if __name__ == "__main__":
    app.run(port=8080)
