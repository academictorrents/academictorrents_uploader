#!/usr/bin/python3
import sys
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from torrent import make_torrent
import os.path
import re
from base64 import b64encode
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

api_key_file = '.api_key.txt'
my_torrent = None

class ATUploaderGui(QtWidgets.QMainWindow):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
 
        self.ui = uic.loadUi('at_uploader.ui')

        # put api key in field if saved
        if os.path.isfile(api_key_file):
            self.ui.apikey_field.setText(open(api_key_file).read())

        # bind items to functions
        self.ui.apikey_save_field.stateChanged.connect(self.save_api_key)
        self.ui.select_file_button.clicked.connect(self.select_file)
        self.ui.select_directory_button.clicked.connect(self.select_directory)
        self.ui.select_torrent_button.clicked.connect(self.select_torrent)

        self.ui.data_source_field.activated[str].connect(self.select_data_source)
        self.ui.create_torrent_button.clicked.connect(self.create_torrent)
        self.ui.upload_button.clicked.connect(self.upload)
        self.ui.show()

    def create_torrent(self):
        if self.ui.data_source_field.currentText()=="Create Torrent From File":
            node_name = self.ui.file_label.text()
        elif self.ui.data_source_field.currentText()=="Create Torrent From Directory":
            node_name = self.ui.directory_label.text()
        elif self.ui.data_source_field.currentText()=="Create Torrent From URL":
            pass
        
        global my_torrent
        my_torrent = make_torrent(node_name)
        QtWidgets.QMessageBox.about(self, "Torrent Created", "Torrent created: " + my_torrent + 
                                    ".  Please fill in metadata before uploading.")

    def select_data_source(self, source):
        self.disable_all_sources()
        if source=="Create Torrent From URL":
            self.ui.select_url_field.setEnabled(True)
            self.ui.select_url_label.setEnabled(True)
            self.ui.download_progress.setEnabled(True)
            self.ui.create_torrent_button.setEnabled(True)
        elif source=="Create Torrent From File":
            self.ui.select_file_button.setEnabled(True)
            self.ui.file_label.setEnabled(True)
            self.ui.create_torrent_button.setEnabled(True)
        elif source=="Create Torrent From Directory":
            self.ui.select_directory_button.setEnabled(True)
            self.ui.directory_label.setEnabled(True)
            self.ui.create_torrent_button.setEnabled(True)
        elif source=="Select Existing Torrent":
            self.ui.select_torrent_button.setEnabled(True)
            self.ui.torrent_label.setEnabled(True)

    def disable_all_sources(self):
        self.ui.select_file_button.setDisabled(True)
        self.ui.file_label.setDisabled(True)
        self.ui.select_directory_button.setDisabled(True)
        self.ui.directory_label.setDisabled(True)
        self.ui.select_url_field.setDisabled(True)
        self.ui.select_url_label.setDisabled(True)
        self.ui.select_torrent_button.setDisabled(True)
        self.ui.torrent_label.setDisabled(True)
        self.ui.create_torrent_button.setDisabled(True)
        self.ui.download_progress.setDisabled(True)

    def save_api_key(self):
        if self.ui.apikey_save_field.isChecked():
            api_key = self.ui.apikey_field.text()
            f = open(api_key_file, 'w')
            f.write(api_key)
            f.close()

    def select_file(self):
        filename = QtWidgets.QFileDialog.getOpenFileName(self, 
                                                     'Select a File',
                                                     '.')
        self.ui.file_label.setText(filename[0])
        
    def select_directory(self):
        directory = QtWidgets.QFileDialog.getExistingDirectory(self,
                                                           'Select Directory',
                                                           '.')
        self.ui.directory_label.setText(directory)

    def select_torrent(self):
        torrent = QtWidgets.QFileDialog.getOpenFileName(self,
                                                    'Select Torrent',
                                                    '.', 'Torrent files (*.torrent)')
        self.ui.torrent_label.setText(torrent)
        global my_torrent
        my_torrent = torrent
 
    def upload(self):
        api_key = self.ui.apikey_field.text()
        matches = re.match("uid=(.*);pass=(.*)", api_key)
        if not len(matches.groups())==2:
            QtWidgets.QMessageBox.about(self, "Error", 
                                        "Invalid API key.  Please log in to Academic Torrents " + 
                                        "and copy your API key from http://academictorrents.com/about.php#apikeys.")
            return

        if my_torrent==None:
            QtWidgets.QMessageBox.about(self, "Error", 
                                        "Create or select a torrent to upload first!")
            return

        if self.ui.category_field.currentText()=='Dataset':
            category = 6
        elif self.ui.category_field.currentText()=='Paper':
            category = 5

        post_params = {
            'uid' : matches.groups()[0],
            'pass' : matches.groups()[1],
            'name' : self.ui.torrent_name_field.text(),
            'authors' : self.ui.authors_field.text(),
            'descr' : self.ui.description_field.toPlainText(),
            'category' : category,
            'tags' : self.ui.tags_field.text(),
            'urllist' : self.ui.backup_url_field.text(),
            'file' : b64encode(open(my_torrent, 'rb').read())
        }
        
        data = urlencode(post_params).encode('utf-8')
        req = Request('http://academictorrents.com/api/paper', data)
        
        try:
            response = urlopen(req)
        except HTTPError as e:
            print(e)
            response = e
            print(response.read())            
        QtWidgets.QMessageBox.about(self, "Success", "You've uploaded!")

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = ATUploaderGui()
    sys.exit(app.exec_())
