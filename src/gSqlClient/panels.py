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

import os
from gi.repository import GObject, Gtk

import exporter
import dialogs

class ResultsetPanel(Gtk.HBox):

    def __init__(self, gladeFile, panel):

        GObject.GObject.__init__(self)
        self._panel = panel

        image = Gtk.Image()
        pxb = GdkPixbuf.Pixbuf.new_from_file(os.path.join(os.path.dirname(__file__), 'pixmaps/db.png'))
        pxb = pxb.scale_simple(16, 16, GdkPixbuf.InterpType.BILINEAR)
        image.set_from_pixbuf(pxb)
        panel.add_item(self, 'Resultset', image)

        xmltree = Gtk.glade.XML(gladeFile)

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
        buff.set_text("%s rows fetched in %s" % (cursor.rowcount, execution_time))
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

class ResultsetTreeView(Gtk.TreeView):

    def __init__(self):
        GObject.GObject.__init__(self)
        self.set_grid_lines(Gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
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
            new_model.append(row)

        self.set_model(new_model)
        self.set_reorderable(False)
        self.show_all()

    def _cell_value(self, column, cell, model, iter):
        #pos = column.cell_get_position(cell)
        cell.set_property('text', model.get_value(iter, column.get_data('column_id')))

    def _on_treeview_clicked(self, treeview, event):

        if event.button != 3:
            return

        #columns = treeview.get_data("columns")
        column = treeview.get_path_at_pos(int(event.x), int(event.y))

        if column is None:
            return

        path = column[0]
        column = column[1]

        if self._contextmenu is not None:
            self._contextmenu.destroy()

        self._contextmenu = ResultsetContextmenu(treeview, path, column)
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
        clipboard = Gtk.clipboard_get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(value)
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
        clipboard = Gtk.clipboard_get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(value)
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

            file_dialog = dialogs.FileExistsDialog("File " + filename + " exists, overwrite?", None)
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

class ResultsetContextmenu(Gtk.Menu):

    def __init__(self, treeview, path, column):

        GObject.GObject.__init__(self)

        copy_cell_item = Gtk.MenuItem("Copy cell value")
        copy_row_item = Gtk.MenuItem("Copy row value")
        export_sql = Gtk.MenuItem("Export as SQL")
        export_xml = Gtk.MenuItem("Export as XML")
        export_csv = Gtk.MenuItem("Export as CSV")

        self.append(copy_cell_item)
        self.append(copy_row_item)
        self.append(export_sql)
        self.append(export_xml)
        self.append(export_csv)

        copy_cell_item.connect("activate", treeview.cell_value_to_clipboard, path, column)
        copy_row_item.connect("activate", treeview.row_value_to_clipboard, path)
        export_sql.connect("activate", treeview.export_grid, exporter.Exporter.FORMAT_SQL)
        export_xml.connect("activate", treeview.export_grid, exporter.Exporter.FORMAT_XML)
        export_csv.connect("activate", treeview.export_grid, exporter.Exporter.FORMAT_CSV)

        self.show_all()

    def popup(self, event):
        Gtk.Menu.popup(self, None, None, None, event.button, event.time)
