import mysql.connector
import yaml

with open("app_conf.yaml", 'r') as f:
    app_config = yaml.safe_load(f.read())

db_conn = mysql.connector.connect(host=app_config['datastore']['hostname'], user=app_config['datastore']['user'],
                                  password=app_config['datastore']['password'], database=app_config['datastore']['db'])
db_cursor = db_conn.cursor()

db_cursor.execute('''
        DROP TABLE gate_assign, gate_request
        ''')

db_conn.commit()
db_conn.close()