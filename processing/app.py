import connexion
from connexion import NoContent
import yaml
import json
import os
import datetime
import requests
import logging
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
from flask_cors import CORS, cross_origin

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


def get_stats():
    """This function gets the stats for the events """

    logger.info("Get Stats request has started")
    current_stats = {}

    if os.path.isfile(app_config["datastore"]["filename"]):
        current_stats_file = open(app_config["datastore"]["filename"])
        data = current_stats_file.read()
        current_stats = json.loads(data)
        current_stats_file.close()

        logger.debug(f"NUM_GATE_REQUESTS: {current_stats['num_gate_requests']}")
        logger.debug(f"NUM_GATE_ASSIGNMENTS: {current_stats['num_gate_assignments']}")

    else:
        logger.error("Datastore file does not exist")
        return "Statistics do not exist", 404

    logger.info("Get Stats request ended")

    return current_stats, 200


def populate_stats():
    """ Periodically update stats """

    logger.info("Start Periodic Processing")
    stats = {}

    if os.path.isfile(app_config["datastore"]["filename"]):
        stats_file = open(app_config["datastore"]["filename"])
        data = stats_file.read()
        stats = json.loads(data)
        stats_file.close()

    last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if "last_updated" in stats:
        last_updated = stats["last_updated"]

    response = requests.get(app_config["eventstore"]["url"] + "/gate/req?timestamp=" + last_updated)
    # http://localhost:8090   /gate/req?timestamp=   2021-02-19T09:12:33Z
    if response.status_code == 200:
        if "num_gate_requests" in stats.keys():
            stats["num_gate_requests"] += len(response.json())
        else:
            stats["num_gate_requests"] = len(response.json())
        # logger.debug(f"URL used {app_config['eventstore']['url'] + '/gate/req?timestamp=' + last_updated}")
        logger.info(f"Processed {len(response.json())} number of Gate Requests {last_updated}")
    else:
        logger.error("An error occurred while getting gate request data")

    response = requests.get(app_config["eventstore"]["url"] + "/gate/assign?timestamp=" + last_updated)
    # print(len(response.json()))
    # print(last_updated)
    if response.status_code == 200:
        if "num_gate_assignments" in stats.keys():
            stats["num_gate_assignments"] += len(response.json())
        else:
            stats["num_gate_assignments"] = len(response.json())
        logger.info(f"Processed {len(response.json())} number of Gate Assignments")
    else:
        logger.error("An error occurred while getting gate request data")

    stats["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    stats_file = open(app_config["datastore"]["filename"], "w")
    stats_file.write(json.dumps(stats, indent=4))
    stats_file.close()

    logger.info("Processing Done")


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval',seconds=app_config['scheduler']['period_sec'])
    sched.start()


app = connexion.FlaskApp(__name__, specification_dir='')
CORS(app.app)
app.app.config['CORS_HEADERS'] = 'Content-Type'
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100)
