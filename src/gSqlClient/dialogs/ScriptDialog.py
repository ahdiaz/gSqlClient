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

from .. import utils

import gettext
from gettext import gettext as _
gettext.textdomain('gsqlclient')


class ScriptDialog:

    OPT_CANCEL = 0
    OPT_ASK = 1
    OPT_STOP = 2
    OPT_IGNORE = 3

    def __init__(self, parent=None):

        self.builder = Gtk.Builder()
        self.builder.add_from_file(utils.get_ui_file('ScriptDialog'))
        self.builder.connect_signals(self)
        self.dialog = self.builder.get_object('ScriptDialog')
        self.dialog.set_transient_for(parent)

        self.radioAsk = self.builder.get_object("radioAsk")
        self.radioStop = self.builder.get_object("radioStop")
        self.radioIgnore = self.builder.get_object("radioIgnore")

    def get_ask_active(self):
        return self.radioAsk.get_active()

    def get_stop_active(self):
        return self.radioStop.get_active()

    def get_ignore_active(self):
        return self.radioIgnore.get_active()

    def run(self):

        ret = self.OPT_CANCEL
        result = self.dialog.run()

        if result != self.OPT_CANCEL:
            if self.radioAsk.get_active():
                ret = self.OPT_ASK

            elif self.radioStop.get_active():
                ret = self.OPT_STOP

            elif self.radioIgnore.get_active():
                ret = self.OPT_IGNORE

        self.dialog.destroy()
        return ret
