#!/usr/bin/python
import sys
from PyQt4 import QtGui, QtCore, uic
import pdb
import os.path

api_key_file = '.api_key.txt'

class ATUploaderGui(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
 
        self.ui = uic.loadUi('at_uploader.ui')

        # initialize api key functionality
        api_key_save = self.ui.apikey_save_field
        api_key_save.stateChanged.connect(self.save_api_key)
        # put api key in field if saved
        if os.path.isfile(api_key_file):
            self.ui.apikey_field.setText(open(api_key_file).read())
        self.ui.show()

    def save_api_key(self):
        if self.ui.apikey_save_field.isChecked():
            api_key = self.ui.apikey_field.text()
            f = open(api_key_file, 'w')
            f.write(api_key)
            f.close()
 
if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    win = ATUploaderGui()
    sys.exit(app.exec_())
