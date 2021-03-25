import connexion
# from connexion import NoContent
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from gate_request import GateRequest
from gate_assign import GateAssign
import yaml
# import logging
import logging.config
import datetime
import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
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

DB_ENGINE = create_engine(
    f'mysql+pymysql://{app_config["datastore"]["user"]}:{app_config["datastore"]["password"]}@{app_config["datastore"]["hostname"]}:{app_config["datastore"]["port"]}/{app_config["datastore"]["db"]}')
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

logger.info(
    f"Connecting to the Database at Hostname: {app_config['datastore']['hostname']} and Port: {app_config['datastore']['port']}")


def get_req_gate(timestamp):
    """ Gets the gate request event after the timestamp """

    session = DB_SESSION()

    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
    print(timestamp_datetime)
    gate_requests = session.query(GateRequest).filter(GateRequest.date_created >= timestamp_datetime)
    print(gate_requests)
    results_list = []

    for request in gate_requests:
        results_list.append(request.to_dict())

    session.close()

    logger.info(f"Query for Gate Requests after {timestamp} returns {len(results_list)} results")

    return results_list, 200


def get_assign_gate(timestamp):
    """ Gets the gate assigned event after the timestamp """

    session = DB_SESSION()

    timestamp_datetime = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")

    gate_assignments = session.query(GateAssign).filter(GateAssign.date_created >= timestamp_datetime)

    results_list = []

    for request in gate_assignments:
        results_list.append(request.to_dict())

    session.close()

    logger.info(f"Query for Gate Assignments after {timestamp} returns {len(results_list)} results")

    return results_list, 200


def process_messages():
    """ Process event messages """

    hostname = f'{app_config["events"]["hostname"]}:{app_config["events"]["port"]}'
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
                                         reset_offset_on_start=False,
                                         auto_offset_reset=OffsetType.LATEST)

    # This is blocking -it will wait    for a new message
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]

        session = DB_SESSION()
        if msg["type"] == "req_gate":
            # Store the event1 (i.e., the payload) to the DB
            req = GateRequest(payload['truck_id'],
                              payload['license_plate'],
                              payload['trailer_type'])
            # print(req)
            session.add(req)
            logger.debug("Stored event assign_gate request with a unique id of " + str(payload['truck_id']))

        elif msg["type"] == "assign_gate":
            # Store the event2 (i.e., the payload) to the DB
            assign = GateAssign(payload['truck_id'],
                                payload['license_plate'],
                                payload['gate_number'])

            session.add(assign)
            logger.debug("Stored event assign_gate request with a unique id of " + str(payload['truck_id']))

        # Commit the new message as being read
        session.commit()
        session.close()

        consumer.commit_offsets()


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090)
