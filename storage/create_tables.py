import mysql.connector
import yaml

with open("app_conf.yaml", 'r') as f:
    app_config = yaml.safe_load(f.read())

db_conn = mysql.connector.connect(host=app_config['datastore']['hostname'], user=app_config['datastore']['user'],
                                  password=app_config['datastore']['password'], database=app_config['datastore']['db'])

db_cursor = db_conn.cursor()

db_cursor.execute('''
        CREATE TABLE gate_request
        (id INT NOT NULL AUTO_INCREMENT,
        truck_id VARCHAR(250) NOT NULL,
        license_plate VARCHAR(250) NOT NULL,
        trailer_type VARCHAR(250) NOT NULL,
        date_created VARCHAR(100) NOT NULL,
        CONSTRAINT gate_request_pk PRIMARY KEY (id))
        ''')

db_cursor.execute('''
        CREATE TABLE gate_assign
        (id INT NOT NULL AUTO_INCREMENT,
        truck_id VARCHAR(250) NOT NULL,
        license_plate VARCHAR(250) NOT NULL,
        gate_number INTEGER NOT NULL,
        date_created VARCHAR(100) NOT NULL,
        CONSTRAINT gate_assign_pk PRIMARY KEY (id))
        ''')

db_conn.commit()
db_conn.close()
