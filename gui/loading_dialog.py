from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt

class LoadingDialog(QDialog):
    def __init__(self, parent=None, message="Chargement en cours..."):
        super().__init__(parent)
        self.setup_ui(message)
        
    def setup_ui(self, message):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("Chargement")
        self.setFixedSize(300, 100)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        
        layout = QVBoxLayout()
        
        # Message
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)  # Mode indéterminé
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
        
    def set_message(self, message):
        """Met à jour le message."""
        self.message_label.setText(message)
