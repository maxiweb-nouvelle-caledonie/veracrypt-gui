"""
Fenêtre principale de l'application VeraCrypt GUI.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QTextEdit,
    QHBoxLayout, QFrame, QMessageBox,
    QSplitter, QListWidget
)
from PyQt6.QtCore import Qt, QTimer
from src.gui.mount_dialog import MountDialog
from src.gui.loading_dialog import LoadingDialog
from src.gui.mounted_volumes_list import MountedVolumesList
from src.utils import veracrypt, system
from src.constants import Constants

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.mounted_volumes = {}
        self.loading_dialog = None
        self.initUI()
        self._load_mounted_volumes()  # Chargement initial des volumes montés

    def initUI(self):
        """Initialise l'interface utilisateur."""
        self.setWindowTitle('VeraCrypt Manager')
        self.setGeometry(100, 100, 1000, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal vertical
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Boutons en haut
        button_layout = QHBoxLayout()
        self._add_buttons(button_layout)
        main_layout.addLayout(button_layout)
        
        # Splitter horizontal pour les colonnes redimensionnables
        splitter = QSplitter()
        main_layout.addWidget(splitter)
        
        # Colonne de gauche : Liste des volumes montés
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(5, 5, 5, 5)
        
        volumes_label = QLabel('Volumes Montés')
        volumes_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(volumes_label)
        
        self.mounted_volumes_list = MountedVolumesList(self)
        self.mounted_volumes_list.volume_unmounted.connect(self._on_volume_unmounted)
        left_layout.addWidget(self.mounted_volumes_list)
        
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Colonne de droite : Zone de logs
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Titre
        title = QLabel('VeraCrypt Manager')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(title)
        
        # Zone de logs
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        right_layout.addWidget(self.log_area)
        
        right_widget.setLayout(right_layout)
        splitter.addWidget(right_widget)
        
        # Définir les tailles initiales des colonnes (50% chacune)
        splitter.setSizes([400, 600])
        
    def _add_buttons(self, layout):
        """Ajoute les boutons à l'interface."""
        self.mount_file_button = QPushButton("Monter un fichier")
        self.mount_device_button = QPushButton("Monter un périphérique")
        self.unmount_button = QPushButton("Démonter un volume")
        self.test_button = QPushButton("Tester VeraCrypt List")
        self.cleanup_button = QPushButton("Nettoyer les points de montage")
        
        # Ajouter les boutons au layout
        layout.addWidget(self.mount_file_button)
        layout.addWidget(self.mount_device_button)
        layout.addWidget(self.unmount_button)
        layout.addWidget(self.test_button)
        layout.addWidget(self.cleanup_button)
        
        # Connecter les signaux
        self.mount_file_button.clicked.connect(self._mount_file)
        self.mount_device_button.clicked.connect(self._mount_device)
        self.unmount_button.clicked.connect(self._unmount_volume_button_clicked)
        self.test_button.clicked.connect(self._test_veracrypt_list)
        self.cleanup_button.clicked.connect(self._cleanup_mount_points)

    def log_message(self, message: str):
        """Ajoute un message dans la zone de logs."""
        self.log_area.append(message)

    def _mount_file(self):
        """Gère le montage d'un fichier."""
        dialog = MountDialog(self, is_device=False)
        self._center_dialog(dialog)
        if dialog.exec():
            self.log_message("Montage du fichier terminé")
            self._refresh_volumes_list()

    def _mount_device(self):
        """Gère le montage d'un périphérique."""
        dialog = MountDialog(self, is_device=True)
        self._center_dialog(dialog)
        if dialog.exec():
            self.log_message("Montage du périphérique terminé")
            self._refresh_volumes_list()

    def _unmount_volume_button_clicked(self):
        """Gestion du clic sur le bouton de démontage."""
        # Récupérer le volume sélectionné
        selected_items = self.mounted_volumes_list.selectedItems()
        if not selected_items:
            self._show_message(
                "Erreur",
                "Veuillez sélectionner un volume à démonter",
                QMessageBox.Icon.Warning
            )
            return
            
        mount_point = selected_items[0].data(Qt.ItemDataRole.UserRole)
        self.log_message(f"Tentative de démontage du volume: {mount_point}")
        
        # Montrer le loader
        self.show_loading("Démontage du volume en cours...")
        
        # Utiliser QTimer pour laisser l'interface se mettre à jour
        QTimer.singleShot(100, lambda: self._unmount_volume(mount_point))

    def _unmount_volume(self, mount_point):
        """Démonte un volume."""
        try:
            # Obtenir le slot associé
            slot = self.mounted_volumes.get(mount_point)
            if not slot:
                self._show_message(
                    "Erreur",
                    f"Impossible de trouver le slot pour {mount_point}",
                    QMessageBox.Icon.Critical
                )
                return
                
            self.log_message(f"Démontage du slot {slot} pour {mount_point}")
            
            # Démonter le volume
            success, message = veracrypt.unmount_volume(mount_point)
            self.log_message(f"Résultat du démontage: success={success}, message={message}")
            
            if success:
                self.log_message(f"Volume démonté avec succès: {mount_point}")
                # Mettre à jour la liste des volumes montés
                if mount_point in self.mounted_volumes:
                    del self.mounted_volumes[mount_point]
                self._refresh_volumes_list()
                self._show_message(
                    "Succès",
                    f"Volume démonté avec succès: {mount_point}"
                )
            else:
                self.log_message(f"Erreur lors du démontage: {message}")
                self._show_message(
                    "Erreur",
                    f"Erreur lors du démontage:\n{message}",
                    QMessageBox.Icon.Critical
                )
                # Rafraîchir la liste même en cas d'erreur
                self._refresh_volumes_list()
        finally:
            self.hide_loading()

    def _refresh_volumes_list(self):
        """Rafraîchit la liste des volumes montés."""
        self.show_loading("Rafraîchissement de la liste...")
        
        # Utiliser QTimer pour laisser l'interface se mettre à jour
        QTimer.singleShot(100, self._do_refresh_volumes_list)
        
    def _do_refresh_volumes_list(self):
        """Effectue le rafraîchissement de la liste."""
        try:
            self.log_message("Rafraîchissement de la liste des volumes montés...")
            self.mounted_volumes_list.clear()
            
            # Récupérer la liste des volumes montés
            mounted_volumes = veracrypt.list_mounted_volumes()
            self.log_message(f"Volumes trouvés: {mounted_volumes}")
            
            if mounted_volumes:
                for slot, mount_point in mounted_volumes:
                    self.log_message(f"Ajout du volume {mount_point} (slot {slot})")
                    self.mounted_volumes_list.add_volume(mount_point)
                    self.mounted_volumes[mount_point] = slot  # Stocker le slot pour le démontage
            else:
                self.log_message("Aucun volume monté")
                
        except Exception as e:
            self.log_message(f"Erreur lors du rafraîchissement: {str(e)}")
        finally:
            self.hide_loading()

    def _on_volume_unmounted(self, mount_point: str):
        """Appelé quand un volume est démonté depuis la liste."""
        self.log_message(f"Signal de démontage reçu pour: {mount_point}")
        if mount_point in self.mounted_volumes:
            del self.mounted_volumes[mount_point]
        self._refresh_volumes_list()

    def _test_veracrypt_list(self):
        """Teste la commande veracrypt --list."""
        self.show_loading("Test de VeraCrypt en cours...")
        
        # Utiliser QTimer pour laisser l'interface se mettre à jour
        QTimer.singleShot(100, self._do_test_veracrypt_list)
        
    def _do_test_veracrypt_list(self):
        """Effectue le test de VeraCrypt."""
        try:
            success, stdout, stderr = veracrypt.execute_veracrypt_command([
                'sudo',
                Constants.VERACRYPT_PATH,
                '--text',
                '--list'
            ])
            
            self.log_message("Test de veracrypt --list")
            if success:
                self.log_message(f"Sortie:\n{stdout}")
            else:
                self.log_message(f"Erreur:\n{stderr}")
                
            self._refresh_volumes_list()
        finally:
            self.hide_loading()
            
    def _cleanup_mount_points(self):
        """Nettoie les points de montage non utilisés."""
        self.show_loading("Nettoyage des points de montage...")
        
        # Utiliser QTimer pour laisser l'interface se mettre à jour
        QTimer.singleShot(100, self._do_cleanup_mount_points)
        
    def _do_cleanup_mount_points(self):
        """Effectue le nettoyage des points de montage."""
        try:
            success, message = system.cleanup_mount_points()
            
            if success:
                self.log_message(f"Succès: {message}")
                self._show_message(
                    "Succès",
                    message,
                    QMessageBox.Icon.Information
                )
            else:
                self.log_message(f"Erreur: {message}")
                self._show_message(
                    "Erreur",
                    f"Erreur lors du nettoyage:\n{message}",
                    QMessageBox.Icon.Critical
                )
                
            # Rafraîchir la liste des volumes montés
            self._refresh_volumes_list()
        finally:
            self.hide_loading()

    def show_loading(self, message="Chargement en cours..."):
        """Affiche le dialogue de chargement."""
        if not self.loading_dialog:
            self.loading_dialog = LoadingDialog(self, message)
            self._center_dialog(self.loading_dialog)
        else:
            self.loading_dialog.set_message(message)
        self.loading_dialog.show()
        
    def hide_loading(self):
        """Cache le dialogue de chargement."""
        if self.loading_dialog:
            self.loading_dialog.hide()
            
    def _center_dialog(self, dialog):
        """Centre un dialogue par rapport à la fenêtre principale."""
        # Obtenir la géométrie de la fenêtre principale
        main_geometry = self.geometry()
        main_center = main_geometry.center()
        
        # Obtenir la taille du dialogue
        dialog_size = dialog.sizeHint()
        
        # Calculer la position pour centrer le dialogue
        x = main_center.x() - dialog_size.width() // 2
        y = main_center.y() - dialog_size.height() // 2
        
        # Déplacer le dialogue
        dialog.move(x, y)

    def _show_message(self, title: str, message: str, icon: QMessageBox.Icon = QMessageBox.Icon.Information):
        """Affiche une boîte de dialogue centrée."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        self._center_dialog(msg_box)
        msg_box.exec()

    def _load_mounted_volumes(self):
        """Charge la liste des volumes montés au démarrage."""
        self.show_loading("Recherche des volumes montés...")
        
        # Utiliser QTimer pour laisser l'interface se mettre à jour
        QTimer.singleShot(100, self._do_load_mounted_volumes)
        
    def _do_load_mounted_volumes(self):
        """Effectue le chargement des volumes montés."""
        try:
            # Obtenir la liste des volumes montés
            volumes = veracrypt.list_mounted_volumes()
            
            # Mettre à jour la liste
            for slot, mount_point in volumes:
                self.mounted_volumes[mount_point] = slot
                
            self.log_message(f"Volumes chargés: {self.mounted_volumes}")
            if self.mounted_volumes:
                self._refresh_volumes_list()
        except Exception as e:
            self.log_message(f"Erreur lors du chargement des volumes: {str(e)}")
        finally:
            self.hide_loading()
