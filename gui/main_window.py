"""
Fenêtre principale de l'application VeraCrypt GUI.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QTextEdit,
    QHBoxLayout, QFrame, QMessageBox,
    QSplitter, QListWidget, QListWidgetItem,
    QMenu
)
from PyQt6.QtCore import Qt
from gui.mount_dialog import MountDialog
from gui.loading_dialog import LoadingDialog
from gui.mounted_volumes_list import MountedVolumesList
from utils import veracrypt, system
from utils.sudo_session import sudo_session
from utils.favorites import Favorites
from constants import Constants
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loading_dialog = None
        self.favorites = Favorites()
        self.setup_ui()
        
        # Initialiser la session sudo
        self.log_message("Initialisation de la session sudo...")
        if not sudo_session.initialize_session():
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible d'initialiser la session sudo.\n"
                "L'application nécessite des droits administrateur pour fonctionner."
            )
            sys.exit(1)
            
        self.log_message("Session sudo initialisée avec succès")
        self._load_mounted_volumes()  # Chargement initial des volumes montés

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("VeraCrypt GUI")
        self.setMinimumSize(800, 600)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Panneau de gauche (favoris)
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)
        
        # Liste des favoris
        favorites_label = QLabel("Favoris")
        left_layout.addWidget(favorites_label)
        
        self.favorites_list = QListWidget()
        self.favorites_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.favorites_list.customContextMenuRequested.connect(self._show_favorite_context_menu)
        self.favorites_list.itemDoubleClicked.connect(self._mount_favorite)
        left_layout.addWidget(self.favorites_list)
        
        main_layout.addWidget(left_panel)
        
        # Panneau de droite
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Boutons d'action
        button_layout = QHBoxLayout()
        
        mount_file_button = QPushButton("Monter un fichier")
        mount_file_button.clicked.connect(lambda: self._show_mount_dialog(False))
        button_layout.addWidget(mount_file_button)
        
        mount_device_button = QPushButton("Monter un périphérique")
        mount_device_button.clicked.connect(lambda: self._show_mount_dialog(True))
        button_layout.addWidget(mount_device_button)
        
        right_layout.addLayout(button_layout)
        
        # Liste des volumes montés
        mounted_label = QLabel("Volumes montés")
        right_layout.addWidget(mounted_label)
        
        self.mounted_list = MountedVolumesList(self)
        self.mounted_list.volume_unmounted.connect(self._on_volume_unmounted)
        right_layout.addWidget(self.mounted_list)
        
        # Zone de logs
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        right_layout.addWidget(self.log_area)
        
        main_layout.addWidget(right_panel)
        
        # Rafraîchir les listes
        self._refresh_favorites()
        self._refresh_mounted_volumes()
        
    def _show_mount_dialog(self, is_device: bool, favorite_path: str = None):
        """Affiche le dialogue de montage."""
        dialog = MountDialog(self, is_device, favorite_path)
        result = dialog.exec()
        self.log_message(f"Résultat du dialogue : {result}")
        
        if result:
            self.log_message("Dialogue de montage fermé avec succès")
            self._refresh_mounted_volumes()
            
            # Vérifier si un favori a été ajouté
            was_added = dialog.was_favorite_added()
            self.log_message(f"Favori ajouté ? {was_added}")
            
            if was_added:
                self.log_message("Un favori a été ajouté, rafraîchissement de la liste")
                # Recharger les favoris depuis le fichier
                self.favorites = Favorites()
                self._refresh_favorites()
            else:
                self.log_message("Aucun favori n'a été ajouté")
            
    def _show_favorite_context_menu(self, position):
        """Affiche le menu contextuel pour un favori."""
        item = self.favorites_list.itemAt(position)
        if item is None:
            return
            
        menu = QMenu()
        mount_action = menu.addAction("Monter")
        remove_action = menu.addAction("Supprimer")
        
        action = menu.exec(self.favorites_list.mapToGlobal(position))
        if action == mount_action:
            self._mount_favorite(item)
        elif action == remove_action:
            self._remove_favorite(item)
            
    def _mount_favorite(self, item):
        """Monte un volume favori."""
        favorite = item.data(Qt.ItemDataRole.UserRole)
        self._show_mount_dialog(favorite['is_device'], favorite['volume_path'])
        
    def _remove_favorite(self, item):
        """Supprime un favori."""
        favorite = item.data(Qt.ItemDataRole.UserRole)
        if self.favorites.remove_favorite(favorite['volume_path']):
            self._refresh_favorites()
            
    def _refresh_favorites(self):
        """Rafraîchit la liste des favoris."""
        self.log_message("Début du rafraîchissement des favoris")
        self.favorites_list.clear()
        favorites = self.favorites.get_favorites()
        self.log_message(f"Nombre de favoris trouvés : {len(favorites)}")
        
        for favorite in favorites:
            self.log_message(f"Ajout du favori : {favorite['name']} ({favorite['volume_path']})")
            item = QListWidgetItem(favorite['name'])
            item.setData(Qt.ItemDataRole.UserRole, favorite)
            self.favorites_list.addItem(item)
            
        self.log_message("Fin du rafraîchissement des favoris")
            
    def _refresh_mounted_volumes(self):
        """Rafraîchit la liste des volumes montés."""
        try:
            volumes = veracrypt.list_mounted_volumes()
            self.mounted_list.clear()
            
            for slot, mount_point in volumes:
                item = QListWidgetItem(f"{mount_point}")
                item.setData(Qt.ItemDataRole.UserRole, (slot, mount_point))
                self.mounted_list.addItem(item)
                
        except Exception as e:
            self.log_message(f"Erreur lors du rafraîchissement des volumes montés : {str(e)}")
            
    def _on_volume_unmounted(self, mount_point: str):
        """Appelé quand un volume est démonté."""
        self._refresh_mounted_volumes()
        self.log_message(f"Volume démonté : {mount_point}")

    def log_message(self, message: str):
        """Ajoute un message dans la zone de logs."""
        self.log_area.append(message)

    def _load_mounted_volumes(self):
        """Charge la liste des volumes montés."""
        self.show_loading("Recherche des volumes montés...")
        try:
            volumes = veracrypt.list_mounted_volumes()
            
            # Mettre à jour la liste
            for slot, mount_point in volumes:
                item = QListWidgetItem(f"{mount_point}")
                item.setData(Qt.ItemDataRole.UserRole, (slot, mount_point))
                self.mounted_list.addItem(item)
                
            self.log_message(f"Volumes chargés: {volumes}")
        except Exception as e:
            self.log_message(f"Erreur lors du chargement des volumes: {str(e)}")
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

    def _on_favorite_added(self):
        """Appelé quand un favori est ajouté."""
        self._refresh_favorites()
        self.log_message("Favori ajouté avec succès")
