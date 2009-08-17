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

""" This plugin enables Gedit as a MySQL client. """

import os
import time
import gedit
import gtk
import gtk.glade
import MySQLdb
from xml.dom.minidom import getDOMImplementation

class GSqlClientPlugin(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
		self._gladeFile = os.path.join(os.path.dirname(__file__), "gsqlclient.glade")

	def activate(self, window):
		""" Activate plugin. """

		id_1 = window.connect("tab-added", self._on_window_tab_added)
		id_2 = window.connect("tab-removed", self._on_window_tab_removed)
		window.set_data(self.__class__.__name__, (id_1, id_2))

		views = window.get_views()
		for view in views:
			self._connect_view(view, window)

	def deactivate(self, window):
		""" Deactivate plugin. """
		"""
		widgets.extend(window.get_views())
		name = self.__class__.__name__
		for widget in widgets:
			for handler_id in widget.get_data(name):
				widget.disconnect(handler_id)
			widget.set_data(name, None)
		"""

	def _on_window_tab_added(self, window, tab):
		""" Connect to signals of the view in tab. """

		name = self.__class__.__name__
		view = tab.get_view()
		handler_id = view.get_data(name)
		if handler_id is None:
			self._connect_view(view, window)

	def _on_window_tab_removed(self, window, tab):
		""" Disconnects signals of the view in tab."""

		self._db_disconnect(tab.get_view(), window)

	def _connect_view(self, view, window):
		""" Connect to view's editing signals. """

		id_1 = view.connect("key-press-event", self._on_view_key_press_event, window)
		view.set_data(self.__class__.__name__, (id_1))

	def _on_view_key_press_event(self, view, event, window):
		""" Manage key events actions. """

		if not (event.state & gtk.gdk.CONTROL_MASK):
			return False

		# CTRL + Return
		if event.keyval == gtk.keysyms.Return:
			self._execute_query(view, window)
			return True

		if  not (event.state & gtk.gdk.MOD1_MASK):
			return False

		# CTRL + ALT + C
		if event.keyval == gtk.keysyms.c:
			self._db_connect(view, window)
			return True

		# CTRL + ALT + R
		if event.keyval == gtk.keysyms.r:
			self._execute_script(view, window)
			return True

		return False

	def _db_connect(self, view, window):

		xmltree = gtk.glade.XML(self._gladeFile)
		xmltree.signal_autoconnect(self)
		connection_dialog = xmltree.get_widget('connectionDialog')
		connection_dialog.set_transient_for(window)

		db = view.get_data('db_connection')
		if db is None:
			xmltree.get_widget('btnDisconnect').hide()

		exit = False
		while not exit:
			result = connection_dialog.run()
			exit = True

			if result == 1:
				host = xmltree.get_widget('txtHost').get_text().strip()
				user = xmltree.get_widget('txtUser').get_text().strip()
				passwd = xmltree.get_widget('txtPassword').get_text().strip()
				schema = xmltree.get_widget('txtSchema').get_text().strip()

				if db is not None:
					self._db_disconnect(view, window)

				try:
					db = MySQLdb.connect(host=host, user=user, passwd=passwd, db=schema)
					view.set_data('db_connection', db)
					panel = window.get_bottom_panel()
					rset = ResultsetPanel(panel, xmltree)
					view.set_data('resultset_panel', rset)
					panel.add_item(rset, 'Resultset', gtk.Image())

				except MySQLdb.Error, e:
					error_dialog = ConnectionErrorDialog("\n  Error %d: %s  \n" % (e.args[0], e.args[1]), window)
					error_dialog.run()
					error_dialog.destroy()
					exit = False

			if result == 2 and db is not None:
				self._db_disconnect(view, window)

		connection_dialog.destroy()

	def _db_disconnect(self, view, window):

		db = view.get_data('db_connection')
		if db is not None:
			db.close()
			self._destroy_resultset_view(view, window)
			view.set_data('db_connection', None)

	def _execute_query(self, view, window):

		sw = view.get_data('resultset_panel')
		if sw is not None:
			sw.clear_resultset()
			sw.clear_information()

		buff = view.get_buffer()
		q = QueryParser(buff)
		query = q.get_current_query()

		if query is not None:

			ret = self._db_query(view, query)
			if not ret["executed"]:
				return

			if ret["errno"] != 0:
				sw.show_information("Error %d: %s" % (ret["errno"], ret["error"]))
			elif ret["selection"]:
				sw.show_resultset(ret["cursor"], ret["execution_time"])
				sw.get_treeview().set_data("last_query", query)
			else:
				sw.show_information("%s rows affected in %s" % (ret["rowcount"], ret["execution_time"]))

			if ret["cursor"] is not None:
				ret["cursor"].close()

	def _execute_script(self, view, window):
		""" Run document as script """

		xmltree = gtk.glade.XML(self._gladeFile)
		script_dialog = xmltree.get_widget('scriptDialog')
		script_dialog.set_transient_for(window)
		dialog_ret = script_dialog.run()

		rbStop = xmltree.get_widget('radiobuttonStop').get_active()
		rbAsk = xmltree.get_widget('radiobuttonAsk').get_active()
		rbIgnore = xmltree.get_widget('radiobuttonIgnore').get_active()

		script_dialog.destroy()
		if dialog_ret == 0:
			return

		sw = view.get_data('resultset_panel')
		if sw is not None:
			sw.clear_resultset()
			sw.clear_information()

		buff = view.get_buffer()
		q = QueryParser(buff)
		queries = q.get_all_queries()

		n = 1
		for query in queries:

			if len(query) == 0:
				continue

			ret = self._db_query(view, query)

			if not ret["executed"]:
				continue

			if ret["cursor"] is not None:
				ret["cursor"].close()

			if ret["errno"] != 0:

				error_message = "\n(%s) - Error %d: %s" % (n, ret["errno"], ret["error"])
				sw.append_information(error_message)

				if rbAsk:
					
					error_dialog = ScriptErrorDialog(error_message, window)
					error_dialog_ret = error_dialog.run()
					error_dialog.destroy()

					if error_dialog_ret == 1:
						rbAsk = False
						rbIgnore = True
					elif error_dialog_ret == 0:
						rbStop = True

				if rbStop:
					break

			elif ret["selection"]:
				sw.append_information("\n(%s) - %s rows fetched in %s" % (n, ret["rowcount"], ret["execution_time"]))
			else:
				sw.append_information("\n(%s) - %s rows affected in %s" % (n, ret["rowcount"], ret["execution_time"]))

			n = n + 1

	def _db_query(self, view, query):
		""" Executes a SQL query """

		result = {
			"executed": False,
			"errno": 0,
			"error": '',
			"rowcount": 0,
			"execution_time": None,
			"selection": False,
			"cursor": None,
			"description": None
		}

		db = view.get_data('db_connection')
		if db is None:
			return result

		result["executed"] = True
		cursor = db.cursor(MySQLdb.cursors.Cursor)
		try:
			t1 = time.time()
			cursor.execute(query)
			execution_time = time.time() - t1
			result["rowcount"] = cursor.rowcount
			result["execution_time"] = execution_time
			if cursor.description is not None:
				result["selection"] = True
				result["cursor"] = cursor
				result["description"] = cursor.description

		except MySQLdb.Error, e:
			result["errno"] = e.args[0]
			result["error"] = e.args[1]

		return result

	def _destroy_resultset_view(self, view, window):
		sw = view.get_data('resultset_panel')
		panel = window.get_bottom_panel()
		panel.remove_item(sw)
		sw.destroy()
		view.set_data('resultset_panel', None)

class QueryParser():

	def __init__(self, buffer):
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
		if len(line) == 0:
			return None

		while its.backward_line() and len(line) > 0:
			query.append(line)
			line = self.get_line(its)
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
		#print query
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

class ResultsetTreeView(gtk.TreeView):

	def __init__(self):
		gtk.TreeView.__init__(self)
		self.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)
		self.connect("button_press_event", self._on_treeview_clicked)
		self._contextmenu = None

	def clear_treeview(self):
		self.set_model(None)
		self.clear_columns()
		self.set_data("columns", 0)
		self.set_data("last_query", None)

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
			column_name = d[0]
			column_types.append(str)

			cell = gtk.CellRendererText()
			cell.set_property("xpad", 3)
			tvcolumn[n] = gtk.TreeViewColumn(column_name, cell, text=n+1)
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
		pos = column.cell_get_position(cell)
		cell.set_property('text', model.get_value(iter, column.get_data('column_id')))

	def _on_treeview_clicked(self, treeview, event):

		if event.button != 3:
			return

		columns = treeview.get_data("columns")
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

		# widget is a variable object
		
		_columns = self.get_columns()
		columns = []
		for c in range(0, len(_columns)):
			columns.append(_columns[c].get_title())

		chooser = gtk.FileChooserDialog(
			title=None,action=gtk.FILE_CHOOSER_ACTION_SAVE,
			buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK)
		)
		chooser.run()
		filename = chooser.get_filename()
		chooser.destroy()

		if filename is None:
			return None

		if os.path.isfile(filename):
			
			file_dialog = FileExistsDialog("File "+filename+" exists, overwrite?", None)
			file_dialog_ret = file_dialog.run()
			file_dialog.destroy()
			if file_dialog_ret == 0:
				return None
		
		re = ResultsetExport(self.get_model(), columns)
		if format == "xml":
			export = re.export_xml()
		elif format == "csv":
			export = re.export_csv()
		else:
			return None

		fp = open(filename, "w")
		fp.write(export)
		fp.close()
		
		return export

