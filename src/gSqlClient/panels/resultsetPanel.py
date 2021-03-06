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
from gi.repository import GObject, Gtk

import exporter
import dialogs

class ResultsetPanel(Gtk.HBox):

    def __init__(self, gladeFile, panel):

        gtk.HBox.__init__(self)
        self._panel = panel

        image = gtk.Image()
        pxb = gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.dirname(__file__), 'pixmaps/db.png'))
        pxb = pxb.scale_simple(16, 16, gtk.gdk.INTERP_BILINEAR)
        image.set_from_pixbuf(pxb)
        panel.add_item(self, 'Resultset', image)

        xmltree = gtk.glade.XML(gladeFile)

#        hbox = xmltree.get_widget("hboxContainer")

        vbox1 = xmltree.get_widget("resultset-vbox1")
        vbox1.reparent(self)

        self.rset_panel = xmltree.get_widget("resultset-vbox3")
        self.rset_panel.hide()
        self.info_panel = xmltree.get_widget("resultset-sw2")
        self.info_panel.hide()

        self.treeview = xmltree.get_widget("treeviewResultset")
        self.text_info = xmltree.get_widget("textviewQueryInfo")
        self.text_error = xmltree.get_widget("textviewErrorInfo")

        sw = xmltree.get_widget("resultset-sw1")
        sw.remove(self.treeview)
        self.treeview.destroy()
        self.treeview = ResultsetTreeView()
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
