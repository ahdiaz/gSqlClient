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