class ResultsetExport():

	def __init__(self, model, columns):
		self._model = model
		self._columns = columns

	def export_xml(self):

		impl = getDOMImplementation()
		#namespaceUri=None, qualifiedName="resultset", doctype=None
		doc = impl.createDocument(None, "resultset", None)
		root = doc.documentElement

		it = self._model.get_iter_first()
		while it is not None:

			row = doc.createElement("row")

			for c in range(0, len(self._columns)):
				column = self._columns[c]
				value = self._model[it][c]
				if value is None:
					value = "NULL"
				if type(value).__name__ != "str":
					value = str(value)
				field = doc.createElement("field")
				name = doc.createAttribute("name")
				name.value = column
				field.setAttributeNode(name)
				field.appendChild(doc.createTextNode(value))
				row.appendChild(field)

			root.appendChild(row)
			it = self._model.iter_next(it)

		xmlstr = doc.toxml()
		doc.unlink()
		return xmlstr

	def export_csv(self):

		csvstr = '"%s"\n' % (str.join('","', self._columns))
		it = self._model.get_iter_first()
		while it is not None:
			row = []
			_row = self._model[it]
			for value in _row:
				if value is None:
					value = "NULL"
				row.append(value)
			csvstr += '"%s"\n' % (str.join('","', row))
			it = self._model.iter_next(it)

		return csvstr

