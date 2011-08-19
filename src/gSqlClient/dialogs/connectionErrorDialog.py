
class ConnectionErrorDialog(Gtk.Dialog):

    def __init__(self, message, parent=None):
        gtk.Dialog.__init__(self, title=_("Connection error"), parent=parent, flags=gtk.DIALOG_MODAL, buttons=None)
        self.add_button(_("Close"), gtk.RESPONSE_CLOSE)
        label = gtk.Label(message)
        self.vbox.pack_start(label, True, True, 0)
        label.show()
