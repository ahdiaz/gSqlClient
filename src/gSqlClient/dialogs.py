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
import pickle
from gi.repository import GObject, Gtk

import db

class ConnectionDialog:
    
    def __init__(self, window, glade_file, dbpool):
        
        self.gstore = GSCStore()
        self.dbpool = dbpool
        self.selected = None
        
        xmltree = gtk.glade.XML(glade_file, "connectionDialog_2")
        xmltree.signal_autoconnect(self)
        
        self.dialog = xmltree.get_widget("connectionDialog_2")
        self.dialog.set_transient_for(window)
        
        self.cmbDriver = xmltree.get_widget("cmbDriver")
        self.lblHost = xmltree.get_widget("lblHost")
        self.txtHost = xmltree.get_widget("txtHost")
        self.lblPort = xmltree.get_widget("lblPort")
        self.txtPort = xmltree.get_widget("txtPort")
        self.lblSocket = xmltree.get_widget("lblSocket")
        self.txtSocket = xmltree.get_widget("txtSocket")
        self.lblUser = xmltree.get_widget("lblUser")
        self.txtUser = xmltree.get_widget("txtUser")
        self.lblPasswd = xmltree.get_widget("lblPassword")
        self.txtPasswd = xmltree.get_widget("txtPassword")
        self.lblSchema = xmltree.get_widget("lblSchema")
        self.txtSchema = xmltree.get_widget("txtSchema")
        self.treeview = xmltree.get_widget("tvConnections")
        
        self.btnAdd = xmltree.get_widget("btnAdd")
        self.btnRemove = xmltree.get_widget("btnRemove")
        self.btnSave = xmltree.get_widget("btnSave")
        self.btnConnect = xmltree.get_widget("btnConnect")
        self.btnDisconnect = xmltree.get_widget("btnDisconnect")
        
        self.load_drivers()
        self.init_treeview()
    
    def run(self, active_connection):
        
        cnn = None
        result = self.dialog.run()

        if result == 1:
            try:
                options = self.get_options()
                cnn = db.get_connector(options)
            
            except db.InvalidConnectorError, e:
                pass
        
        self.dialog.destroy()
        return result, cnn
    
    def load_drivers(self):
        
        model = self.cmbDriver.get_model()
        model.clear()
        
        model.append([db.__DB_NONE__])
        
        try:
            import MySQLdb
            model.append([db.__DB_MYSQL__])
        except ImportError, e:
            print "ImportError: " + str(e)
        
        try:
            import sqlite3
            model.append([db.__DB_SQLITE__])
        except ImportError, e:
            print "ImportError: " + str(e)
        
        try:
            import psycopg2
            model.append([db.__DB_POSTGRE__])
        except ImportError, e:
            print "ImportError: " + str(e)
        
        try:
            import pymssql
            model.append([db.__DB_SQLSERVER__])
        except ImportError, e:
            print "ImportError: " + str(e)
        
        self.cmbDriver.set_model(model)
    
    def init_treeview(self):
        
        # create a CellRendererText to render the data
        cell = gtk.CellRendererText()
        
        # create the TreeViewColumn to display the data
        tvcolumn = gtk.TreeViewColumn('Connections')
        
        # add the cell to the tvcolumn and allow it to expand
        tvcolumn.pack_start(cell, True)
        
        # function for showing the cell text
        tvcolumn.set_cell_data_func(cell, self._cell_value)
        
        # add tvcolumn to treeview
        self.treeview.append_column(tvcolumn)
        
        # set the cell "text" attribute to column 0 - retrieve text
        # from that column in treestore
        tvcolumn.add_attribute(cell, 'text', 0)
        
        # make it searchable
        self.treeview.set_search_column(0)
        
        # Allow sorting on the column
        tvcolumn.set_sort_column_id(0)
        
        # Allow drag and drop reordering of rows
        self.treeview.set_reorderable(True)
        
        # create a TreeStore with one string column to use as the model
        treestore = gtk.TreeStore(object)
        
        # update the model
        self.treeview.set_model(treestore)
        
        # update the model
        self.update_treeview()

    def _cell_value(self, column, cell, model, iter):
        cnn = model.get_value(iter, 0)
        cell.set_property('text', cnn.get_connection_string())
    
    def update_treeview(self):
        
        # clear the model
        treestore = self.treeview.get_model()
        treestore.clear()
        
        # add the stored connections
        cnn = db.DummyConnector('Stored')
        self.stored = treestore.append(None, [cnn])
        
        connections = self.gstore.get_connections()
        for connection in connections: 
            treestore.append(self.stored, [connection])
        
        # add the active connections
        cnn = db.DummyConnector('Opened')
        self.opened = treestore.append(None, [cnn])
        
        cnn = db.DummyConnector('(Open new connection)')
        treestore.append(self.opened, [cnn])
        
        for key in self.dbpool.keys():
            cnn = self.dbpool.get(key) 
            treestore.append(self.opened, [cnn])
        
        # update the model
        self.treeview.set_model(treestore)
        
        # expand all nodes
        self.treeview.expand_all()
    
    def update_selected_row(self):
        
        if not self.is_stored_connection(self.selected):
            return
        
        options = self.get_options()
        
        try:
            cnn = db.get_connector(options)
            model = self.treeview.get_model()
            model.set_value(self.selected, 0, cnn)
            
            self.save_connections()
        
        except db.InvalidConnectorError, e:
            pass
    
    def get_options(self):
        
        # Normalized options
        options = {
            "driver": self.cmbDriver.get_active_text(),
            "host": self.txtHost.get_text(),
            "port": self.txtPort.get_text(),
            "socket": self.txtSocket.get_text(),
            "user": self.txtUser.get_text(),
            "passwd": self.txtPasswd.get_text(),
            "schema": self.txtSchema.get_text()
        }
        
        return options
    
    def update_form(self):
        
        try:
            model = self.treeview.get_model()
            cnn = model.get_value(self.selected, 0)
            self.combo_set_active_by_value(self.cmbDriver, cnn.get_driver())
            self.txtHost.set_text(cnn.get_host())
            self.txtPort.set_text(cnn.get_port())
            self.txtSocket.set_text(cnn.get_socket())
            self.txtUser.set_text(cnn.get_user())
            self.txtPasswd.set_text(cnn.get_passwd())
            self.txtSchema.set_text(cnn.get_schema())
        
        except Exception, e:
            self.combo_set_active_by_value(self.cmbDriver, db.__DB_NONE__)
            self.txtHost.set_text("")
            self.txtPort.set_text("")
            self.txtSocket.set_text("")
            self.txtUser.set_text("")
            self.txtPasswd.set_text("")
            self.txtSchema.set_text("")
        
    def combo_set_active_by_value(self, combo, value):
        # Set the active index by value
        model = combo.get_model()
        for index in range(0, len(model)):
            row = model[index]
            if row[0] == value:
                combo.set_active(index)
                break
    
    def on_cmbDriver_changed(self, widget):
        
        self.update_selected_row()
        
        driver = self.cmbDriver.get_active_text()
        if not self.is_stored_connection(self.selected):
            self.txtPort.set_text(str(db.get_default_port(driver)))
            self.btnSave.set_sensitive(driver != db.__DB_NONE__)
        
        self.btnConnect.set_sensitive(driver != db.__DB_NONE__)
        
        if driver == db.__DB_SQLITE__:
            self.lblHost.hide()
            self.txtHost.hide()
            self.lblPort.hide()
            self.txtPort.hide()
            self.lblSocket.hide()
            self.txtSocket.hide()
            self.lblUser.hide()
            self.txtUser.hide()
            self.lblPasswd.hide()
            self.txtPasswd.hide()
        
        else:
            self.lblHost.show()
            self.txtHost.show()
            self.lblPort.show()
            self.txtPort.show()
            self.lblSocket.show()
            self.txtSocket.show()
            self.lblUser.show()
            self.txtUser.show()
            self.lblPasswd.show()
            self.txtPasswd.show()
    
    def on_txtHost_changed(self, widget):
        self.update_selected_row()
    
    def on_txtPort_changed(self, widget):
        self.update_selected_row()
    
    def on_txtSocket_changed(self, widget):
        self.update_selected_row()
    
    def on_txtUser_changed(self, widget):
        self.update_selected_row()
    
    def on_txtPassword_changed(self, widget):
        self.update_selected_row()
    
    def on_txtSchema_changed(self, widget):
        self.update_selected_row()
    
    def is_stored_connection(self, iter):
        
        ret = False
        model = self.treeview.get_model()
        
        try:
            parent = model.iter_parent(iter)
            parent_path = model.get_path(parent)
            stored_path = model.get_path(self.stored)
            if parent_path == stored_path:
                ret = True
        
        except Exception, e:
            pass
        
        return ret
    
    def is_opened_connection(self, iter):
        
        ret = False
        model = self.treeview.get_model()
        
        try:
            parent = model.iter_parent(iter)
            parent_path = model.get_path(parent)
            opened_path = model.get_path(self.opened)
            if parent_path == opened_path:
                cnn = model.get_value(iter, 0)
                ret = isinstance(cnn, db.Connector)
        
        except Exception, e:
            pass
        
        return ret
    
    def on_btnSave_clicked(self, widget):
        
        options = self.get_options()
        
        try:
            cnn = db.get_connector(options)
            treestore = self.treeview.get_model()
            new_connection = treestore.append(self.stored, [cnn])
            treeselection = self.treeview.get_selection()
            treeselection.select_path(treestore.get_path(new_connection))
            self.on_tvConnections_cursor_changed(self.treeview)
            
            self.save_connections()
        
        except db.InvalidConnectorError, e:
            pass
    
    def on_btnDisconnect_clicked(self, widget):
        model = self.treeview.get_model()
        cnn = model.get_value(self.selected, 0)
        model.remove(self.selected)
        self.dbpool.remove(cnn)
        cnn.close()
        cnn = None
        self.selected = None
        self.btnDisconnect.set_sensitive(False)
        self.update_form()
    
    def on_btnAdd_clicked(self, widget):
        # Append a new row and expand the treeview,
        # then select the new connection and update the options
        treestore = self.treeview.get_model()
        new_connection = treestore.append(self.stored, ['New connection'])
        self.treeview.expand_row(treestore.get_path(self.stored), False)
        treeselection = self.treeview.get_selection()
        treeselection.select_path(treestore.get_path(new_connection))
        self.update_form()
    
    def on_btnRemove_clicked(self, widget):
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        
        if self.is_stored_connection(iter):
            model.remove(iter)
            self.selected = None
            self.btnRemove.set_sensitive(False)
            self.btnSave.set_sensitive(False)
            self.btnDisconnect.set_sensitive(False)
            self.update_form()
    
    def on_tvConnections_cursor_changed(self, treeview):
        
        treeselection = self.treeview.get_selection()
        (model, iter) = treeselection.get_selected()
        
        self.btnRemove.set_sensitive(False)
        self.btnSave.set_sensitive(False)
        self.btnConnect.set_sensitive(False)
        self.btnDisconnect.set_sensitive(False)
        self.selected = None
        
        if self.is_stored_connection(iter):
            self.btnRemove.set_sensitive(True)
            self.btnConnect.set_sensitive(True)
            self.selected = iter
        
        if self.is_opened_connection(iter):
            self.btnDisconnect.set_sensitive(True)
            self.btnConnect.set_sensitive(True)
            self.selected = iter
        
        self.update_form()
    
    def save_connections(self):
        treestore = self.treeview.get_model()
        treeiter = treestore.iter_children(self.stored)
        connections = []
        while treeiter != None:
            cnn = treestore.get_value(treeiter, 0)
            connections.append(cnn)
            treeiter = treestore.iter_next(treeiter)
        self.gstore.set_connections(connections)
        self.gstore.save_data()

