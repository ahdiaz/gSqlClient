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
