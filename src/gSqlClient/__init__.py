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
import gedit
import gtk
import gtk.glade

import db
import panels
import dialogs

__gladeFile__ = os.path.join(os.path.dirname(__file__), 'gsqlclient.glade')

class GSqlClientPlugin(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
		self.dbpool = db.DbPool()
		self.qparser = db.QueryParser()

	def activate(self, window):
		""" Activate plugin. """

		self.window = window

		id_1 = window.connect("tab-added", self._on_window_tab_added)
		id_2 = window.connect("tab-removed", self._on_window_tab_removed)
		id_3 = window.connect("active-tab-changed", self._on_window_active_tab_changed)
		window.set_data(self.__class__.__name__, (id_1, id_2, id_3))

		views = window.get_views()
		for view in views:
			self._connect_view(view)

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

		views = window.get_views()
		for view in views:
			self._db_disconnect(view)

	def _on_window_tab_added(self, window, tab):
		""" Connect to signals of the view in tab. """

		name = self.__class__.__name__
		view = tab.get_view()
		handler_id = view.get_data(name)
		if handler_id is None:
			self._connect_view(view)

	def _on_window_tab_removed(self, window, tab):
		""" Disconnects signals of the view in tab."""

		self._db_disconnect(tab.get_view())

	def _on_window_active_tab_changed(self, window, tab):
		view = tab.get_view()
		sw = view.get_data('resultset_panel')
		if sw != None:
			sw.activate()

	def _connect_view(self, view):
		""" Connect to view's editing signals. """

		id_1 = view.connect("key-press-event", self._on_view_key_press_event)
		view.set_data(self.__class__.__name__, (id_1))

	def _on_view_key_press_event(self, view, event):
		""" Manage key events actions. """

		if not (event.state & gtk.gdk.CONTROL_MASK):
			return False

		# CTRL + Return
		if event.keyval == gtk.keysyms.Return:
			self._execute_query(view)
			return True

		if  not (event.state & gtk.gdk.MOD1_MASK):
			return False

		# CTRL + ALT + C
		if event.keyval == gtk.keysyms.c:
			self._db_connect(view)
			return True

		# CTRL + ALT + R
		if event.keyval == gtk.keysyms.r:
			self._execute_script(view)
			return True

		return False

	def _db_connect(self, view):

		dbc = view.get_data('dbc')

		d = dialogs.ConnectionDialog(__gladeFile__, self.window, self.dbpool)
		result, options = d.run(dbc)

		if result == 2:
			self._db_disconnect(view)
			
		elif result == 1:

			if dbc != None and dbc.is_connected():
				self._db_disconnect(view)

			dbc = db.get_connector(options)
			self.dbpool.append(dbc)

			try:

				dbc.connect()

				panel = self.window.get_bottom_panel()
				rset = panels.ResultsetPanel(__gladeFile__, panel)

				view.set_data('dbc', dbc)
				view.set_data('resultset_panel', rset)

			except db.Error, e:
				error_dialog = dialogs.ConnectionErrorDialog("\n  Error %d: %s  \n" % (e.errno, e.error), self.window)
				error_dialog.run()
				error_dialog.destroy()
				exit = False

			except Exception, e:
				error_dialog = dialogs.ConnectionErrorDialog("\n  %s  \n" % (e), self.window)
				error_dialog.run()
				error_dialog.destroy()
				exit = False

	def _db_disconnect(self, view):

		dbc = view.get_data('dbc')
		if dbc != None and dbc.is_connected():
			self.dbpool.remove(dbc)
			dbc.close()
			self._destroy_resultset_view(view)
			view.set_data('dbc', None)

	def _execute_query(self, view):

		sw = view.get_data('resultset_panel')
		if sw is not None:
			sw.clear_resultset()
			sw.clear_information()

		buff = view.get_buffer()
		self.qparser.set_buffer(buff)
		query = self.qparser.get_current_query()

		if query is not None:

			dbc = view.get_data('dbc')
			ret = dbc.execute(query)
			
#			print ret
			
			if not ret["executed"]:
				return

			if ret["errno"] != 0:
				sw.show_information("Error %s: %s" % (ret["errno"], ret["error"]))
				
			elif ret["selection"]:
				sw.show_resultset(ret["cursor"], ret["execution_time"])
				
			else:
				sw.show_information("%s rows affected in %s" % (ret["rowcount"], ret["execution_time"]))

			if ret["cursor"] is not None:
				ret["cursor"].close()

	def _execute_script(self, view):
		""" Run document as script """

		xmltree = gtk.glade.XML(__gladeFile__)
		script_dialog = xmltree.get_widget('scriptDialog')
		script_dialog.set_transient_for(self.window)
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
		self.qparser.set_buffer(buff)
		queries = self.qparser.get_all_queries()
		
		dbc = view.get_data('dbc')

		n = 1
		for query in queries:

			if len(query) == 0:
				continue

			ret = dbc.execute(query)

			if not ret["executed"]:
				continue

			if ret["cursor"] is not None:
				ret["cursor"].close()

			if ret["errno"] != 0:

				error_message = "\n(%s) - Error %s: %s" % (n, ret["errno"], ret["error"])
				sw.append_information(error_message)

				if rbAsk:

					error_dialog = dialogs.ScriptErrorDialog(error_message, self.window)
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

	def _destroy_resultset_view(self, view):
		sw = view.get_data('resultset_panel')
		panel = self.window.get_bottom_panel()
		panel.remove_item(sw)
		sw.destroy()
		view.set_data('resultset_panel', None)
