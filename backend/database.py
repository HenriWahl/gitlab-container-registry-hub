from datetime import datetime
from time import sleep
from urllib.parse import quote

from couchdb3 import Document, \
    Server
from dateutil.relativedelta import relativedelta
from deepdiff import DeepDiff

from backend.config import config, \
    TIMEOUT
from backend.helpers import log


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
        self._database.save_index(index={'fields': ['name']},
                                  ddoc='name')
        self._database.save_index(index={'fields': ['hash']},
                                  ddoc='hash')
        self._database.save_index(index={'fields': ['path']},
                                  ddoc='path')
        self._database.save_index(index={'fields': ['registry']},
                                  ddoc='registry')

    def store_by_id(self, document_id: str, document_content: dict) -> Document:
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

    def delete_by_document(self, document):
        """
        Delete a document from the database.
        :param document: document to delete
        """
        # quoting is necessary to avoid IDs being cut of at '/'s
        document_id_quoted = quote(document['_id'], safe='')
        revision = document.get('_rev')
        try:
            self._database.delete(docid=document_id_quoted, rev=revision)
        except Exception as exception:
            log.error(exception)
            return False
        return True



class CouchDBServer:

    # connect to CouchDB server
    def __init__(self, config):
        """
        Connect to CouchDB server using the configuration settings.
        :return: CouchDB server instance
        """
        while True:
            try:
                self._server = Server(
                    config.couchdb.url,
                    user=config.couchdb.user,
                    password=config.couchdb.password,
                    timeout=TIMEOUT
                )
                # test connection by retrieving all databases
                self._server.all_dbs()
                break
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
        # return self._server.get(database_name)


# connect to CouchDB server
couchdb = CouchDBServer(config)
