"""
Dialogue de montage pour les fichiers et périphériques VeraCrypt.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QFileDialog, QMessageBox, QDialogButtonBox,
    QInputDialog, QCheckBox
)
from PyQt6.QtCore import QDir, Qt, QUrl, pyqtSignal
from typing import Optional, Tuple
import os
from datetime import datetime
from constants import Constants
from utils import veracrypt, system
from utils.favorites import Favorites
import time
from gui.loading_dialog import LoadingDialog
from gui.device_dialog import DeviceDialog

class MountDialog(QDialog):
    # Signal émis quand un favori est ajouté
    favorite_added = pyqtSignal()
    
    def __init__(self, parent=None, is_device=False, favorite_path=None):
        super().__init__(parent)
        self.is_device = is_device
        self.favorite_path = favorite_path
        self.favorites = Favorites()
        self.favorite_added = False  # Pour suivre si un favori a été ajouté
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Monter un volume" if not self.is_device else "Monter un périphérique")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Chemin du volume
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        if self.favorite_path:
            self.path_edit.setText(self.favorite_path)
            self.path_edit.setReadOnly(True)
        
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self.browse_volume)
        path_layout.addWidget(QLabel("Chemin :"))
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)
        
        # Point de montage
        mount_layout = QHBoxLayout()
        self.mount_edit = QLineEdit()
        
        # Si c'est un favori, utiliser le point de montage stocké
        if self.favorite_path:
            favorite = self.favorites.get_favorite(self.favorite_path)
            if favorite and 'mount_point' in favorite:
                self.mount_edit.setText(favorite['mount_point'])
        
        mount_button = QPushButton("Parcourir...")
        mount_button.clicked.connect(self.browse_mount_point)
        mount_layout.addWidget(QLabel("Point de montage :"))
        mount_layout.addWidget(self.mount_edit)
        mount_layout.addWidget(mount_button)
        layout.addLayout(mount_layout)
        
        # Mot de passe
        password_layout = QHBoxLayout()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(QLabel("Mot de passe :"))
        password_layout.addWidget(self.password_edit)
        layout.addLayout(password_layout)
        
        # Option favori (seulement si ce n'est pas un favori existant)
        self.favorite_checkbox = QCheckBox("Ajouter aux favoris")
        if self.favorite_path:
            self.favorite_checkbox.setVisible(False)
        layout.addWidget(self.favorite_checkbox)
        
        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def browse_volume(self):
        """Ouvre un dialogue pour sélectionner un volume."""
        if self.is_device:
            # Pour les périphériques, on utilise notre propre dialogue
            dialog = DeviceDialog(self)
            if dialog.exec():
                self.path_edit.setText(dialog.selected_device)
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
                self.path_edit.setText(file_name)

    def browse_mount_point(self):
        """Ouvre un dialogue pour sélectionner le point de montage."""
        # Utiliser le répertoire utilisateur comme base
        user_dir = veracrypt.get_user_mount_dir()
        
        # Demander le nom du répertoire
        dir_name, ok = QInputDialog.getText(
            self,
            "Point de montage",
            "Nom du répertoire de montage :",
            QLineEdit.EchoMode.Normal,
            ""
        )
        
        if ok and dir_name:
            # Construire le chemin complet
            mount_point = os.path.join(user_dir, dir_name)
            self.mount_edit.setText(mount_point)
        
    def accept(self):
        """Valide et monte le volume."""
        path = self.path_edit.text()
        mount_point = self.mount_edit.text()
        password = self.password_edit.text()
        
        if not path:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un volume")
            return
            
        if not mount_point:
            QMessageBox.warning(self, "Erreur", "Veuillez spécifier un point de montage")
            return
            
        if not password:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer un mot de passe")
            return
            
        # Vérifier le point de montage
        valid, error = veracrypt.check_mount_point(mount_point)
        if not valid:
            QMessageBox.warning(self, "Erreur", error)
            return
            
        # Monter le volume
        success, error = veracrypt.mount_volume(path, mount_point, password)
        
        if success:
            # Si l'option favori est cochée et que ce n'est pas déjà un favori
            if not self.favorite_path and self.favorite_checkbox.isChecked() and self.favorite_checkbox.isVisible():
                # Demander le nom du favori
                name, ok = QInputDialog.getText(
                    self,
                    "Nom du favori",
                    "Entrez un nom pour ce favori :"
                )
                if ok and name:
                    print(f"Tentative d'ajout du favori : {name} ({path})")  # Debug
                    if self.favorites.add_favorite(name, path, self.is_device, mount_point):
                        print("Favori ajouté avec succès")  # Debug
                        self.favorite_added = True
                    else:
                        print("Échec de l'ajout du favori")  # Debug
                        QMessageBox.warning(
                            self,
                            "Erreur",
                            "Impossible d'ajouter le favori. Peut-être existe-t-il déjà ?"
                        )
            super().accept()
        else:
            QMessageBox.critical(self, "Erreur", f"Impossible de monter le volume : {error}")
            
    def was_favorite_added(self) -> bool:
        """Retourne True si un favori a été ajouté pendant le dialogue."""
        return self.favorite_added
