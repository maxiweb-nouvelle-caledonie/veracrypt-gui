import sys
import os
import subprocess
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QPushButton, QFileDialog, QMessageBox, QTreeView,
                            QLabel, QLineEdit, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class VeraCryptManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('VeraCrypt Manager')
        self.setGeometry(100, 100, 800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Composants pour le montage
        self.setup_mount_section(layout)
        
        # Liste des volumes montés
        self.setup_mounted_volumes_section(layout)

    def setup_mount_section(self, layout):
        # Bouton pour sélectionner le fichier/périphérique
        self.select_button = QPushButton('Sélectionner Volume/Périphérique')
        self.select_button.clicked.connect(self.select_volume)
        layout.addWidget(self.select_button)

        # Type de volume
        self.volume_type = QComboBox()
        self.volume_type.addItems(['Fichier', 'Périphérique'])
        layout.addWidget(self.volume_type)

        # Point de montage
        self.mount_path = QLineEdit()
        self.mount_path.setPlaceholderText('Point de montage...')
        layout.addWidget(self.mount_path)

        # Bouton de montage
        self.mount_button = QPushButton('Monter')
        self.mount_button.clicked.connect(self.mount_volume)
        layout.addWidget(self.mount_button)

    def setup_mounted_volumes_section(self, layout):
        # Liste des volumes montés
        self.volumes_list = QTreeView()
        layout.addWidget(self.volumes_list)

        # Bouton de démontage
        self.unmount_button = QPushButton('Démonter')
        self.unmount_button.clicked.connect(self.unmount_volume)
        layout.addWidget(self.unmount_button)

    def select_volume(self):
        if self.volume_type.currentText() == 'Fichier':
            filename, _ = QFileDialog.getOpenFileName(
                self, 
                "Sélectionner le volume VeraCrypt",
                os.path.expanduser("~")
            )
            if filename:
                self.selected_volume = filename
        else:
            # Logique pour lister les périphériques
            self.show_device_selection_dialog()

    def mount_volume(self):
        # Vérification sudo
        if not self.check_sudo():
            QMessageBox.critical(self, 'Erreur', 'Privilèges sudo requis')
            return

        # Dialogue pour le mot de passe
        password, ok = self.get_password_dialog()
        if not ok:
            return

        # Lancer le montage dans un thread séparé
        self.mount_thread = MountThread(
            self.selected_volume,
            self.mount_path.text(),
            password
        )
        self.mount_thread.finished.connect(self.on_mount_finished)
        self.mount_thread.start()

    def unmount_volume(self):
        selected = self.volumes_list.selectedIndexes()
        if not selected:
            return

        volume = selected[0].data()
        # Lancer le démontage dans un thread
        self.unmount_thread = UnmountThread(volume)
        self.unmount_thread.finished.connect(self.on_unmount_finished)
        self.unmount_thread.start()

    def check_sudo(self):
        try:
            subprocess.run(['sudo', '-v'], check=True)
            return True
        except subprocess.CalledProcessError:
            return False

class MountThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, volume, mount_point, password):
        super().__init__()
        self.volume = volume
        self.mount_point = mount_point
        self.password = password

    def run(self):
        try:
            # Commandes de montage similaires au script bash
            # Utilisation de subprocess.run avec input pour le mot de passe
            result = subprocess.run(
                ['sudo', 'veracrypt', '-t', self.volume, self.mount_point],
                input=f"{self.password}\n\n\nn\n".encode(),
                capture_output=True
            )
            success = result.returncode == 0
            self.finished.emit(success, result.stderr.decode() if not success else "")
        except Exception as e:
            self.finished.emit(False, str(e))

class UnmountThread(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, volume):
        super().__init__()
        self.volume = volume

    def run(self):
        try:
            result = subprocess.run(
                ['sudo', 'veracrypt', '-d', self.volume],
                capture_output=True
            )
            success = result.returncode == 0
            self.finished.emit(success, result.stderr.decode() if not success else "")
        except Exception as e:
            self.finished.emit(False, str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VeraCryptManager()
    window.show()
    sys.exit(app.exec())