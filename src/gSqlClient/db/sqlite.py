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


import sqlite3
from .. import db

class SQLiteConnector(db.Connector):

    def _get_options(self):

        options = {"database": self.schema}
        return options

    def update_connection_string(self):

        self.connection_string = '%s://%s' % (self.driver, self.schema)

    def connect(self):

        if self.db != None:
            return self.db

        try:
            options = self._get_options()
            self.db = sqlite3.connect(**options)

        except sqlite3.Error, e:
            raise db.ConnectorError(-1, e.args[0])

        return self.db

    def _execute(self, query):

        cursor = None

        try:
            cursor = self.cursor()
            cursor.execute(query)

        except sqlite3.Error, e:
            cursor.close()
            raise db.ConnectorError(-1, e.args[0])

        return cursor
