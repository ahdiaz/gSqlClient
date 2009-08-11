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

class GSqlClientPlugin(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)

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

		return False

	def _db_connect(self, view, window):

		gladeFile = os.path.join(os.path.dirname(__file__), "gsqlclient.glade")
		xmltree = gtk.glade.XML(gladeFile)
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
				host = xmltree.get_widget('txtHost').get_text()
				user = xmltree.get_widget('txtUser').get_text()
				passwd = xmltree.get_widget('txtPassword').get_text()
				schema = xmltree.get_widget('txtSchema').get_text()

				if db is not None:
					self._db_disconnect(view, window)

				try:
					db = MySQLdb.connect(host=host, user=user, passwd=passwd, db=schema)
					view.set_data('db_connection', db)
					panel = window.get_bottom_panel()
					rset = ResultsetPanel(panel)
					view.set_data('resultset_panel', rset)
					panel.add_item(rset, 'Resultset', gtk.Image())

				except MySQLdb.Error, e:
					error_dialog = gtk.Dialog(title="Connection error", parent=window, flags=gtk.DIALOG_MODAL, buttons=None)
					error_dialog.add_button("Close", gtk.RESPONSE_CLOSE)
					label = gtk.Label("\n  Error %d: %s  \n" % (e.args[0], e.args[1]))
					error_dialog.vbox.pack_start(label, True, True, 0)
					label.show()
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
		buff = view.get_buffer()
		q = QueryParser(buff)
		query = q.get_current_query()
		if query is not None:
			self._db_query(view, query)

	def _execute_script(self, view, window):
		""" Run document as script """

	def _db_query(self, view, query):
		""" Executes a SQL query """

		db = view.get_data('db_connection')
		if db is None: return

		sw = view.get_data('resultset_panel')
		cursor = db.cursor(MySQLdb.cursors.Cursor)
		try:
			t1 = time.time()
			cursor.execute(query)
			execution_time = time.time() - t1
			if cursor.description is not None:
				sw.show_resultset(cursor, execution_time)
			else:
				sw.show_information("%s rows affected in %s" % (cursor.rowcount, execution_time))
			cursor.close()
		except MySQLdb.Error, e:
			sw.show_information("Error %d: %s" % (e.args[0], e.args[1]))

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
		ite.forward_to_line_end()
		if its.get_line() != ite.get_line():
			return ""
		line = its.get_text(ite).strip()
		#print "\n(%s) - %s\n" % (len(line), line)
		#print "its = %s, ite = %s\n" % (its.get_line(), ite.get_line())
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
		while its.backward_line() and len(line) > 0:
			query.append(line)
			line = self.get_line(its)
		query.reverse()

		its = self._get_iter_at_cursor()
		while 1:
			cont = its.forward_line()
			line = self.get_line(its)
			if len(line) == 0:
				break
			query.append(line)
			if not cont:
				break

		query = str.join("\n", query).strip()
		if len(query) == 0:
			query = None
		#print query
		return query

	def get_all_queries(self):
		queries = ()

class ResultsetPanel(gtk.VBox):

	def __init__(self, panel):

		gtk.VBox.__init__(self)
		self._panel = panel

		self._treeview = ResultsetTreeView()
		self._treeview.set_grid_lines(gtk.TREE_VIEW_GRID_LINES_HORIZONTAL)

		self._textview1 = gtk.TextView()
		self._textview1.set_editable(False)
		self._textview1.set_left_margin(5)
		self._textview1.set_right_margin(5)

		self._sw = gtk.ScrolledWindow()
		self._sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self._sw.add(self._treeview)
		self._sw.show_all()

		self._textview2 = gtk.TextView()
		self._textview2.set_editable(False)
		self._textview1.set_left_margin(5)
		self._textview1.set_right_margin(5)

	def _clean(self):
		children = self.get_children()
		for child in children:
			self.remove(child)

	def _activate(self):
		self._panel.set_property("visible", True)
		self._panel.activate_item(self)

	def show_resultset(self, cursor, execution_time):
		self._clean()
		self._treeview.load_cursor(cursor)
		buff = self._textview1.get_buffer()
		buff.set_text("%s rows fetched in %s" % (cursor.rowcount, execution_time))
		self.pack_start(self._sw, True)
		self.pack_start(self._textview1, False)
		self.show_all()
		self._activate()

	def show_information(self, message):
		self._clean()
		buff = self._textview2.get_buffer()
		buff.set_text(message)
		self.add(self._textview2)
		self.show_all()
		self._activate()

class ResultsetTreeView(gtk.TreeView):

	def __init__(self):
		gtk.TreeView.__init__(self)

	def load_cursor(self, cursor):

		self.set_model(None)

		cols = len(self.get_columns())
		while (cols > 0):
			 cols = self.remove_column(self.get_column(0))

		column_types = []
		tvcolumn = [None] * len(cursor.description)

		for n in range(0, len(cursor.description)):

			d = cursor.description[n]
			column_name = d[0]
			column_types.append(str)

			cell = gtk.CellRendererText()
			cell.set_property("xpad", 10)
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
