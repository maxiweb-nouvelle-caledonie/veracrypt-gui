"""
Dialogue de montage pour les fichiers et périphériques VeraCrypt.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QFileDialog, QMessageBox, QDialogButtonBox,
    QInputDialog
)
from PyQt6.QtCore import QDir, Qt, QUrl
from typing import Optional, Tuple
import os
from datetime import datetime
from src.constants import Constants
from src.utils import veracrypt, system
import time
from src.gui.loading_dialog import LoadingDialog
from src.gui.device_dialog import DeviceDialog

class MountDialog(QDialog):
    def __init__(self, parent=None, is_device=False):
        super().__init__(parent)
        self.is_device = is_device
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Monter un volume")
        layout = QVBoxLayout()
        
        # Volume
        volume_layout = QHBoxLayout()
        volume_label = QLabel("Volume:")
        self.volume_path = QLineEdit()
        volume_button = QPushButton("Parcourir")
        volume_button.clicked.connect(self._browse_volume)
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_path)
        volume_layout.addWidget(volume_button)
        layout.addLayout(volume_layout)
        
        # Point de montage
        mount_layout = QHBoxLayout()
        mount_label = QLabel("Point de montage:")
        self.mount_point = QLineEdit()
        mount_button = QPushButton("Parcourir")
        mount_button.clicked.connect(self._browse_mount_point)
        mount_layout.addWidget(mount_label)
        mount_layout.addWidget(self.mount_point)
        mount_layout.addWidget(mount_button)
        layout.addLayout(mount_layout)
        
        # Mot de passe
        password_layout = QHBoxLayout()
        password_label = QLabel("Mot de passe:")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password)
        layout.addLayout(password_layout)
        
        # Boutons
        button_layout = QHBoxLayout()
        cancel_button = QPushButton("Annuler")
        ok_button = QPushButton("OK")
        cancel_button.clicked.connect(self.reject)
        ok_button.clicked.connect(self._handle_ok)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
    def _browse_volume(self):
        """Ouvre un dialogue pour sélectionner un volume."""
        if self.is_device:
            # Pour les périphériques, on utilise notre propre dialogue
            dialog = DeviceDialog(self)
            if dialog.exec():
                self.volume_path.setText(dialog.selected_device)
                # Créer un point de montage par défaut
                mount_point = os.path.join(
                    veracrypt.get_user_mount_dir(),
                    f"veracrypt_{time.strftime('%Y%m%d_%H%M%S')}"
                )
                self.mount_point.setText(mount_point)
        else:
            # Pour les fichiers, on utilise le dialogue standard
            options = QFileDialog.Option.DontUseNativeDialog
            file_filter = "Volumes VeraCrypt (*.vc *.tc *.hc);;Tous les fichiers (*)"
            
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Sélectionner un volume VeraCrypt",
                "",  # Dossier par défaut
                file_filter,
                options=options
            )
            
            if file_name:
                self.volume_path.setText(file_name)
                
    def _browse_mount_point(self):
        """Ouvre un dialogue pour sélectionner le point de montage."""
        # Utiliser le répertoire utilisateur comme base
        user_dir = veracrypt.get_user_mount_dir()
        
        # Demander le nom du répertoire
        dir_name, ok = QInputDialog.getText(
            self,
            "Point de montage",
            "Nom du répertoire de montage:",
            QLineEdit.EchoMode.Normal,
            ""
        )
        
        if ok and dir_name:
            # Construire le chemin complet
            mount_point = os.path.join(user_dir, dir_name)
            self.mount_point.setText(mount_point)
            
    def _get_volume_path(self) -> bool:
        """Vérifie et retourne le chemin du volume."""
        volume_path = self.volume_path.text().strip()
        if not volume_path:
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez sélectionner un volume"
            )
            return False
            
        # Pour les périphériques, utiliser la validation spécifique
        if self.is_device:
            if not system._is_valid_device(volume_path):
                QMessageBox.warning(
                    self,
                    "Erreur",
                    f"Le périphérique {volume_path} n'est pas valide ou n'existe pas"
                )
                return False
        else:
            # Pour les fichiers, vérifier l'existence
            if not os.path.exists(volume_path):
                QMessageBox.warning(
                    self,
                    "Erreur",
                    f"Le fichier {volume_path} n'existe pas"
                )
                return False
                
            if not os.path.isfile(volume_path):
                QMessageBox.warning(
                    self,
                    "Erreur",
                    f"{volume_path} n'est pas un fichier"
                )
                return False
            
        return True
            
    def _get_mount_point(self) -> bool:
        """Vérifie et retourne le point de montage."""
        mount_point = self.mount_point.text().strip()
        
        # Si aucun point de montage n'est spécifié
        if not mount_point:
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez spécifier un point de montage"
            )
            return False
            
        # Vérifier le point de montage
        valid, error = veracrypt.check_mount_point(mount_point)
        if not valid:
            QMessageBox.warning(
                self,
                "Erreur",
                error
            )
            return False
            
        return True
            
    def _get_password(self) -> bool:
        """Vérifie et retourne le mot de passe."""
        if not self.password.text():
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez entrer un mot de passe"
            )
            return False
        return True
        
    def _handle_ok(self):
        """Gère le clic sur le bouton OK."""
        if not self._get_volume_path():
            return
            
        if not self._get_mount_point():
            return
            
        if not self._get_password():
            return
            
        # Montrer le loader
        loading = LoadingDialog(self, "Montage du volume en cours...")
        loading.show()
        
        try:
            # Monter le volume
            success, message = veracrypt.mount_volume(
                self.volume_path.text(),
                self.mount_point.text(),
                self.password.text()
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Succès",
                    f"Le volume {self.volume_path.text()} a été monté avec succès sur {self.mount_point.text()}"
                )
                self.accept()
            else:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur lors du montage: {message}"
                )
        finally:
            loading.hide()
            
    def exec(self) -> bool:
        """Exécute le dialogue de montage."""
        return super().exec()
