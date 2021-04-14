import connexion
import yaml
import json
import logging.config
from pykafka import KafkaClient
from flask_cors import CORS, cross_origin
import os

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


def get_req_gate(index):
    """ Get gate request event """

    hostname = f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}'
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)

    logger.info(f"Getting the Gate Request at index {index}")

    count = 0
    reading = None
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)

            if msg["type"] == "req_gate":
                logger.info(f"Count: {count}")

                if count == index:
                    reading = msg["payload"]
                    return reading, 200

                count += 1
    except:
        logger.error("No more messages found")

    logger.error(f"Couldn't find gate request at index {index}")
    return {"message": "Not Found"}, 404


def get_assign_gate(index):
    """ Get gate assignment event """

    hostname = f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}'
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True,
                                         consumer_timeout_ms=1000)

    logger.info(f"Getting the Gate Assignment at index {index}")

    count = 0
    reading = None
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)

            if msg["type"] == "assign_gate":
                logger.info(f"Count: {count}")

                if count == index:
                    reading = msg["payload"]
                    return reading, 200

                count += 1
    except:
        logger.error("No more messages found")

    logger.error(f"Couldn't find gate assignment at index {index}")
    return {"message": "Not Found"}, 404


app = connexion.FlaskApp(__name__, specification_dir='')
if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] != "test":
    CORS(app.app)
    app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml", base_path="/audit_log", strict_validation=True, validate_responses=True)

if __name__ == "__main__":

    app.run(port=8110)
