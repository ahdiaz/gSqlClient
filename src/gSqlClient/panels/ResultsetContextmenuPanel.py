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

from gi.repository import GObject, Gtk

from .. import utils

import gettext
from gettext import gettext as _
gettext.textdomain('gsqlclient')


class ResultsetContextmenuPanel(Gtk.Menu):

    def __init__(self, treeview, path, column):

        GObject.GObject.__init__(self)

        copy_cell_item = Gtk.MenuItem(_("Copy cell value"))
        copy_row_item = Gtk.MenuItem(_("Copy row value"))
        export_sql = Gtk.MenuItem(_("Export as SQL"))
        export_xml = Gtk.MenuItem(_("Export as XML"))
        export_csv = Gtk.MenuItem(_("Export as CSV"))

        self.append(copy_cell_item)
        self.append(copy_row_item)
        self.append(export_sql)
        self.append(export_xml)
        self.append(export_csv)

        copy_cell_item.connect("activate", treeview.cell_value_to_clipboard, path, column)
        copy_row_item.connect("activate", treeview.row_value_to_clipboard, path)
        export_sql.connect("activate", treeview.export_grid, utils.Exporter.FORMAT_SQL)
        export_xml.connect("activate", treeview.export_grid, utils.Exporter.FORMAT_XML)
        export_csv.connect("activate", treeview.export_grid, utils.Exporter.FORMAT_CSV)

        self.show_all()

    def popup(self, event):
        Gtk.Menu.popup(self, None, None, None, None, event.button, event.time)
