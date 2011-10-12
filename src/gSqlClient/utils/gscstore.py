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

import os
import pickle

class GSCStore:

    def __init__(self):

        self.PROTOCOL = pickle.HIGHEST_PROTOCOL
        self.CONNECTIONS = "connections"
        self.SHORTCUTS = "shortcuts"

        self.data = {}

        self.file_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'gscstore.pickle')

        if os.path.isfile(self.file_path):
            self.load_data()
        else:
            data = {self.CONNECTIONS: [], self.SHORTCUTS: []}
            self.set_data(data)
            self.save_data()

    def load_data(self):
        fp = open(self.file_path, "rb")
        data = pickle.load(fp)
        fp.close()
        self.data = data

    def save_data(self):
        fp = open(self.file_path, "wb")
        pickle.dump(self.data, fp, self.PROTOCOL)
        fp.close()

    def get_data(self):
        return self.data

    def set_data(self, data):
        self.data = data

    def get_connections(self):
        data = self.get_data()
        data = data[self.CONNECTIONS]
        return data

    def set_connections(self, connections):
        data = self.get_data()
        data[self.CONNECTIONS] = connections
        self.set_data(data)

    def get_shortcuts(self):
        data = self.get_data()
        data = data[self.SHORTCUTS]
        return data

    def set_shortcuts(self, shortcuts):
        data = self.get_data()
        data[self.SHORTCUTS] = shortcuts
        self.set_data(data)
