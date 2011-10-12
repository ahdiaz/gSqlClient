#!/bin/bash

lang=$1
appname="gsqlclient"
source_path="../src/gSqlClient"

if [ "" == "$lang" ]; then
    lang="es"
fi

potfilesin="${source_path}/po/POTFILES.in"
potfile="${source_path}/po/${appname}.pot"
pofile="${source_path}/po/${lang}/LC_MESSAGES/${lang}.po"
pofilemerged="${source_path}/po/${lang}/LC_MESSAGES/${lang}.merged.po"
mofile="${source_path}/po/${lang}/LC_MESSAGES/${appname}.mo"

find $source_path -type f -name "*.py" > $potfilesin

xgettext --language=Python --keyword=_ --output=$potfile -f $potfilesin

if [ ! -f $pofile ]; then

    msginit --input=$potfile --locale=es_ES --output-file $pofile

else

    msgmerge $pofile $potfile > $pofilemerged
    mv $pofilemerged $pofile

fi
