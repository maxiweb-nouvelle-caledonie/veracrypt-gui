"""
Assistant de création de volumes VeraCrypt.
"""

import os
from PyQt6.QtWidgets import (
    QWizard,
    QWizardPage,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QMessageBox,
    QFileDialog,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QHBoxLayout,
    QCheckBox,
    QWidget
)
from PyQt6.QtCore import Qt, QMetaObject, Q_ARG, pyqtSlot
from PyQt6.QtGui import QIcon
from utils import VolumeCreation, EntropyCollector
from .progress_dialog import ProgressDialog

class CreateVolumeWizard(QWizard):
    # Pages du wizard
    PAGE_VOLUME = 0
    PAGE_PASSWORD = 1
    PAGE_ENCRYPTION = 2
    PAGE_ENTROPY = 3
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setWindowTitle("Créer un volume VeraCrypt")
        
        # Propriétés du volume
        self.volume_path = None
        self.volume_size = None
        self.password = None
        self.encryption = None
        self.hash_algo = None
        self.filesystem = None
        self.random_data = None
        
        # Ajouter les pages
        self.setPage(self.PAGE_VOLUME, VolumePage(self))
        self.setPage(self.PAGE_PASSWORD, PasswordPage(self))
        self.setPage(self.PAGE_PASSWORD + 1, EncryptionPage(self))
        self.setPage(self.PAGE_PASSWORD + 2, EntropyPage(self))
        
        # Configuration du wizard
        self.setOption(QWizard.WizardOption.HaveHelpButton, False)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)

    def accept(self):
        """Appelé quand l'utilisateur clique sur Terminer."""
        # Récupérer toutes les informations
        volume_path = self.volume_path
        size = self.volume_size
        encryption = self.encryption
        hash_algo = self.hash_algo
        filesystem = self.filesystem
        password = self.password
        
        # Créer la boîte de dialogue de progression
        progress = ProgressDialog(self)
        progress.show()
        
        # Créer le volume
        def create_volume():
            success, message = VolumeCreation.create_volume(
                path=volume_path,
                password=password,
                size=size,
                encryption=encryption,
                hash_algo=hash_algo,
                filesystem=filesystem,
                random_data=self.random_data,
                progress_callback=progress.update_progress
            )
            
            # Mettre à jour la boîte de dialogue
            progress.done(success)
            
            # Utiliser invokeMethod pour appeler les méthodes Qt depuis le thread
            if success:
                QMetaObject.invokeMethod(self, "show_success_and_close", 
                                       Qt.ConnectionType.QueuedConnection,
                                       Q_ARG(str, message))
            else:
                QMetaObject.invokeMethod(self, "show_error", 
                                       Qt.ConnectionType.QueuedConnection,
                                       Q_ARG(str, message))
                progress.close()
        
        # Lancer la création dans un thread séparé
        from PyQt6.QtCore import QThread
        
        class CreationThread(QThread):
            def run(self):
                create_volume()
        
        self.creation_thread = CreationThread()
        self.creation_thread.start()
    
    @pyqtSlot(str)
    def show_success_and_close(self, message):
        """Affiche le message de succès et ferme le wizard."""
        QMessageBox.information(self, "Succès", message)
        super().accept()
    
    @pyqtSlot(str)
    def show_error(self, message):
        """Affiche le message d'erreur."""
        QMessageBox.critical(self, "Erreur", message)
        progress.close()

class EntropyPage(QWizardPage):
    """Page de collecte d'entropie."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Collecte d'entropie")
        self.setSubTitle("Déplacez votre souris pour générer de l'aléatoire nécessaire au chiffrement.")
        
        layout = QVBoxLayout()
        
        # Créer le collecteur d'entropie
        self.entropy_collector = EntropyCollector()
        self.entropy_collector.entropy_collected.connect(self._on_entropy_collected)
        layout.addWidget(self.entropy_collector)
        
        self.setLayout(layout)
        
    def initializePage(self):
        """Appelé quand la page est affichée."""
        self.entropy_collector.start_collecting()
        
    def isComplete(self) -> bool:
        """Vérifie si la page est complète."""
        return hasattr(self.wizard(), 'random_data') and self.wizard().random_data is not None
        
    def _on_entropy_collected(self, entropy: str):
        """Appelé quand l'entropie est collectée."""
        self.wizard().random_data = entropy
        self.completeChanged.emit()

class EncryptionPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Options de chiffrement")
        self.setSubTitle("Choisissez les algorithmes de chiffrement et de hachage.")
        
        layout = QVBoxLayout()
        
        # Algorithme de chiffrement
        encryption_label = QLabel("Algorithme de chiffrement :")
        self.encryption_combo = QComboBox()
        self.encryption_combo.addItems(VolumeCreation.ENCRYPTION_ALGORITHMS.keys())
        layout.addWidget(encryption_label)
        layout.addWidget(self.encryption_combo)
        
        # Algorithme de hachage
        hash_label = QLabel("Algorithme de hachage :")
        self.hash_combo = QComboBox()
        self.hash_combo.addItems(VolumeCreation.HASH_ALGORITHMS.keys())
        layout.addWidget(hash_label)
        layout.addWidget(self.hash_combo)
        
        # Système de fichiers
        filesystem_label = QLabel("Système de fichiers :")
        self.filesystem_combo = QComboBox()
        self.filesystem_combo.addItems(VolumeCreation.FILESYSTEMS.keys())
        layout.addWidget(filesystem_label)
        layout.addWidget(self.filesystem_combo)
        
        self.setLayout(layout)
        
    def validatePage(self) -> bool:
        # Stocker les valeurs dans le wizard
        self.wizard().encryption = self.encryption_combo.currentText()
        self.wizard().hash_algo = self.hash_combo.currentText()
        self.wizard().filesystem = self.filesystem_combo.currentText()
        return True

