from datetime import datetime
from json import dumps
from time import sleep
from urllib.parse import quote

from couchdb3 import Document, \
    Server
from dateutil.relativedelta import relativedelta
from deepdiff import DeepDiff, \
    Delta

from backend.config import config, \
    TIMEOUT


class CouchDBDatabase:
    """
    CouchDBDatabase class to handle operations on a specific CouchDB database.
    """

    def __init__(self, server, name):
        """
        Initialize the CouchDBDatabase with the given database name.
        :param database_name: Name of the database
        """
        self._name = name
        self._database = server.get(name)

    def store(self, document_id: str, document_content: dict) -> Document:
        # quoting is necessary to avoid IDs being cut of at '/'s
        document_id_quoted = quote(document_id, safe='')
        document = self._database.get(document_id_quoted)
        for key, value in document_content.items():
            if isinstance(value, datetime):
                # convert datetime to string
                document_content[key] = value.isoformat()
            elif isinstance(value, relativedelta):
                # convert datetime to string
                document_content[key] = str(value)
            # elif value == None:
            #     #document_content[key] = str(value)
            #     document_content[key] = ''

        if document:
            document_as_dict = dict(document)
            diff = DeepDiff(document_as_dict, document_content, ignore_order=True)
            # something is strange with 'status', needs to be checked
            # same with 'cleanup_policy_started_at'
            if 'airflow' in document_id:
                pass
            if diff.get('values_changed') or \
                diff.get('affected_root_keys') and \
                diff.affected_root_keys != set(['_id', '_rev']):
                #diff.affected_root_keys != set(['status', '_id', '_rev']):
                # diff.affected_root_keys != set(['status', '_id', '_rev']) and \
                # diff.affected_root_keys != set(['cleanup_policy_started_at', 'status', '_id', '_rev']):
                #document_content_json = dumps(document_content)
                #document.update({**{'_id': document_id_quoted}, **document_content_json})
                document.update({**{'_id': document_id_quoted}, **document_content})
                self._database.save(document)
        else:
            #document_content_json = dumps(document_content)
            #self._database.save({**{'_id': document_id_quoted}, **document_content_json})
            self._database.save({**{'_id': document_id_quoted}, **document_content})

        return self._database.get(document_id)


class CouchDBServer:

    # connect to CouchDB server
    def __init__(self, config):
        """
        Connect to CouchDB server using the configuration settings.
        :return: CouchDB server instance
        """

        self._server = None

        while not self._server:
            try:
                self._server = Server(
                    config.couchdb.url,
                    user=config.couchdb.user,
                    password=config.couchdb.password,
                    timeout=TIMEOUT
                )
                print(dir(self._server))
            except Exception as exception:
                print(f"Error connecting to CouchDB: {exception}")
                sleep(10)

        if not '_users' in self._server.all_dbs():
            print("Creating '_users' database...")
            self._server.create('_users')

    def all_databases(self):
        """
        Get a list of all databases on the CouchDB server.
        :return: List of database names
        """
        return self._server.all_dbs()

    def get(self, database_name):
        """
        Get a specific database by name.
        :param database_name: Name of the database to retrieve
        :return: Database instance
        """
        if not (database_name in self._server.all_dbs()):
            self._server.create(database_name)
        return self._server.get(database_name)

    def get_database(self, database_name):
        """
        Get a specific database by name.
        :param database_name: Name of the database to retrieve
        :return: Database instance
        """
        if database_name not in self._server.all_dbs():
            self._server.create(database_name)
        return CouchDBDatabase(self, database_name)


# connect to CouchDB server
couchdb = CouchDBServer(config)
print(dir(couchdb))

pass
