
class ResultsetTreeView(Gtk.TreeView):

    def __init__(self):
        gtk.TreeView.__init__(self)
        self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
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

            cell = gtk.CellRendererText()
            cell.set_property("xpad", 3)
            tvcolumn[n] = gtk.TreeViewColumn(column_name, cell, text=n + 1)
            tvcolumn[n].set_resizable(True)
            tvcolumn[n].set_data('column_id', n)
            tvcolumn[n].set_cell_data_func(cell, self._cell_value)
            self.append_column(tvcolumn[n])

        column_types = tuple(column_types)
        new_model = gtk.ListStore(*column_types)

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
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
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
        clipboard = gtk.clipboard_get(gtk.gdk.SELECTION_CLIPBOARD)
        clipboard.set_text(value)
        return value

    def export_grid(self, widget, format):

        _columns = self.get_columns()
        columns = []
        for c in range(0, len(_columns)):
            columns.append(_columns[c].get_title())

        chooser = gtk.FileChooserDialog(
            title=None, action=gtk.FILE_CHOOSER_ACTION_SAVE,
            buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
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
