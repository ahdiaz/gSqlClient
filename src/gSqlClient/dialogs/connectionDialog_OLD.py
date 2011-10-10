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

class ConnectionDialog_old():

    def __init__(self, gladeFile, window, dbpool):

        self.xmltree = Gtk.glade.XML(gladeFile, 'connectionDialog')
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
