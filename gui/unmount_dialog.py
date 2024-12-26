"""
Dialogue de démontage pour les volumes VeraCrypt.
"""

from PyQt6.QtWidgets import QDialog, QInputDialog, QMessageBox
from src.utils import veracrypt, system
from src.constants import Constants

class UnmountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Démontage VeraCrypt")
        self.setModal(True)

    def exec(self) -> bool:
        """Exécute le dialogue de démontage."""
        # Liste des volumes montés
        volumes = veracrypt.list_mounted_volumes()
        if not volumes:
            QMessageBox.information(self, 'Info', 'Aucun volume monté.')
            return False

        # Sélection du volume à démonter
        selected_mount = self._select_volume(volumes)
        if not selected_mount:
            return False

        # Démontage du volume
        return self._unmount_volume(selected_mount)

    def _select_volume(self, volumes):
        """Sélectionne un volume à démonter."""
        selected_mount, ok = QInputDialog.getItem(
            self,
            'Sélection du volume',
            'Choisissez le volume à démonter :',
            volumes,
            0,
            False
        )
        return selected_mount if ok and selected_mount else None

    def _unmount_volume(self, mount_point: str) -> bool:
        """Démonte un volume VeraCrypt."""
        self.parent.log_message(f"Tentative de démontage du volume sur {mount_point}...")
        
        success, message = veracrypt.unmount_volume(mount_point)
        
        if success:
            QMessageBox.information(self, 'Succès', f'Volume démonté avec succès: {mount_point}')
            if mount_point in self.parent.mounted_volumes:
                del self.parent.mounted_volumes[mount_point]
            
            # Nettoyage du point de montage si nécessaire
            if mount_point.startswith(Constants.MOUNT_PREFIX):
                system.cleanup_mount_point(mount_point)
            
            return True
        else:
            QMessageBox.critical(self, 'Erreur', f'Erreur de démontage:\n{message}')
            return False
