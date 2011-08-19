
class ScriptErrorDialog(Gtk.Dialog):

    def __init__(self, message, parent=None):
        gtk.Dialog.__init__(self, title=_("Script error"), parent=parent, flags=gtk.DIALOG_MODAL, buttons=None)
        self.add_button(_("Ignore"), 2)
        self.add_button(_("Ignore all"), 1)
        self.add_button(_("Stop script"), 0)
        label = gtk.Label(message)
        self.vbox.pack_start(label, True, True, 0)
        label.show()
