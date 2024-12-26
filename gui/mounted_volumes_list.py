"""
Widget affichant la liste des volumes montés avec leurs icônes.
"""

from PyQt6.QtWidgets import (
    QListWidget, QListWidgetItem, QMenu,
    QMessageBox
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal
import os
import subprocess
from src.utils import veracrypt, system
from src.constants import Constants

class MountedVolumesList(QListWidget):
    volume_unmounted = pyqtSignal(str)  # Signal émis quand un volume est démonté

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemDoubleClicked.connect(self._open_volume)
        self._init_icons()

    def _init_icons(self):
        """Initialise les icônes pour les volumes."""
        self.volume_icon = QIcon.fromTheme('drive-harddisk')

    def add_volume(self, mount_path: str):
        """Ajoute un volume à la liste."""
        item = QListWidgetItem(self.volume_icon, mount_path)
        item.setData(Qt.ItemDataRole.UserRole, mount_path)
        self.addItem(item)

    def remove_volume(self, mount_path: str):
        """Retire un volume de la liste."""
        items = self.findItems(mount_path, Qt.MatchFlag.MatchExactly)
        for item in items:
            self.takeItem(self.row(item))

    def _open_volume(self, item):
        """Ouvre le volume dans l'explorateur de fichiers."""
        mount_path = item.data(Qt.ItemDataRole.UserRole)
        try:
            # Utiliser xdg-open pour ouvrir le gestionnaire de fichiers par défaut
            subprocess.Popen(['xdg-open', mount_path])
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'ouvrir le volume:\n{str(e)}"
            )

    def _show_context_menu(self, position):
        """Affiche le menu contextuel pour un volume."""
        item = self.itemAt(position)
        if not item:
            return
            
        mount_path = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu()
        
        # Action pour ouvrir
        open_action = menu.addAction("Ouvrir")
        open_action.triggered.connect(lambda: self._open_volume(item))
        
        # Séparateur
        menu.addSeparator()
        
        # Action pour démonter
        unmount_action = menu.addAction("Démonter")
        unmount_action.triggered.connect(lambda: self._unmount_volume(mount_path))
        
        # Action pour afficher les informations
        info_action = menu.addAction("Informations")
        info_action.triggered.connect(lambda: self._show_volume_info(mount_path))
        
        menu.exec(self.mapToGlobal(position))

    def _show_volume_info(self, mount_path):
        """Affiche les informations détaillées sur un volume."""
        cmd = [
            'sudo',
            Constants.VERACRYPT_PATH,
            '--text',
            '--list'
        ]
        success, stdout, _ = veracrypt.execute_veracrypt_command(cmd)
        if success:
            info = ""
            for line in stdout.split('\n'):
                if mount_path in line:
                    info = line
                    break
                    
            if info:
                QMessageBox.information(
                    self,
                    "Informations sur le volume",
                    f"Détails du volume:\n{info}"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "Impossible de trouver les informations du volume"
                )
                
    def _unmount_volume(self, mount_path):
        """Démonte un volume."""
        try:
            success, message = veracrypt.unmount_volume(mount_path)
            
            if success:
                self.remove_volume(mount_path)
                self.volume_unmounted.emit(mount_path)
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Le volume {mount_path} a été démonté avec succès"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur de démontage:\n{message}"
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur inattendue lors du démontage:\n{str(e)}"
            )
