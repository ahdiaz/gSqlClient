
class FileExistsDialog(Gtk.Dialog):

    def __init__(self, message, parent=None):
        GObject.GObject.__init__(self, title=_("File exists"), parent=parent, flags=Gtk.DialogFlags.MODAL, buttons=None)
        self.add_button(_("Yes"), 1)
        self.add_button(_("Cancel"), 0)
        label = Gtk.Label(label=message)
        self.vbox.pack_start(label, True, True, 0)
        label.show()
