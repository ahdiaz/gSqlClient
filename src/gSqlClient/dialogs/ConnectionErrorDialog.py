
class ConnectionErrorDialog(Gtk.Dialog):

    def __init__(self, message, parent=None):
        GObject.GObject.__init__(self, title=_("Connection error"), parent=parent, flags=Gtk.DialogFlags.MODAL, buttons=None)
        self.add_button(_("Close"), Gtk.ResponseType.CLOSE)
        label = Gtk.Label(label=message)
        self.vbox.pack_start(label, True, True, 0)
        label.show()
