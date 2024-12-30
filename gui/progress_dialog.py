from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton
from PyQt6.QtCore import Qt, QTimer, QMetaObject, Q_ARG, pyqtSlot

class ProgressDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Création du volume")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # Layout principal
        layout = QVBoxLayout()
        
        # Label pour le statut
        self.status_label = QLabel("Initialisation...")
        layout.addWidget(self.status_label)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)
        
        # Label pour la vitesse et le temps restant
        self.speed_label = QLabel()
        layout.addWidget(self.speed_label)
        
        # Bouton pour forcer la fermeture
        self.force_close_button = QPushButton("Fermer")
        self.force_close_button.clicked.connect(self.force_close)
        self.force_close_button.setVisible(False)  # Caché par défaut
        layout.addWidget(self.force_close_button)
        
        self.setLayout(layout)
        
        # Timer pour mettre à jour l'interface
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_progress)
        self.timer.start(200)  # Mise à jour toutes les 200ms
        
        # Dernière ligne traitée
        self.last_line = ""
    
    @pyqtSlot(str)
    def update_status(self, text):
        """Met à jour le texte de statut."""
        self.status_label.setText(text)
        if text in ["Volume créé avec succès !", "Erreur lors de la création du volume"]:
            self.timer.stop()
    
    @pyqtSlot()
    def stop_timer(self):
        """Arrête le timer."""
        self.timer.stop()
    
    @pyqtSlot()
    def close_dialog(self):
        """Ferme la boîte de dialogue."""
        self.close()
    
    @pyqtSlot(int)
    def set_progress(self, value):
        """Met à jour la valeur de la barre de progression."""
        self.progress_bar.setValue(value)
    
    @pyqtSlot(str)
    def set_speed(self, text):
        """Met à jour le texte de vitesse."""
        self.speed_label.setText(text)
        
    def update_progress(self, line: str):
        """Met à jour l'interface avec la ligne de progression."""
        self.last_line = line
        
        # Analyser la ligne de progression
        if "Done:" in line:
            try:
                # Extraire le pourcentage
                percent = float(line.split("Done:")[1].split("%")[0].strip().replace(",", "."))
                QMetaObject.invokeMethod(self, "set_progress", 
                                       Qt.ConnectionType.QueuedConnection,
                                       Q_ARG(int, int(percent)))
                
                # Extraire la vitesse
                speed = line.split("Speed:")[1].split("Left:")[0].strip()
                
                # Extraire le temps restant
                time_left = line.split("Left:")[1].strip()
                
                # Mettre à jour les labels
                QMetaObject.invokeMethod(self, "update_status", 
                                       Qt.ConnectionType.QueuedConnection,
                                       Q_ARG(str, "Création du volume en cours..."))
                QMetaObject.invokeMethod(self, "set_speed", 
                                       Qt.ConnectionType.QueuedConnection,
                                       Q_ARG(str, f"Vitesse : {speed} | Temps restant : {time_left}"))
            except:
                pass
        
    def check_progress(self):
        """Appelé périodiquement pour vérifier la progression."""
        # Cette méthode sera appelée par le timer
        pass
        
    def done(self, success: bool):
        """Appelé quand la création est terminée."""
        if success:
            QMetaObject.invokeMethod(self, "update_status", 
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(str, "Volume créé avec succès !"))
            QMetaObject.invokeMethod(self, "set_progress", 
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(int, 100))
            QMetaObject.invokeMethod(self, "force_close",
                                   Qt.ConnectionType.QueuedConnection)
        else:
            QMetaObject.invokeMethod(self, "update_status",
                                   Qt.ConnectionType.QueuedConnection,
                                   Q_ARG(str, "Erreur lors de la création du volume"))
            QMetaObject.invokeMethod(self, "force_close",
                                   Qt.ConnectionType.QueuedConnection)
        
    @pyqtSlot()
    def force_close(self):
        """Force la fermeture de la fenêtre."""
        self.timer.stop()
        self.close()
        
    def closeEvent(self, event):
        """Gérer la fermeture de la fenêtre."""
        if self.force_close_button.isVisible():
            event.accept()
        else:
            self.force_close_button.setVisible(True)
            event.ignore()
