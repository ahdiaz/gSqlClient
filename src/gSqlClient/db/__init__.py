# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
# gSqlClient is a Python plugin that turns Gedit into a SQL client.
# Copyright (C) 2009 Antonio Hernández Diaz <ahdiaz@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


import time
import hashlib

import gettext
from gettext import gettext as _
gettext.textdomain('gsqlclient')

__DB_NONE__ = _("(None)")
__DB_MYSQL__ = "MySQL"
__DB_POSTGRE__ = "PostgreSQL"
__DB_SQLITE__ = "SQLite"
__DB_SQLSERVER__ = "SQLServer"

__DEFAULT_PORT_MYSQL__ = 3306
__DEFAULT_PORT_POSTGRE__ = 5432
__DEFAULT_PORT_SQLSERVER__ = 1433

def get_connector(options):

    cnn = None
    driver = options['driver']

    if driver == __DB_MYSQL__:

        import mysql
        cnn = mysql.MySQLConnector(options)

    elif driver == __DB_POSTGRE__:

        import postgre
        cnn = postgre.PostgreSQLConnector(options)

    elif driver == __DB_SQLITE__:

        import sqlite
        cnn = sqlite.SQLiteConnector(options)

    elif driver == __DB_SQLSERVER__:

        import mssql
        cnn = mssql.SQLServerConnector(options)

    if cnn == None:
        raise InvalidConnectorError(driver)

    return cnn

def get_default_port(driver):

    port = "";

    if driver == __DB_MYSQL__:
        port = __DEFAULT_PORT_MYSQL__

    elif driver == __DB_POSTGRE__:
        port = __DEFAULT_PORT_POSTGRE__

    elif driver == __DB_SQLSERVER__:
        port = __DEFAULT_PORT_SQLSERVER__

    return port

def create_hash(options):
    hash = ";".join(["%s=%s" % (k, v) for k, v in options.items()])
    hash = hashlib.md5(hash).hexdigest()
    return hash

class Connector():

    def __init__(self, options):

        self.db = None
        self.hash = create_hash(options)

        if "driver" in options:
            driver = str(options["driver"]).strip()
            if len(driver) == 0:
                raise db.ConnectorError(-1, _("The driver cannot be empty."))
            self.driver = driver

        else:
            raise db.ConnectorError(-1, _("The driver cannot be empty."))

        self.host = ""
        self.port = ""
        self.socket = ""
        self.user = ""
        self.passwd = ""
        self.schema = ""

        if "host" in options:
            self.set_host(options["host"])

        if "port" in options:
            self.set_port(options["port"])

        if "socket" in options:
            self.set_socket(options["socket"])

        if "user" in options:
            self.set_user(options["user"])

        if "passwd" in options:
            self.set_passwd(options["passwd"])

        if "schema" in options:
            self.set_schema(options["schema"])

        self.update_connection_string()

    def update_connection_string(self):
        pass

    def get_connection_string(self):
        self.update_connection_string()
        return self.connection_string

    def get_driver(self):
        return self.driver

    def get_host(self):
        return self.host

    def set_host(self, host):
        self.host = str(host).strip()

    def get_port(self):
        return self.port

    def set_port(self, port):
        self.port = str(port).strip()

    def get_socket(self):
        return self.socket

    def set_socket(self, socket):
        self.socket = str(socket).strip()

    def get_user(self):
        return self.user

    def set_user(self, user):
        self.user = str(user).strip()

    def get_passwd(self):
        return self.passwd

    def set_passwd(self, passwd):
        self.passwd = str(passwd).strip()

    def get_schema(self):
        return self.schema

    def set_schema(self, schema):
        self.schema = str(schema).strip()

    def _get_options(self):
        # Return specific driver options
        pass

    def get_options(self):
        # Return normalized options
        options = {
            "driver": self.driver,
            "host": self.host,
            "port": self.port,
            "socket": self.socket,
            "user": self.user,
            "passwd": self.passwd,
            "schema": self.schema
        }
        return options

    def connect(self):
        pass

    def close(self):
        if self.db != None:
            self.db.close()
            self.db = None

    def cursor(self):

        if self.db == None:
            # raise NotConnected
            return None

        cursor = self.db.cursor()
        return cursor

    def is_connected(self):
        return self.db != None

    def _execute(self, query):
        pass

    def execute(self, query):
        """ Executes a SQL query """

        result = {
            "rowcount": 0,
            "execution_time": None,
            "selection": False,
            "cursor": None,
            "description": None
        }

        try:

            t1 = time.time()
            cursor = self._execute(query)
            execution_time = time.time() - t1

            # http://docs.python.org/library/sqlite3.html#sqlite3.Cursor.rowcount
            # the database engine's own support for the determination
            # of "rows affected"/"rows selected" is quirky.
            result["rowcount"] = cursor.rowcount

            result["execution_time"] = execution_time

            if cursor.description is not None:
                result["selection"] = True
                result["cursor"] = cursor
                result["description"] = cursor.description

        except ConnectorError, e:
            raise e

        return result

class DummyConnector(Connector):

    def __init__(self, name):
        self.driver = name

    def _get_options(self):
        return {}

    def update_connection_string(self):
        self.connection_string = self.driver

    def connect(self):
        raise db.ConnectorError(-1, _("This connector is used only from the treeview."))

    def _execute(self, query):
        raise db.ConnectorError(-1, _("This connector is used only from the treeview."))

class DbPool():

    def __init__(self):
        self._db_pool = {}

    def get(self, key):
        if key in self._db_pool:
            return self._db_pool[key]
        else:
            return None

    def append(self, connector):
        self._db_pool.update({connector.connection_string: connector})

    def remove(self, connector):
        del self._db_pool[connector.connection_string]

    def keys(self):
        return self._db_pool.keys()

class InvalidConnectorError(Exception):

    def __init__(self, driver, message=None):
        self.driver = driver
        if message == None:
            message = _("Connector \"%s\" is not valid.") % (driver,)
        self.message = message

    def __str__(self):
        return "InvalidConnectorError: %s" % (self.message,)


class ConnectorError(Exception):

    def __init__(self, errno, error):
        self.errno = errno
        self.error = error

    def __str__(self):
        return "Error %s: %s" % (self.errno, self.error)