class PasswordPage(QWizardPage):
    """Page de saisie du mot de passe."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Mot de passe")
        self.setSubTitle("Choisissez un mot de passe pour votre volume.")
        
        layout = QVBoxLayout()
        
        # Champ mot de passe
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Entrez votre mot de passe")
        self.password_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.password_edit)
        
        # Champ confirmation
        self.confirm_edit = QLineEdit()
        self.confirm_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_edit.setPlaceholderText("Confirmez votre mot de passe")
        self.confirm_edit.textChanged.connect(self.on_text_changed)
        layout.addWidget(self.confirm_edit)
        
        # Option pour afficher le mot de passe
        self.show_password = QCheckBox("Afficher le mot de passe")
        self.show_password.stateChanged.connect(self.toggle_password_visibility)
        layout.addWidget(self.show_password)
        
        # Message d'erreur
        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red")
        layout.addWidget(self.error_label)
        
        self.setLayout(layout)
        
        # État de validation
        self._is_valid = False
        
    def on_text_changed(self):
        """Appelé quand le texte change dans un des champs."""
        self._is_valid = self.validate_password()
        self.completeChanged.emit()
        
    def validate_password(self):
        """Valide le mot de passe saisi."""
        password = self.password_edit.text()
        confirm = self.confirm_edit.text()
        
        # Vérifier si le mot de passe est vide
        if not password:
            self.error_label.setText("Le mot de passe ne peut pas être vide")
            return False
            
        # Vérifier si les mots de passe correspondent
        if password != confirm:
            self.error_label.setText("Les mots de passe ne correspondent pas")
            return False
        
        # Tout est OK
        self.error_label.clear()
        return True
        
    def isComplete(self):
        """Détermine si la page est complète."""
        return self._is_valid
        
    def toggle_password_visibility(self, state):
        """Change la visibilité du mot de passe."""
        mode = QLineEdit.EchoMode.Normal if state else QLineEdit.EchoMode.Password
        self.password_edit.setEchoMode(mode)
        self.confirm_edit.setEchoMode(mode)
        
    def validatePage(self):
        """Valide la page et sauvegarde le mot de passe."""
        if not self._is_valid:
            return False
            
        self.wizard().password = self.password_edit.text()
        return True

class VolumePage(QWizardPage):
    def __init__(self, wizard):
        super().__init__(wizard)
        self.setTitle("Volume")
        self.setSubTitle("Choisissez l'emplacement et la taille du volume.")
        
        layout = QVBoxLayout()
        
        # Emplacement du volume
        layout.addWidget(QLabel("Emplacement du volume :"))
        
        path_widget = QWidget()
        path_layout = QHBoxLayout()
        path_layout.setContentsMargins(0, 0, 0, 0)
        
        self.path_edit = QLineEdit()
        path_layout.addWidget(self.path_edit)
        
        browse_button = QPushButton("Parcourir...")
        browse_button.clicked.connect(self._browse_volume)
        path_layout.addWidget(browse_button)
        
        path_widget.setLayout(path_layout)
        layout.addWidget(path_widget)
        
        # Taille du volume
        layout.addWidget(QLabel("Taille du volume :"))
        
        size_widget = QWidget()
        size_layout = QHBoxLayout()
        size_layout.setContentsMargins(0, 0, 0, 0)
        
        self.size_spin = QSpinBox()
        self.size_spin.setMinimum(1)
        self.size_spin.setMaximum(1024 * 1024)  # 1 PB
        size_layout.addWidget(self.size_spin)
        
        self.size_unit = QComboBox()
        self.size_unit.addItems(['MB', 'GB', 'TB'])
        self.size_unit.setCurrentText('GB')
        size_layout.addWidget(self.size_unit)
        
        size_widget.setLayout(size_layout)
        layout.addWidget(size_widget)
        
        self.setLayout(layout)
        
    def _browse_volume(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Choisir l'emplacement du volume",
            "",
            "Volumes VeraCrypt (*.tc);;Tous les fichiers (*.*)"
        )
        if path:
            self.path_edit.setText(path)
            
    def validatePage(self) -> bool:
        if not self.path_edit.text():
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez choisir un emplacement pour le volume."
            )
            return False
            
        if os.path.exists(self.path_edit.text()):
            QMessageBox.warning(
                self,
                "Erreur",
                "Un fichier existe déjà à cet emplacement."
            )
            return False
            
        self.wizard().volume_path = self.path_edit.text()
        self.wizard().volume_size = VolumeCreation.format_size(
            self.size_spin.value(),
            self.size_unit.currentText()
        )
        return True
