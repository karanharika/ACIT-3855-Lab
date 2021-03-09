import connexion
from connexion import NoContent
import requests
import yaml
import logging
import logging.config
import datetime
import json
from pykafka import KafkaClient

with open("app_conf.yaml", 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yaml', 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

    logger = logging.getLogger('basicLogger')


def req_gate(body):
    """ This function is for event request """

    logger.info("Received event req_gate request with a unique id of " + str(body['truck_id']))
    # response = requests.post(app_config['gate_request']['url'], json=body)

    client = KafkaClient(hosts=f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}')
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    producer = topic.get_sync_producer()
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
    # response = requests.post(app_config['gate_assign']['url'], json=body)

    client = KafkaClient(hosts=f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}')
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    producer = topic.get_sync_producer()
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
