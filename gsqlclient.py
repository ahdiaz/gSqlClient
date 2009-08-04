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
import gedit
import gtk
import gtk.glade
import MySQLdb

class GSqlClientPlugin(gedit.Plugin):
	
	def __init__(self):
		gedit.Plugin.__init__(self)

	def activate(self, window):
		""" Activate plugin. """

		callback = self._on_window_tab_added
		id_1 = window.connect("tab-added", callback)
		callback = self._on_window_tab_removed
		id_2 = window.connect("tab-removed", callback)
		window.set_data(self.__class__.__name__, (id_1, id_2))
		 
		views = window.get_views()
		for view in views:
			self._connect_view(view, window)
    
	def deactivate(self, window):
		""" Deactivate plugin. """
		
		widgets.extend(window.get_views())
		name = self.__class__.__name__
		for widget in widgets:
			for handler_id in widget.get_data(name):
				widget.disconnect(handler_id)
			widget.set_data(name, None)

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
		
		panel = window.get_bottom_panel()
		sw = tab.get_view().get_data('resultset_panel')
		panel.remove_item(sw)

	def _connect_view(self, view, window):
		""" Connect to view's editing signals. """

		callback = self._on_view_key_press_event
		id_1 = view.connect("key-press-event", callback, window)
		view.set_data(self.__class__.__name__, (id_1))

	def _on_view_key_press_event(self, view, event, window):
		""" Manage key events actions. """
		
		if not (event.state & gtk.gdk.CONTROL_MASK):
			return False

		# CTRL + Return
		if event.keyval == gtk.keysyms.Return:
			self._db_query(view, window)
			return True
		
		if  not (event.state & gtk.gdk.MOD1_MASK):
			return False
		
		# CTRL + ALT + C
		if event.keyval == gtk.keysyms.c:			
			self._db_connect(view, window)			
			return True
		
		return False
	
	def _db_connect(self, view, window):
	
		db = view.get_data('db_connection')
		
		gladeFile = os.path.join(os.path.dirname(__file__), "gsqlclient.glade")
		self.tree = gtk.glade.XML(gladeFile)
		self.tree.signal_autoconnect(self)
		self._dialog = self.tree.get_widget('connectionDialog')
		self._dialog.set_transient_for(window)
		if db is None:
			self.tree.get_widget('btnDisconnect').hide()
		
		result = self._dialog.run()
						
		if result == 1:
			host = self.tree.get_widget('txtHost').get_text()
			user = self.tree.get_widget('txtUser').get_text()
			passwd = self.tree.get_widget('txtPassword').get_text()
			schema = self.tree.get_widget('txtSchema').get_text()
			
			if db is not None:
				self._db_disconnect(view, window)
				
			db = MySQLdb.connect(host=host, user=user, passwd=passwd, db=schema)
			view.set_data('db_connection', db)
			self._create_resultset_view(view, window)
			
		if result == 2 and db is not None:
			self._db_disconnect(view, window)
			
		self._dialog.destroy()
	
	def _db_disconnect(self, view, window):
	
		db = view.get_data('db_connection')
		if db is not None:
			db.close()
			self._destroy_resultset_view(view, window)
			view.set_data('db_connection', None)

	def _db_query(self, view, window):
		""" Executes a SQL query """

		db = view.get_data('db_connection')
		if db is None: return
		
		query = self._get_query(view)		
		cursor = db.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute(query)		
		self._prepare_resultset_view(view, window, cursor)
		
		cursor.close()

	def _get_query(self, view):
		
		buff = view.get_buffer()
		selection = buff.get_selection_bounds()
		if len(selection) == 0:
			its = buff.get_iter_at_mark(buff.get_insert())
			ite = its.copy()
			its.set_line_offset(0)
			ite.forward_to_line_end()
			selection = (its, ite)

		its = selection[0]
		ite = selection[1]
		query = its.get_text(ite)
		
		return query

	def _prepare_resultset_view(self, view, window, cursor):

		sw = view.get_data('resultset_panel')
		panel = window.get_bottom_panel()
		panel.set_property("visible", True)
		panel.activate_item(sw)		
		treeview = sw.get_children()
		treeview = treeview[0]
		treeview.set_model(None)

		cols = len(treeview.get_columns())
		while (cols > 0):
			 cols = treeview.remove_column(treeview.get_column(0))
		
		column_names = []
		column_types = []
		new_model = None
		
		while (1):
			row = cursor.fetchone()
			if row == None:
				break
#			print row, row.values()
			if new_model == None:
				for key, value in row.iteritems():
					column_names.append(key)
					column_types.append(str)
				column_types = tuple(column_types)
				new_model = gtk.ListStore(*column_types)
			
			new_model.append(row.values())

		
		tvcolumn = [None] * len(column_names)
		for n in range(0, len(column_names)):
			cell = gtk.CellRendererText()
			tvcolumn[n] = gtk.TreeViewColumn(column_names[n], cell, text=n+1)
			tvcolumn[n].set_data('column_id', n)
			tvcolumn[n].set_cell_data_func(cell, self.field_value)
			treeview.append_column(tvcolumn[n])
		
		treeview.set_model(new_model)
		treeview.show_all()

	def field_value(self, column, cell, model, iter):
		pos = column.cell_get_position(cell)
		cell.set_property('text', model.get_value(iter, column.get_data('column_id')))
		return

	def _create_resultset_view(self, view, window):

		sw = gtk.ScrolledWindow()
		sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		
		treeview = gtk.TreeView()		
		sw.add(treeview)
		sw.show_all()

		view.set_data('resultset_panel', sw)

		panel = window.get_bottom_panel()
		panel.add_item(sw, 'Resultset', gtk.Image())

	def _destroy_resultset_view(self, view, window):
		sw = view.get_data('resultset_panel')
		panel = window.get_bottom_panel()
		panel.remove_item(sw)
		sw.destroy()