class ResultsetContextmenu(gtk.Menu):

	def __init__(self, treeview, path, column):

		gtk.Menu.__init__(self)

		# Create the menu items
		copy_cell_item = gtk.MenuItem("Copy cell value")
		copy_row_item = gtk.MenuItem("Copy row value")
		export_xml = gtk.MenuItem("Export as XML")
		export_csv = gtk.MenuItem("Export as CSV")

		# Add them to the menu
		self.append(copy_cell_item)
		self.append(copy_row_item)
		self.append(export_xml)
		self.append(export_csv)

		# Attach the callback functions to the activate signal
		copy_cell_item.connect("activate", treeview.cell_value_to_clipboard, path, column)
		copy_row_item.connect("activate", treeview.row_value_to_clipboard, path)
		export_xml.connect("activate", treeview.export_grid, "xml")
		export_csv.connect("activate", treeview.export_grid, "csv")

		# We do need to show menu items
		self.show_all()

	def popup(self, event):
		gtk.Menu.popup(self, None, None, None, event.button, event.time)

class ResultsetPanel(gtk.HBox):

	def __init__(self, panel, xmltree):

		gtk.HBox.__init__(self)
		self._panel = panel

		hbox = xmltree.get_widget("hboxContainer")

		vbox1 = xmltree.get_widget("resultset-vbox1")
		vbox1.reparent(self)

		self._rset_panel = xmltree.get_widget("resultset-vbox3")
		self._rset_panel.hide()
		self._info_panel = xmltree.get_widget("resultset-sw2")
		self._info_panel.hide()

		self._treeview = xmltree.get_widget("treeviewResultset")
		self._text_info = xmltree.get_widget("textviewQueryInfo")
		self._text_error = xmltree.get_widget("textviewErrorInfo")

		sw = xmltree.get_widget("resultset-sw1")
		sw.remove(self._treeview)
		self._treeview.destroy()
		self._treeview = ResultsetTreeView()
		sw.add(self._treeview)

	def get_treeview(self):
		return self._treeview

	def get_text_info(self):
		return self._text_info

	def get_text_error(self):
		return self._text_error

	def _activate(self):
		self._panel.set_property("visible", True)
		self._panel.activate_item(self)

	def clear_resultset(self):
		self._treeview.clear_treeview()
		buff = self._text_info.get_buffer()
		buff.set_text("")

	def show_resultset(self, cursor, execution_time):
		self._treeview.load_cursor(cursor)
		buff = self._text_info.get_buffer()
		buff.set_text("%s rows fetched in %s" % (cursor.rowcount, execution_time))
		self._info_panel.hide()
		self._rset_panel.show()
		self._activate()

	def clear_information(self):
		buff = self._text_error.get_buffer()
		buff.set_text("")

	def show_information(self, message):
		buff = self._text_error.get_buffer()
		buff.set_text(message)
		self._rset_panel.hide()
		self._info_panel.show()
		self._activate()

	def append_information(self, message):
		buff = self._text_error.get_buffer()
		it = buff.get_end_iter()
		buff.insert(it, "\n"+message)
		self._rset_panel.hide()
		self._info_panel.show()
		self._activate()

class ConnectionErrorDialog(gtk.Dialog):

	def __init__(self, message, parent=None):
		gtk.Dialog.__init__(self, title="Connection error", parent=parent, flags=gtk.DIALOG_MODAL, buttons=None)
		self.add_button("Close", gtk.RESPONSE_CLOSE)
		label = gtk.Label(message)
		self.vbox.pack_start(label, True, True, 0)
		label.show()

class ScriptErrorDialog(gtk.Dialog):

	def __init__(self, message, parent=None):
		gtk.Dialog.__init__(self, title="Script error", parent=parent, flags=gtk.DIALOG_MODAL, buttons=None)
		self.add_button("Ignore", 2)
		self.add_button("Ignore all", 1)
		self.add_button("Stop script", 0)
		label = gtk.Label(message)
		self.vbox.pack_start(label, True, True, 0)
		label.show()

class FileExistsDialog(gtk.Dialog):

	def __init__(self, message, parent=None):
		gtk.Dialog.__init__(self, title="File exists", parent=parent, flags=gtk.DIALOG_MODAL, buttons=None)
		self.add_button("Yes", 1)
		self.add_button("Cancel", 0)
		label = gtk.Label(message)
		self.vbox.pack_start(label, True, True, 0)
		label.show()
