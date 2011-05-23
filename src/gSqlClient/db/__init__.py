#
# gSqlClient plugin for Gedit allows to query MySQL databases.
# Copyright (C) 2009 Antonio Hernandez Diaz <ahdiaz@gmail.com>
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
# $Id$
#

import time
import hashlib

__DB_MYSQL__ = 'MySQL'
__DB_POSTGRE__ = 'PostgreSQL'
__DB_SQLITE__ = 'SQLite'
__DB_SQLSERVER__ = 'SQLServer'

__DEFAULT_PORT_MYSQL__ = 3306
__DEFAULT_PORT_POSTGRE__ = 5432
__DEFAULT_PORT_SQLSERVER__ = 1433
    
def get_connector(options):
        
    cnn = None
    driver = options['driver']
    
    if driver == __DB_MYSQL__:
        
        import mysql
        cnn = mysql.MySQLConnector(options)
        
    elif driver == __DB_SQLITE__:
        
        import sqlite
        cnn = sqlite.SQLiteConnector(options)

    if cnn == None:
        # raise Exception
        pass
    
    return cnn

def create_hash(options):
    hash = ";".join(["%s=%s" % (k, v) for k, v in options.items()])
    hash = hashlib.md5(hash).hexdigest()
    return hash


class Connector():

    def __init__(self, options):
        self.db = None
        self.hash = create_hash(options)
        self.options = options.copy()
        self.driver = self.options['driver']
        del self.options['driver']
        self.connection_string = self._create_connection_string()

    def _create_connection_string(self):
        pass

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
            "executed": False,
            "errno": 0,
            "error": '',
            "rowcount": 0,
            "execution_time": None,
            "selection": False,
            "cursor": None,
            "description": None
        }
    
        if self.is_connected() == False:
            return result
    
        try:
    
            t1 = time.time()
            cursor = self._execute(query)
            execution_time = time.time() - t1
    
            # http://docs.python.org/library/sqlite3.html#sqlite3.Cursor.rowcount
            # the database engine's own support for the determination
            # of "rows affected"/"rows selected" is quirky.
            result["rowcount"] = cursor.rowcount
        
            result["executed"] = True
    
            result["execution_time"] = execution_time
    
            if cursor.description is not None:
                result["selection"] = True
                result["cursor"] = cursor
                result["description"] = cursor.description
    
        except Error, e:
            result["errno"] = e.errno
            result["error"] = e.error
    
        return result

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

class QueryParser():

    def set_buffer(self, buffer):
        self._buffer = buffer

    def _get_iter_at_cursor(self):
        iter = self._buffer.get_iter_at_mark(self._buffer.get_insert())
        return iter

    def get_line(self, its):
        ite = its.copy()
        its.set_line_offset(0)
        if  not ite.ends_line():
            ite.forward_to_line_end()
        if its.get_line() != ite.get_line():
            return ""
        line = its.get_text(ite).strip()
        #print "\n(%s) - %s\n" % (len(line), line)
        return line

    def get_selection(self):
        query = None
        selection = self._buffer.get_selection_bounds()
        if len(selection) > 0:
            its = selection[0]
            ite = selection[1]
            query = its.get_text(ite)

        return query

    def get_current_query(self):

        selection = self.get_selection()
        if selection is not None:
            return selection

        query = []
        its = self._get_iter_at_cursor()
        line = self.get_line(its)
        
        while len(line) > 0:
            query.append(line)
            ret = its.backward_line()
            line = self.get_line(its)
            if ret == False:
                line = ""
        query.reverse()

        its = self._get_iter_at_cursor()
        while 1:
            cont = its.forward_line()
            line = self.get_line(its)
            if not cont or len(line) == 0:
                break
            else:
                query.append(line)

        query = str.join("\n", query).strip()
        if len(query) == 0:
            query = None

        return query

    def get_all_queries(self):
        queries = []
        query = []
        it = self._buffer.get_start_iter()
        while 1:
            line = self.get_line(it)
            if len(line) > 0:
                query.append(line)
            else:
                query = str.join("\n", query).strip()
                queries.append(query)
                query = []
            if not it.forward_line():
                if len(query) > 0:
                    query = str.join("\n", query).strip()
                    queries.append(query)
                break

        return queries

class Error(Exception):
    
    def __init__(self, errno, error):
        self.errno = errno
        self.error = error
