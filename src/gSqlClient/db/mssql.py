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


############################
# Warning: Untested module #
############################

import pymssql
from .. import db

class SQLServerConnector(db.Connector):

    def _get_options(self):

        options = {
            "host": "%s:%s" % (self.host, self.port),
            "user": self.user,
            "password": self.passwd,
            "database": self.schema
        }

        if len(self.socket) > 0:
            options["host"] = self.socket

        return options

    def update_connection_string(self):

        if len(self.socket) > 0:
            host = self.socket
        else:
            host = '%s:%s' % (self.host, self.port)

        host = '%s@%s' % (self.user, host)

        self.connection_string = '%s://%s' % (self.driver, host)

    def connect(self):

        if self.db != None:
            return self.db

        try:
            options = self._get_options()
            self.db = pymssql.connect(**options)

        except pymssql.MssqlException, e:
            raise db.ConnectorError(e.number, e.message)

        return self.db

    def _execute(self, query):

        cursor = None

        try:
            cursor = self.cursor()
            cursor.execute(query)

        except pymssql.MssqlException, e:
            cursor.close()
            self.db.rollback()
            raise db.ConnectorError(e.number, e.message)

        return cursor
