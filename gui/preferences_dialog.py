"""
Dialogue des préférences.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QCheckBox,
    QDialogButtonBox, QFileDialog,
    QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt
from utils.preferences import preferences
from utils.themes import THEMES

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Préférences")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Groupe Apparence
        appearance_group = QGroupBox("Apparence")
        appearance_layout = QVBoxLayout()
        
        # Thème
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("Thème :"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEMES.keys())
        self.theme_combo.setCurrentText(preferences.get('theme'))
        theme_layout.addWidget(self.theme_combo)
        appearance_layout.addLayout(theme_layout)
        
        # Notifications
        self.show_notifications_checkbox = QCheckBox("Afficher les notifications")
        self.show_notifications_checkbox.setChecked(preferences.get('show_notifications', True))
        appearance_layout.addWidget(self.show_notifications_checkbox)
        
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)
        
        # Groupe Points de montage
        mount_group = QGroupBox("Points de montage")
        mount_layout = QVBoxLayout()
        
        # Options de nettoyage
        self.auto_clean_checkbox = QCheckBox("Nettoyer automatiquement les points de montage vides")
        self.auto_clean_checkbox.setChecked(preferences.get('auto_clean_mount_points', True))
        mount_layout.addWidget(self.auto_clean_checkbox)
        
        # Vérification au démarrage
        self.check_on_start_checkbox = QCheckBox("Vérifier l'intégrité des points de montage au démarrage")
        self.check_on_start_checkbox.setChecked(preferences.get('check_mount_points_on_start', True))
        mount_layout.addWidget(self.check_on_start_checkbox)
        
        # Répertoire de montage par défaut
        mount_dir_layout = QHBoxLayout()
        mount_dir_layout.addWidget(QLabel("Répertoire de montage par défaut :"))
        self.mount_dir_label = QLabel(preferences.get('default_mount_dir'))
        mount_dir_layout.addWidget(self.mount_dir_label)
        mount_dir_button = QPushButton("Parcourir...")
        mount_dir_button.clicked.connect(self._choose_mount_dir)
        mount_dir_layout.addWidget(mount_dir_button)
        mount_layout.addLayout(mount_dir_layout)
        
        mount_group.setLayout(mount_layout)
        layout.addWidget(mount_group)
        
        # Boutons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
    def _choose_mount_dir(self):
        """Ouvre un dialogue pour choisir le répertoire de montage par défaut."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Choisir le répertoire de montage par défaut",
            preferences.get('default_mount_dir')
        )
        if directory:
            self.mount_dir_label.setText(directory)
            
    def accept(self):
        """Sauvegarde les préférences."""
        preferences.set('auto_clean_mount_points', self.auto_clean_checkbox.isChecked())
        preferences.set('check_mount_points_on_start', self.check_on_start_checkbox.isChecked())
        preferences.set('show_notifications', self.show_notifications_checkbox.isChecked())
        preferences.set('default_mount_dir', self.mount_dir_label.text())
        preferences.set('theme', self.theme_combo.currentText())
        super().accept()
