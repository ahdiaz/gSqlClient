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
from gi.repository import GObject, Gtk, Gdk

from .. import exporter
from .. import dialogs
from .. panels.ResultsetContextmenuPanel import ResultsetContextmenuPanel

import gettext
from gettext import gettext as _
gettext.textdomain('gsqlclient')


class ResultsetTreeviewPanel(Gtk.TreeView):

    def __init__(self):
        GObject.GObject.__init__(self)
        self.set_grid_lines(Gtk.TreeViewGridLines.HORIZONTAL)
        self.connect("button_press_event", self._on_treeview_clicked)
        self._contextmenu = None
        self._exporter = exporter.Exporter()

    def clear_treeview(self):
        self.set_model(None)
        self.clear_columns()
        self.set_data("columns", 0)

    def clear_columns(self):
        cols = len(self.get_columns())
        while (cols > 0):
            cols = self.remove_column(self.get_column(0))

    def load_cursor(self, cursor):

        self.clear_treeview()

        column_types = []
        columns = len(cursor.description)
        self.set_data("columns", columns)
        tvcolumn = [None] * columns

        for n in range(0, columns):

            d = cursor.description[n]
            column_name = d[0].replace("_", "__")
            column_types.append(str)

            cell = Gtk.CellRendererText()
            cell.set_property("xpad", 3)
            tvcolumn[n] = Gtk.TreeViewColumn(column_name, cell, text=n + 1)
            tvcolumn[n].set_resizable(True)
            tvcolumn[n].set_data('column_id', n)
            tvcolumn[n].set_cell_data_func(cell, self._cell_value)
            self.append_column(tvcolumn[n])

        column_types = tuple(column_types)
        new_model = Gtk.ListStore(*column_types)

        while (1):
            row = cursor.fetchone()
            if row == None:
                break

            # TODO: Other way to transform data into strings?
            s_row = []
            for value in row:
                s_row.append(str(value))
            new_model.append(s_row)

        self.set_model(new_model)
        self.set_reorderable(False)
        self.show_all()

    def _cell_value(self, column, cell, model, iter, user_param):
        cell.set_property('text', model.get_value(iter, column.get_data('column_id')))

    def _on_treeview_clicked(self, treeview, event):

        if event.button != 3:
            return

        column = treeview.get_path_at_pos(int(event.x), int(event.y))

        if column is None:
            return

        path = column[0]
        column = column[1]

        if self._contextmenu is not None:
            self._contextmenu.destroy()

        self._contextmenu = ResultsetContextmenuPanel(treeview, path, column)
        self._contextmenu.popup(event)

    def _get_cell_value(self, treeview, path, column):

        row = self._get_row_value(treeview, path)
        column_id = column.get_data("column_id")
        return row[column_id]

    def _get_row_value(self, treeview, path):

        model = treeview.get_model()
        return model[path]

    def cell_value_to_clipboard(self, menuitem, path, column):

        """ self == treeview """
        self._contextmenu.destroy()
        value = self._get_cell_value(self, path, column)
        if value is None:
            value = "NULL"
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(value, -1)
        return value

    def row_value_to_clipboard(self, menuitem, path):

        """ self == treeview """
        self._contextmenu.destroy()

        _row = self._get_row_value(self, path)
        row = []
        for value in _row:
            if value is None:
                value = "NULL"
            row.append(value)

        value = '"%s"' % (str.join('"\t"', row).strip(" \t\r\n"))
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(value, -1)
        return value

    def export_grid(self, widget, format):

        _columns = self.get_columns()
        columns = []
        for c in range(0, len(_columns)):
            columns.append(_columns[c].get_title())

        chooser = Gtk.FileChooserDialog(
            title=None, action=Gtk.FileChooserAction.SAVE,
            buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        )
        chooser.run()
        filename = chooser.get_filename()
        chooser.destroy()

        if filename is None:
            return None

        if os.path.isfile(filename):

            file_dialog = dialogs.FileExistsDialog(_("File %s exists, overwrite?") % (filename,), None)
            file_dialog_ret = file_dialog.run()
            file_dialog.destroy()
            if file_dialog_ret == 0:
                return None

        exported = self._exporter.export(format, self.get_model(), columns)

        if exported == None:
            return None

        fp = open(filename, "w")
        fp.write(exported)
        fp.close()

        return exported
