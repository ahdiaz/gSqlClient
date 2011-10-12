# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
#
# gSqlClient is a Python plugin that turns Gedit into a SQL client.
# Copyright (C) 2009 Antonio Hernández Diaz <ahdiaz@gmail.com>
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


from gi.repository import GObject, Gtk

import gettext
from gettext import gettext as _
gettext.textdomain('gsqlclient')


class ScriptErrorDialog(Gtk.Dialog):

    OPT_STOP = 0
    OPT_IGNORE_ALL = 1
    OPT_IGNORE = 2

    def __init__(self, message, parent=None):
        Gtk.Dialog.__init__(self, title=_("Script error"), parent=parent, flags=Gtk.DialogFlags.MODAL, buttons=None)
        self.add_button(_("Ignore"), self.OPT_IGNORE)
        self.add_button(_("Ignore all"), self.OPT_IGNORE_ALL)
        self.add_button(_("Stop script"), self.OPT_STOP)
        label = Gtk.Label(label=message)
        self.vbox.pack_start(label, True, True, 0)
        label.show()