class GSCStore:
    
    def __init__(self):
        
        self.PROTOCOL = pickle.HIGHEST_PROTOCOL
        self.CONNECTIONS = "connections"
        self.SHORTCUTS = "shortcuts"
        
        self.data = {}
        
        self.file_path = os.path.join(os.path.dirname(__file__), "gscstore.pickle")
        if os.path.isfile(self.file_path):
            self.load_data()
        else:
            data = {self.CONNECTIONS: [], self.SHORTCUTS: []}
            self.set_data(data)
            self.save_data()
    
    def load_data(self):
        fp = open(self.file_path, "rb")
        data = pickle.load(fp)
        fp.close()
        self.data = data
    
    def save_data(self):
        fp = open(self.file_path, "wb")
        pickle.dump(self.data, fp, self.PROTOCOL)
        fp.close()
    
    def get_data(self):
        return self.data
    
    def set_data(self, data):
        self.data = data
    
    def get_connections(self):
        data = self.get_data()
        data = data[self.CONNECTIONS]
        return data
    
    def set_connections(self, connections):
        data = self.get_data()
        data[self.CONNECTIONS] = connections
        self.set_data(data)
    
    def get_shortcuts(self):
        data = self.get_data()
        data = data[self.SHORTCUTS]
        return data
    
    def set_shortcuts(self, shortcuts):
        data = self.get_data()
        data[self.SHORTCUTS] = shortcuts
        self.set_data(data)

