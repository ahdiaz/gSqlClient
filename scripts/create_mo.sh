#!/bin/bash

lang=$1
appname="gsqlclient"
source_path="../src/gSqlClient"

if [ "" == "$lang" ]; then
    lang="es"
fi

pofile="${source_path}/po/${lang}/LC_MESSAGES/${lang}.po"
mofile="${source_path}/po/${lang}/LC_MESSAGES/${appname}.mo"

msgfmt $pofile --output-file $mofile
