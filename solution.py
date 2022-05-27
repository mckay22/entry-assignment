import json
import psycopg2
from psycopg2 import errors
import os


class Interface:
    """ Base Interface class that represents data with desired Instance attributes
     which needs to be stored in postgres db"""
    exclude_interfaces = ['BDI', 'Loopback']

    def __init__(self, group_name, interface_name, description, max_frame_size, config, port_channel_id) -> None:
        self.group_name = group_name
        self.interface_name = interface_name
        self.postgres_name = group_name + str(interface_name)
        self.description = description
        self.max_frame_size = max_frame_size
        self.config = json.dumps(config)
        self.port_channel_id = port_channel_id
        self.valid = self.check_if_valid_interface()

    def check_if_valid_interface(self) -> bool:
        """Based on assignment We can ignore interfaces that are not needed"""
        return True if self.group_name not in self.exclude_interfaces else False


class DatabaseManager:

    def __init__(self):
        self.conn = self.initialize_connection()
        self.curr = self.conn.cursor()
        self.desired_interfaces = []

    @staticmethod
    def initialize_connection():
        connection = psycopg2.connect(database='postgres',
                                      user=os.environ['DB_USERNAME'],
                                      password=os.environ['DB_PASSWORD'],
                                      host='localhost', port='5432')
        return connection

    def parse_config_file(self) -> None:
        """Extract desired interfaces from configClear_v2.json"""
        with open('assignment/configClear_v2.json', 'r') as f:
            file = json.load(f)

        config_interfaces = file['frinx-uniconfig-topology:configuration']['Cisco-IOS-XE-native:native']['interface']
        for group_name in config_interfaces.keys():
            for interface_data in config_interfaces[group_name]:
                self.initialize_interface(group_name, interface_data)

    def initialize_interface(self, group_name, interface_data) -> None:
        """ Initializing instances of class Interface"""
        valid_port_channel_id = interface_data.get('Cisco-IOS-XE-ethernet:channel-group')
        # since channel-group is not present in every configuration we need to check if this dictionary exists
        if valid_port_channel_id:
            port_channel_id = valid_port_channel_id.get('number')
        else:
            port_channel_id = None
        interface = Interface(group_name=group_name,
                              interface_name=interface_data.get('name'),
                              description=interface_data.get('description'),
                              max_frame_size=interface_data.get('mtu'),
                              config=interface_data,
                              port_channel_id=port_channel_id)
        if interface.valid:
            # we want to append only desired interfaces
            self.desired_interfaces.append(interface)

    def create_table(self) -> None:
        command = '''
        CREATE TABLE interfaces (id SERIAL PRIMARY KEY,
        connection INTEGER,
        name VARCHAR(255) NOT NULL,
        description VARCHAR(255),
        config json,type VARCHAR(50),
        infra_type VARCHAR(50),
        port_channel_id INTEGER,
        max_frame_size INTEGER);'''
        try:
            self.curr.execute(command)
            self.conn.commit()
        except psycopg2.errors.DuplicateTable:
            self.conn.rollback()
            print('error: Table already exists')

    def insert_into_table(self) -> None:
        interface_list = []
        for interface in self.desired_interfaces:
            interface_list.append((interface.postgres_name,
                                   interface.description,
                                   interface.max_frame_size,
                                   interface.config,
                                   interface.port_channel_id))
        sql_query_insert = """INSERT INTO interfaces (name, description, max_frame_size, config, port_channel_id) VALUES (%s, %s, %s, %s, %s)"""
        try:
            self.curr.executemany(sql_query_insert, interface_list)
            self.conn.commit()
        except Exception as e:
            print(f"error occurred: {e}, Rolling back")
            self.conn.rollback()

    def close_db_connection(self) -> None:
        self.curr.close()
        self.conn.close()

    def main(self) -> None:
        self.create_table()
        self.parse_config_file()
        self.insert_into_table()
        self.close_db_connection()


if __name__ == "__main__":
    DatabaseManager().main()
