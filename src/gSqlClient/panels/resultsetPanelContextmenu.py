
class ResultsetContextmenu(Gtk.Menu):

    def __init__(self, treeview, path, column):

        gtk.Menu.__init__(self)

        copy_cell_item = gtk.MenuItem(_("Copy cell value"))
        copy_row_item = gtk.MenuItem(_("Copy row value"))
        export_sql = gtk.MenuItem(_("Export as SQL"))
        export_xml = gtk.MenuItem(_("Export as XML"))
        export_csv = gtk.MenuItem(_("Export as CSV"))

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
        gtk.Menu.popup(self, None, None, None, event.button, event.time)
