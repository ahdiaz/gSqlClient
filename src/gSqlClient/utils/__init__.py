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
# $Id: __init__.py 63 2011-08-19 00:14:31Z ahdiaz $
#

import os

from exporter import Exporter
from gscstore import GSCStore


def get_data_file(*path_segments):
    return os.path.join(get_data_path(), *path_segments)

def get_data_path():
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

    abs_data_path = os.path.abspath(path)
    if not os.path.exists(abs_data_path):
        return None

    return abs_data_path

def get_media_file(media_file_name):
    media_filename = get_data_file('media', '%s' % (media_file_name,))
    if not os.path.exists(media_filename):
        media_filename = None

    return media_filename

def get_ui_file(ui_file_name):
    ui_filename = get_data_file('ui', '%s.ui' % (ui_file_name,))
    if not os.path.exists(ui_filename):
        ui_filename = None

    return ui_filename

def get_locale_path():
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'po')
