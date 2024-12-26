from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QMessageBox
)
from src.utils import system

class DeviceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_device = None
        self.devices = []
        self.setup_ui()
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Sélectionner un périphérique")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Liste des périphériques
        self.device_list = QListWidget()
        layout.addWidget(self.device_list)
        
        # Boutons
        button_layout = QHBoxLayout()
        cancel_btn = QPushButton("Annuler")
        ok_btn = QPushButton("OK")
        cancel_btn.clicked.connect(self.reject)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(ok_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Charger les périphériques
        self._load_devices()
        
    def _load_devices(self):
        """Charge la liste des périphériques."""
        self.devices = system.list_devices()
        
        if not self.devices:
            QMessageBox.warning(
                self,
                "Erreur",
                "Aucun périphérique disponible"
            )
            self.reject()
            return
            
        # Remplir la liste
        for _, name in self.devices:
            self.device_list.addItem(name)
            
    def accept(self):
        """Valide la sélection."""
        current_row = self.device_list.currentRow()
        if current_row >= 0:
            self.selected_device = self.devices[current_row][0]  # Chemin du périphérique
            super().accept()
        else:
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez sélectionner un périphérique"
            )
