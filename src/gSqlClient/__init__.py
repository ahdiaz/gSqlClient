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
from gi.repository import GObject, Gtk, Gdk, Gedit

import db
import panels
import dialogs


__gladeFile__ = os.path.join(os.path.dirname(__file__), 'gsqlclient.glade')

class GSqlClientPlugin(GObject.Object, Gedit.WindowActivatable):
    
    __gtype_name__ = "GSqlClientPlugin"

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self.gsc = GSqlClient(self.window)

    def do_activate(self):
        """
        Connect the needed signals for the window
        and connect the current views.
        """

        handler_id_1 = self.window.connect("tab-added", self._on_tab_added)
        handler_id_2 = self.window.connect("tab-removed", self._on_tab_removed)
        handler_id_3 = self.window.connect("active-tab-changed", self._on_active_tab_changed)
        
        self.window.set_data(self.__gtype_name__, (handler_id_1, handler_id_2, handler_id_3))

        views = self.window.get_views()
        for view in views:
            self._connect_view(view)

    def do_deactivate(self):
        """ Disconnect the window signals and current views. """
        
        for handler_id in self.window.get_data(self.__gtype_name__):
            self.window.disconnect(handler_id)
        
        self.window.set_data(self.__gtype_name__, None)

        views = self.window.get_views()
        for view in views:
            self._disconnect_view(view)

    def do_update_state(self):
        pass
    
    def _on_tab_added(self, window, tab, data=None):
        """ Connect the new view. """
        
        view = tab.get_view()
        self._connect_view(view)
        
        self.gsc.on_tab_added(window, tab, data)
    
    def _on_tab_removed(self, window, tab, data=None):
        """ Disconnect the view. """
        
        view = tab.get_view()
        self._disconnect_view(view)
        
        self.gsc.on_tab_removed(window, tab, data)
    
    def _on_active_tab_changed(self, window, tab, data=None):
        
        self.gsc.on_active_tab_changed(window, tab, data)
    
    def _connect_view(self, view):
        """ Connect the needed view signals. """
        
        handler_id = view.get_data(self.__gtype_name__)
        
        if handler_id is None:
            handler_id = view.connect("key-press-event", self._on_key_press_event)
            view.set_data(self.__gtype_name__, (handler_id))
        
        self.gsc.on_connect_view(view)
    
    def _disconnect_view(self, view):
        """ Disconnect the view signals. """
        
        handler_id = view.get_data(self.__gtype_name__)
        
        if handler_id is not None:
            view.disconnect(handler_id)
            view.set_data(self.__gtype_name__, None)
        
        self.gsc.on_disconnect_view(view)
    
    def _on_key_press_event(self, view, event):
        """ Fired when we press any key on a view. """
        
        self.gsc.on_key_press_event(view, event)
    

class GSqlClient():
    
    def __init__(self, window):
        self.window = window
        self.dbpool = db.DbPool()
        self.qparser = db.QueryParser()

    def on_tab_added(self, window, tab, data=None):
        pass

    def on_tab_removed(self, window, tab, data=None):
        pass

    def on_active_tab_changed(self, window, tab, data=None):
        view = tab.get_view()
        sw = view.get_data('resultset_panel')
        if sw != None:
            sw.activate()

    def on_connect_view(self, view):
        pass
        
    def on_disconnect_view(self, view):

        self._db_disconnect(view)        

    def on_key_press_event(self, view, event):
        """ Manage key events actions. """
        
        if not (event.state & Gdk.ModifierType.CONTROL_MASK):
            return False

        # CTRL + Return
        # Execute a SQL sentence
        if event.keyval == Gdk.KEY_Return:
            self._execute_query(view)
            return True

        if  not (event.state & Gdk.ModifierType.SHIFT_MASK):
            return False

        # CTRL + SHIFT + C
        # Show the connection dialog
        if event.keyval == Gdk.KEY_C:
            self._db_connect(view)
            return True

        # CTRL + SHIFT + R
        # Run the current document as a SQL script
        if event.keyval == Gdk.KEY_R:
            self._execute_script(view)
            return True

        return False

    def _db_connect(self, view):

        dbc = view.get_data('dbc')

        d = dialogs.ConnectionDialog(self.window, __gladeFile__, self.dbpool)
        result, new_dbc = d.run(dbc)

        if result == 2:
            self._db_disconnect(view)
            
        elif result == 1:

            self._db_disconnect(view)
            dbc = new_dbc

            try:

                dbc.connect()
                self.dbpool.append(dbc)

                panel = self.window.get_bottom_panel()
                rset = panels.ResultsetPanel(__gladeFile__, panel)

                view.set_data('dbc', dbc)
                view.set_data('resultset_panel', rset)

            except Exception, e:
                error_dialog = dialogs.ConnectionErrorDialog("\n  %s  \n" % (str(e)), self.window)
                error_dialog.run()
                error_dialog.destroy()

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

            try:
                dbc = view.get_data('dbc')
                ret = dbc.execute(query)
            
#                print ret
                
                if ret["selection"]:
                    sw.show_resultset(ret["cursor"], ret["execution_time"])
                    
                else:
                    sw.show_information("%s rows affected in %s" % (ret["rowcount"], ret["execution_time"]))
    
                if ret["cursor"] is not None:
                    ret["cursor"].close()

            except db.ConnectorError, e:
                sw.show_information("%s" % (str(e)))

            except Exception, e:
                pass
            
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

            try:
                ret = dbc.execute(query)
    
                if ret["cursor"] is not None:
                    ret["cursor"].close()
        
                if ret["selection"]:
                    sw.append_information("\n(%s) - %s rows fetched in %s" % (n, ret["rowcount"], ret["execution_time"]))
                    
                else:
                    sw.append_information("\n(%s) - %s rows affected in %s" % (n, ret["rowcount"], ret["execution_time"]))

            except db.ConnectorError, e:
                error_message = "\n(%s) - %s" % (n, str(e))
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

            except Exception, e:
                pass
            
            n = n + 1

    def _destroy_resultset_view(self, view):
        sw = view.get_data('resultset_panel')
        panel = self.window.get_bottom_panel()
        panel.remove_item(sw)
        sw.destroy()
        view.set_data('resultset_panel', None)

    
