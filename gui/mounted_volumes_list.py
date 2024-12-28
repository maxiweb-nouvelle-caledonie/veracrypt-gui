"""
Widget de liste des volumes montés.
"""

from PyQt6.QtWidgets import QListWidget, QListWidgetItem, QMenu, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from src.utils import veracrypt

class MountedVolumesList(QListWidget):
    """Liste des volumes montés avec menu contextuel."""
    
    # Signal émis quand un volume est démonté
    volume_unmounted = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Initialiser les icônes
        self._init_icons()
        
    def _init_icons(self):
        """Initialise les icônes pour les différents types de volumes."""
        # Icône par défaut pour les volumes
        self.volume_icon = QIcon.fromTheme('drive-harddisk')
        # Icône pour les périphériques
        self.device_icon = QIcon.fromTheme('drive-removable-media')
        # Icône pour les fichiers
        self.file_icon = QIcon.fromTheme('media-flash')
        
    def addItem(self, item: QListWidgetItem):
        """Surcharge de addItem pour ajouter automatiquement une icône."""
        # Récupérer le point de montage
        _, mount_point = item.data(Qt.ItemDataRole.UserRole)
        
        # Déterminer l'icône appropriée
        if mount_point.startswith('/dev/'):
            item.setIcon(self.device_icon)
        else:
            item.setIcon(self.volume_icon)
            
        # Ajouter l'item à la liste
        super().addItem(item)
        
    def _show_context_menu(self, position):
        """Affiche le menu contextuel."""
        item = self.itemAt(position)
        if not item:
            return
            
        # Créer le menu
        menu = QMenu()
        unmount_action = menu.addAction(QIcon.fromTheme('media-eject'), "Démonter")
        open_action = menu.addAction(QIcon.fromTheme('folder-open'), "Ouvrir")
        
        # Ajouter un séparateur
        menu.addSeparator()
        
        # Ajouter l'action d'informations
        info_action = menu.addAction(QIcon.fromTheme('dialog-information'), "Informations")
        
        # Récupérer le point de montage
        slot, mount_point = item.data(Qt.ItemDataRole.UserRole)
        
        # Exécuter l'action sélectionnée
        action = menu.exec(self.mapToGlobal(position))
        if action == unmount_action:
            self._unmount_volume(mount_point)
        elif action == open_action:
            self._open_volume(mount_point)
        elif action == info_action:
            self._show_volume_info(slot, mount_point)
            
    def _unmount_volume(self, mount_point: str):
        """Démonte un volume."""
        # Demander confirmation
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment démonter le volume {mount_point} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success, error = veracrypt.unmount_volume(mount_point)
            if success:
                # Émettre le signal de démontage
                self.volume_unmounted.emit(mount_point)
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Le volume {mount_point} a été démonté avec succès"
                )
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur lors du démontage: {error}"
                )
                
    def _open_volume(self, mount_point: str):
        """Ouvre le volume dans le gestionnaire de fichiers."""
        try:
            # Utiliser xdg-open pour ouvrir le point de montage
            import subprocess
            subprocess.Popen(['xdg-open', mount_point])
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'ouvrir le volume: {str(e)}"
            )
            
    def _show_volume_info(self, slot: str, mount_point: str):
        """Affiche les informations sur le volume."""
        try:
            # Récupérer les informations du volume
            volumes = veracrypt.list_mounted_volumes()
            for vol_slot, vol_mount in volumes:
                if vol_slot == slot:
                    QMessageBox.information(
                        self,
                        "Informations sur le volume",
                        f"Slot: {slot}\n"
                        f"Point de montage: {mount_point}"
                    )
                    return
                    
            QMessageBox.warning(
                self,
                "Erreur",
                "Impossible de trouver les informations du volume"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de la récupération des informations: {str(e)}"
            )
