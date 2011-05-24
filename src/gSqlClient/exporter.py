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

from xml.dom.minidom import getDOMImplementation

class Exporter():

    FORMAT_SQL = "SQL"
    FORMAT_XML = "XML"
    FORMAT_CSV = "CSV"

    def export(self, format, model, columns):

        exported = None

        if format == Exporter.FORMAT_XML:
            exported = self._export_xml(model, columns)
        elif format == Exporter.FORMAT_CSV:
            exported = self._export_csv(model, columns)
        elif format == Exporter.FORMAT_SQL:
            exported = self._export_sql(model, columns)

        return exported

    def _export_xml(self, model, columns):

        impl = getDOMImplementation()
        #namespaceUri=None, qualifiedName="resultset", doctype=None
        doc = impl.createDocument(None, "resultset", None)
        root = doc.documentElement

        it = model.get_iter_first()
        while it is not None:

            row = doc.createElement("row")

            for c in range(0, len(columns)):
                
                column = columns[c]
                value = model[it][c]
                
                if value is None:
                    value = "NULL"
                                
                name = doc.createAttribute("name")
                name.value = column
                
                # TODO: Type in the cursor, not in the treeview model
                ftype = doc.createAttribute("type")
                ftype.value = type(value).__name__
                
                field = doc.createElement("field")
                field.setAttributeNode(name)
                #field.setAttributeNode(ftype)
                field.appendChild(doc.createTextNode(str(value)))
                row.appendChild(field)

            root.appendChild(row)
            it = model.iter_next(it)

        xmlstr = doc.toxml()
        doc.unlink()

        return xmlstr

    def _export_csv(self, model, columns):

        csvstr = '"%s"\n' % (str.join('","', columns))
        
        it = model.get_iter_first()
        while it is not None:
            
            row = []
            _row = model[it]
            
            for value in _row:
                if value is None:
                    value = "NULL"
                row.append(value)
            
            csvstr += '"%s"\n' % (str.join('","', row))
            it = model.iter_next(it)

        return csvstr

    def _export_sql(self, model, columns):

        # TODO: What is the table to use if the SQL sentence is a join between more than one table?
        table = 'table'

        # See panels.py: ResultsetTreeView::load_cursor()
        str_columns = ', '.join(['`%s`' % (c.replace("__", "_")) for c in columns])
        
        str_insert = "INSERT INTO `" + table + "` (" + str_columns + ") VALUES ('%s');\n"
        sqlstr = ''
        
        it = model.get_iter_first()
        while it is not None:
            
            row = []
            _row = model[it]
            
            for value in _row:
                if value is None:
                    value = "NULL"
                row.append(value)
            
            sqlstr += str_insert % (str.join("', '", row))
            it = model.iter_next(it)

        return sqlstr
