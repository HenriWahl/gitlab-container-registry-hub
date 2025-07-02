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
        self._database = server.get_database_from_server(name)
        index_name = self._database.save_index(index={'fields': ['name']},
                                  ddoc='name')
        index_id = self._database.save_index(index={'fields': ['id']},
                                  ddoc='id',
                                  name='id')
        pass

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
            if diff.get('values_changed') or \
                diff.get('affected_root_keys') and \
                set(diff.affected_root_keys) != {'_id', '_rev'}:
                document.update({**{'_id': document_id_quoted}, **document_content})
                self._database.save(document)
        else:
            self._database.save({**{'_id': document_id_quoted}, **document_content})

        return self._database.get(document_id)

    def find(self, selector=dict(), use_index=None):
        result = self._database.find(selector=selector,
                                    use_index=use_index,
                                    limit=99999999)
        if 'warning' in result:
            print(result['warning'])
        return result.get('docs', list())


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

    def get_database_from_server(self, database_name):
        """
        Get access to a database on server
        :param database_name: Name of the database to retrieve
        :return: Database instance
        """
        if database_name not in self._server.all_dbs():
            self._server.create(database_name)
        return self._server.get(database_name)

    def get_database_object(self, database_name):
        """
        Get a specific database object, instance of CouchDBDatabase
        :param database_name: Name of the database to retrieve
        :return: Database instance
        """
        if database_name not in self._server.all_dbs():
            self._server.create(database_name)
        return CouchDBDatabase(self, database_name)
        #return self._server.get(database_name)

# connect to CouchDB server
couchdb = CouchDBServer(config)
