
class FileExistsDialog(Gtk.Dialog):

    def __init__(self, message, parent=None):
        gtk.Dialog.__init__(self, title="File exists", parent=parent, flags=gtk.DIALOG_MODAL, buttons=None)
        self.add_button("Yes", 1)
        self.add_button("Cancel", 0)
        label = gtk.Label(message)
        self.vbox.pack_start(label, True, True, 0)
        label.show()
