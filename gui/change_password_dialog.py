"""
Assistant de modification du mot de passe d'un volume VeraCrypt.
"""

from PyQt6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QCheckBox,
    QPushButton,
    QFileDialog
)
from PyQt6.QtCore import Qt
from utils.volume_creation import VolumeCreation
import logging
import os

logger = logging.getLogger(__name__)

class ChangePasswordWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Modifier le mot de passe")
        self.setMinimumWidth(600)
        
        # Pages du wizard
        self.addPage(SelectVolumePage(self))
        self.addPage(CurrentPasswordPage(self))
        self.addPage(NewPasswordPage(self))
        
        # Propriétés
        self.volume_path = None
        self.current_password = None
        self.new_password = None
        self.current_keyfile = None
        self.new_keyfile = None

class SelectVolumePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Sélection du volume")
        self.setSubTitle("Sélectionnez le volume dont vous souhaitez modifier le mot de passe")
        
        layout = QVBoxLayout()
        
        # Sélection du fichier
        file_layout = QVBoxLayout()
        self.path_label = QLabel("Chemin du volume :")
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self._browse_volume)
        
        file_layout.addWidget(self.path_label)
        file_layout.addWidget(self.path_edit)
        file_layout.addWidget(browse_button)
        layout.addLayout(file_layout)
        
        self.setLayout(layout)
        
    def _browse_volume(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un volume VeraCrypt",
            "",
            "Volumes VeraCrypt (*.tc);;Tous les fichiers (*.*)"
        )
        if file_path:
            self.path_edit.setText(file_path)
            
    def validatePage(self):
        path = self.path_edit.text()
        if not path:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un volume")
            return False
            
        if not os.path.exists(path):
            QMessageBox.warning(self, "Erreur", "Le fichier n'existe pas")
            return False
            
        self.wizard().volume_path = path
        return True

class CurrentPasswordPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Mot de passe actuel")
        self.setSubTitle("Entrez le mot de passe actuel du volume")
        
        layout = QVBoxLayout()
        
        # Champ mot de passe actuel
        self.current_password = QLineEdit()
        self.current_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.current_password.setPlaceholderText("Entrez le mot de passe actuel")
        layout.addWidget(QLabel("Mot de passe actuel :"))
        layout.addWidget(self.current_password)
        
        # Option fichier clé actuel
        self.use_keyfile = QCheckBox("Utiliser un fichier clé")
        self.use_keyfile.stateChanged.connect(self._toggle_keyfile)
        layout.addWidget(self.use_keyfile)
        
        self.keyfile_edit = QLineEdit()
        self.keyfile_edit.setReadOnly(True)
        self.keyfile_edit.setVisible(False)
        layout.addWidget(self.keyfile_edit)
        
        self.browse_keyfile = QPushButton("Parcourir...")
        self.browse_keyfile.clicked.connect(self._browse_keyfile)
        self.browse_keyfile.setVisible(False)
        layout.addWidget(self.browse_keyfile)
        
        # Option pour afficher le mot de passe
        self.show_password = QCheckBox("Afficher le mot de passe")
        self.show_password.stateChanged.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password)
        
        self.setLayout(layout)
        
    def _toggle_keyfile(self, state):
        self.keyfile_edit.setVisible(state)
        self.browse_keyfile.setVisible(state)
        
    def _browse_keyfile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier clé",
            "",
            "Tous les fichiers (*.*)"
        )
        if file_path:
            self.keyfile_edit.setText(file_path)
            
    def _toggle_password_visibility(self, state):
        self.current_password.setEchoMode(
            QLineEdit.EchoMode.Normal if state else QLineEdit.EchoMode.Password
        )
        
    def validatePage(self):
        password = self.current_password.text()
        if not password:
            QMessageBox.warning(self, "Erreur", "Veuillez entrer le mot de passe actuel")
            return False
            
        self.wizard().current_password = password
        self.wizard().current_keyfile = self.keyfile_edit.text() if self.use_keyfile.isChecked() else None
        return True

class NewPasswordPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Nouveau mot de passe")
        self.setSubTitle("Entrez le nouveau mot de passe pour le volume")
        
        layout = QVBoxLayout()
        
        # Nouveau mot de passe
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Entrez le nouveau mot de passe")
        self.password_edit.textChanged.connect(self._validate_password)
        layout.addWidget(QLabel("Nouveau mot de passe :"))
        layout.addWidget(self.password_edit)
        
        # Confirmation
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText("Confirmez le nouveau mot de passe")
        self.confirm_edit.textChanged.connect(self._validate_password)
        layout.addWidget(QLabel("Confirmation :"))
        layout.addWidget(self.confirm_edit)
        
        # Option nouveau fichier clé
        self.use_keyfile = QCheckBox("Utiliser un fichier clé")
        self.use_keyfile.stateChanged.connect(self._toggle_keyfile)
        layout.addWidget(self.use_keyfile)
        
        self.keyfile_edit = QLineEdit()
        self.keyfile_edit.setReadOnly(True)
        self.keyfile_edit.setVisible(False)
        layout.addWidget(self.keyfile_edit)
        
        self.browse_keyfile = QPushButton("Parcourir...")
        self.browse_keyfile.clicked.connect(self._browse_keyfile)
        self.browse_keyfile.setVisible(False)
        layout.addWidget(self.browse_keyfile)
        
        # Option pour afficher les mots de passe
        self.show_password = QCheckBox("Afficher les mots de passe")
        self.show_password.stateChanged.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password)
        
        # Message d'erreur
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)
        
        self.setLayout(layout)
        
    def _toggle_keyfile(self, state):
        self.keyfile_edit.setVisible(state)
        self.browse_keyfile.setVisible(state)
        
    def _browse_keyfile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier clé",
            "",
            "Tous les fichiers (*.*)"
        )
        if file_path:
            self.keyfile_edit.setText(file_path)
            
    def _toggle_password_visibility(self, state):
        mode = QLineEdit.EchoMode.Normal if state else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)
        self.confirm_edit.setEchoMode(mode)
        
    def _validate_password(self):
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        
        if not password:
            self.error_label.setText("Le mot de passe ne peut pas être vide")
            return False
            
        if password != confirm:
            self.error_label.setText("Les mots de passe ne correspondent pas")
            return False
            
        if len(password) < 12:
            self.error_label.setText("Le mot de passe doit faire au moins 12 caractères")
            return False
            
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            self.error_label.setText(
                "Le mot de passe doit contenir: majuscules, minuscules, "
                "chiffres et caractères spéciaux"
            )
            return False
            
        self.error_label.clear()
        return True
        
    def validatePage(self):
        if not self._validate_password():
            return False
            
        self.wizard().new_password = self.password_edit.text()
        self.wizard().new_keyfile = self.keyfile_edit.text() if self.use_keyfile.isChecked() else None
        return True