class ConnectionDialog_old():

    def __init__(self, gladeFile, window, dbpool):

        self.xmltree = gtk.glade.XML(gladeFile, 'connectionDialog')
        self.window = window
        self.dbpool = dbpool

    def run(self, dbc):

        dic = {
            "on_cmbReuse_changed": self.on_reuse_changed,
            "on_cmbDriver_changed": self.on_driver_changed
        }
        self.xmltree.signal_autoconnect(dic)

        self.dialog = self.xmltree.get_widget('connectionDialog')
        self.dialog.set_transient_for(self.window)

        self.cmbReuse = self.xmltree.get_widget('cmbReuse')
        self.set_reuse_options()

        self.cmbDriver = self.xmltree.get_widget('cmbDriver')
        self.lblHost = self.xmltree.get_widget('lblHost')
        self.txtHost = self.xmltree.get_widget('txtHost')
        self.lblUser = self.xmltree.get_widget('lblUser')
        self.txtUser = self.xmltree.get_widget('txtUser')
        self.lblPasswd = self.xmltree.get_widget('lblPassword')
        self.txtPasswd = self.xmltree.get_widget('txtPassword')
        self.lblSchema = self.xmltree.get_widget('lblSchema')
        self.txtSchema = self.xmltree.get_widget('txtSchema')

        self.set_avaiable_drivers()
        self.cmbDriver.set_active(0)

        if dbc == None or (dbc != None and dbc.is_connected() == False):
                self.xmltree.get_widget('btnDisconnect').hide()

        if dbc != None:
            self.set_connection_options(dbc)

        data = None
        result = self.dialog.run()

        if result == 1:
            data = self.get_connection_options()

        self.dialog.destroy()

        return result, data

    def set_avaiable_drivers(self):
        
        model = self.cmbDriver.get_model()
        model.clear()
        
        try:
            import MySQLdb
            model.append([db.__DB_MYSQL__])
        except ImportError, e:
            print 'ImportError: ' + str(e)
        
        try:
            import sqlite3
            model.append([db.__DB_SQLITE__])
        except ImportError, e:
            print 'ImportError: ' + str(e)
        
        try:
            import psycopg2
            model.append([db.__DB_POSTGRE__])
        except ImportError, e:
            print 'ImportError: ' + str(e)
        
        try:
            import pymssql
            model.append([db.__DB_SQLSERVER__])
        except ImportError, e:
            print 'ImportError: ' + str(e)
        
        self.cmbDriver.set_model(model)
        
    def on_reuse_changed(self, widget):

        key = self.cmbReuse.get_active_text()
        dbc = self.dbpool.get(key)
        if dbc == None:
            return

        self.set_connection_options(dbc)

    def on_driver_changed(self, widget):

        if self.cmbDriver.get_active_text() == db.__DB_SQLITE__:
            self.lblHost.hide()
            self.txtHost.hide()
            self.lblUser.hide()
            self.txtUser.hide()
            self.lblPasswd.hide()
            self.txtPasswd.hide()

        else:
            self.lblHost.show()
            self.txtHost.show()
            self.lblUser.show()
            self.txtUser.show()
            self.lblPasswd.show()
            self.txtPasswd.show()

    def set_reuse_options(self):

        self.cmbReuse.remove_text(0)
        self.cmbReuse.append_text('-----')
        keys = self.dbpool.keys()

        for key in keys:
            self.cmbReuse.append_text(key)

        self.cmbReuse.set_active(0)

    def get_connection_options(self):

        driver = self.cmbDriver.get_active_text()
        host = self.txtHost.get_text().strip()
        user = self.txtUser.get_text().strip()
        passwd = self.txtPasswd.get_text().strip()
        schema = self.txtSchema.get_text().strip()

        options = {'driver': driver}

        if driver == db.__DB_MYSQL__:

            options.update({
                'user': user,
                'passwd': passwd,
                'db': schema
            })

            if os.path.exists(host):
                options['unix_socket'] = host
                
            elif host.find(':') > 0:

                hostport = host.split(':')
                
                if hostport[1].isdigit():
                    port = int(hostport[1])
                    
                else:
                    port = db.__DEFAULT_PORT_MYSQL__

                options['host'] = hostport[0]
                options['port'] = port
                
            else:
                options['host'] = host
                options['port'] = db.__DEFAULT_PORT_MYSQL__
        
        elif driver == db.__DB_POSTGRE__:

            options.update({
                'user': user,
                'password': passwd,
                'database': schema
            })

            if host.find(':') > 0:

                hostport = host.split(':')
                
                if hostport[1].isdigit():
                    port = int(hostport[1])
                    
                else:
                    port = db.__DEFAULT_PORT_POSTGRE__

                options['host'] = hostport[0]
                options['port'] = port
                
            else:
                options['host'] = host
                options['port'] = db.__DEFAULT_PORT_POSTGRE__            

        elif  driver == db.__DB_SQLSERVER__:

            options.update({
                'user': user,
                'password': passwd,
                'database': schema
            })

            port = db.__DEFAULT_PORT_SQLSERVER__

            if host.find(':') > 0:

                hostport = host.split(':')
                if hostport[1].isdigit():
                    port = hostport[1]

                host = hostport[0]

            options['host'] = '%s:%s' % (host, port)

        elif  driver == db.__DB_SQLITE__:

            options.update({'database': schema})

        return options

    def set_connection_options(self, dbc):

        driver = dbc.driver
        options = dbc.options

        if driver == db.__DB_MYSQL__:

            self.cmbDriver.set_active(0)

            host = ''
            if 'unix_socket' in options:
                host = options['unix_socket']
                
            elif 'port' in options:
                host = '%s:%d' % (options['host'], options['port'])
                
            else:
                host = options['host']

            self.txtHost.set_text(host)
            self.txtUser.set_text(options['user'])
            self.txtPasswd.set_text(options['passwd'])
            self.txtSchema.set_text(options['db'])

        elif driver == db.__DB_POSTGRE__:
            
            self.cmbDriver.set_active(2)

            host = ''
            if 'port' in options:
                host = '%s:%d' % (options['host'], options['port'])
                
            else:
                host = options['host']

            self.txtHost.set_text(host)
            self.txtUser.set_text(options['user'])
            self.txtPasswd.set_text(options['password'])
            self.txtSchema.set_text(options['database'])
        
        elif  driver == db.__DB_SQLSERVER__:

            self.cmbDriver.set_active(3)

            self.txtHost.set_text(options['host'])
            self.txtUser.set_text(options['user'])
            self.txtPasswd.set_text(options['password'])
            self.txtSchema.set_text(options['database'])

        elif  driver == db.__DB_SQLITE__:

            self.cmbDriver.set_active(1)
            self.txtSchema.set_text(options['database'])

        self.on_driver_changed(None)

class ConnectionErrorDialog(Gtk.Dialog):

    def __init__(self, message, parent=None):
        gtk.Dialog.__init__(self, title="Connection error", parent=parent, flags=gtk.DIALOG_MODAL, buttons=None)
        self.add_button("Close", gtk.RESPONSE_CLOSE)
        label = gtk.Label(message)
        self.vbox.pack_start(label, True, True, 0)
        label.show()

class ScriptErrorDialog(Gtk.Dialog):

    def __init__(self, message, parent=None):
        gtk.Dialog.__init__(self, title="Script error", parent=parent, flags=gtk.DIALOG_MODAL, buttons=None)
        self.add_button("Ignore", 2)
        self.add_button("Ignore all", 1)
        self.add_button("Stop script", 0)
        label = gtk.Label(message)
        self.vbox.pack_start(label, True, True, 0)
        label.show()

class FileExistsDialog(Gtk.Dialog):

    def __init__(self, message, parent=None):
        gtk.Dialog.__init__(self, title="File exists", parent=parent, flags=gtk.DIALOG_MODAL, buttons=None)
        self.add_button("Yes", 1)
        self.add_button("Cancel", 0)
        label = gtk.Label(message)
        self.vbox.pack_start(label, True, True, 0)
        label.show()
