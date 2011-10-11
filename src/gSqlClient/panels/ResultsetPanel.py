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
# $Id: panels.py 62 2011-08-18 23:53:03Z ahdiaz $
#

import os
from gi.repository import GObject, Gtk, GdkPixbuf

from .. import utils
from .. import exporter
from .. import dialogs
from .. panels.ResultsetTreeviewPanel import ResultsetTreeviewPanel


class ResultsetPanel(Gtk.HBox):

    def __init__(self, panel):

        GObject.GObject.__init__(self)
        self._panel = panel

        image = Gtk.Image()
        pxb = GdkPixbuf.Pixbuf.new_from_file(utils.get_media_file('db.png'))
        pxb = pxb.scale_simple(16, 16, GdkPixbuf.InterpType.BILINEAR)
        image.set_from_pixbuf(pxb)

        # TODO: What are the parameters of add_item?
        panel.add_item(self, '?', 'Resultset', image)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(utils.get_ui_file('ResultsetPanel'))
        self.builder.connect_signals(self)
        self.dialog = self.builder.get_object('ResultsetPanel')

        vbox1 = self.builder.get_object("resultset-vbox1")
        vbox1.reparent(self)

        self.rset_panel = self.builder.get_object("resultset-vbox3")
        self.rset_panel.hide()
        self.info_panel = self.builder.get_object("resultset-sw2")
        self.info_panel.hide()

        self.treeview = self.builder.get_object("treeviewResultset")
        self.text_info = self.builder.get_object("textviewQueryInfo")
        self.text_error = self.builder.get_object("textviewErrorInfo")

        sw = self.builder.get_object("resultset-sw1")
        sw.remove(self.treeview)
        self.treeview.destroy()
        self.treeview = ResultsetTreeviewPanel()
        sw.add(self.treeview)

    def activate(self):
        self._panel.set_property("visible", True)
        self._panel.activate_item(self)

    def clear_resultset(self):
        self.treeview.clear_treeview()
        buff = self.text_info.get_buffer()
        buff.set_text("")

    def show_resultset(self, cursor, execution_time):
        self.treeview.load_cursor(cursor)
        buff = self.text_info.get_buffer()
        buff.set_text(_("%s rows fetched in %s") % (cursor.rowcount, execution_time))
        self.info_panel.hide()
        self.rset_panel.show()
        self.activate()

    def clear_information(self):
        buff = self.text_error.get_buffer()
        buff.set_text("")

    def show_information(self, message):
        buff = self.text_error.get_buffer()
        buff.set_text(message)
        self.rset_panel.hide()
        self.info_panel.show()
        self.activate()

    def append_information(self, message):
        buff = self.text_error.get_buffer()
        it = buff.get_end_iter()
        buff.insert(it, "\n" + message)
        self.rset_panel.hide()
        self.info_panel.show()
        self.activate()
