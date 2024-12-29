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
from PyQt6.QtGui import QIcon, QAction
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
        
        # Initialiser les icônes
        self._init_icons()
        
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
        
    def _init_icons(self):
        """Initialise les icônes."""
        # Icône par défaut pour les volumes
        self.volume_icon = QIcon.fromTheme('drive-harddisk')
        # Icône pour les périphériques
        self.device_icon = QIcon.fromTheme('drive-removable-media')
        # Icône pour les fichiers
        self.file_icon = QIcon.fromTheme('media-flash')
        
    def setup_ui(self):
        """Configure l'interface utilisateur."""
        self.setWindowTitle("VeraCrypt GUI")
        self.setMinimumSize(800, 600)
        
        # Créer la barre de menu
        self._setup_menu_bar()
        
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
        
        mount_file_button = QPushButton()
        mount_file_button.setIcon(self.file_icon)
        mount_file_button.setText("Monter un fichier")
        mount_file_button.clicked.connect(lambda: self._show_mount_dialog(False))
        button_layout.addWidget(mount_file_button)
        
        mount_device_button = QPushButton()
        mount_device_button.setIcon(self.device_icon)
        mount_device_button.setText("Monter un périphérique")
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
        
    def _setup_menu_bar(self):
        """Configure la barre de menu."""
        menubar = self.menuBar()
        
        # Menu Monter
        mount_menu = menubar.addMenu("Monter")
        
        # Action Monter un fichier
        mount_file_action = QAction(self.file_icon, "Fichier...", self)
        mount_file_action.triggered.connect(lambda: self._show_mount_dialog(False))
        mount_menu.addAction(mount_file_action)
        
        # Action Monter un périphérique
        mount_device_action = QAction(self.device_icon, "Périphérique...", self)
        mount_device_action.triggered.connect(lambda: self._show_mount_dialog(True))
        mount_menu.addAction(mount_device_action)
        
        # Menu Favoris
        favorites_menu = menubar.addMenu("Favoris")
        
        # Ajouter les favoris au menu
        for favorite in self.favorites.get_favorites():
            action = QAction(
                self.device_icon if favorite['is_device'] else self.file_icon,
                favorite['name'],
                self
            )
            # Créer un QListWidgetItem temporaire pour le favori
            temp_item = QListWidgetItem()
            temp_item.setData(Qt.ItemDataRole.UserRole, favorite['volume_path'])
            action.triggered.connect(
                lambda checked, item=temp_item: self._mount_favorite(item)
            )
            favorites_menu.addAction(action)
            
        # Si aucun favori, ajouter une action désactivée
        if not self.favorites.get_favorites():
            no_favorites = QAction("Aucun favori", self)
            no_favorites.setEnabled(False)
            favorites_menu.addAction(no_favorites)
            
        # Action Quitter (directement dans la barre de menu)
        quit_action = QAction("Quitter", self)
        quit_action.triggered.connect(self.close)
        menubar.addAction(quit_action)
            
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
        try:
            # Récupérer le chemin du favori
            favorite_path = item.data(Qt.ItemDataRole.UserRole)
            if not favorite_path:
                return
                
            # Récupérer les informations du favori
            favorite = self.favorites.get_favorite(favorite_path)
            if not favorite:
                return
                
            # Récupérer le point de montage configuré ou en générer un nouveau
            mount_point = favorite.get('mount_point') or veracrypt.generate_mount_point()
            
            # Vérifier si un mot de passe est enregistré
            password = self.favorites.get_favorite_password(favorite_path)
            
            if password:
                # Si on a le mot de passe, monter directement
                self.log_message(f"Montage automatique du favori {favorite['name']}...")
                
                # Afficher le dialogue de chargement
                self.loading_dialog = LoadingDialog(self)
                self.loading_dialog.show()
                
                # Monter le volume
                success, error = veracrypt.mount_volume(favorite_path, mount_point, password)
                
                # Fermer le dialogue de chargement
                if self.loading_dialog:
                    self.loading_dialog.close()
                    self.loading_dialog = None
                
                if success:
                    self.log_message(f"Volume monté avec succès sur {mount_point}")
                    self._refresh_mounted_volumes()
                else:
                    self.log_message(f"Erreur lors du montage : {error}")
                    QMessageBox.critical(
                        self,
                        "Erreur",
                        f"Impossible de monter le volume : {error}"
                    )
            else:
                # Si pas de mot de passe, afficher le dialogue de montage
                self._show_mount_dialog(favorite.get('is_device', False), favorite_path)
                
        except Exception as e:
            self.log_message(f"Erreur lors du montage du favori : {str(e)}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors du montage du favori : {str(e)}"
            )
            
    def _remove_favorite(self, item):
        """Supprime un favori."""
        # Récupérer le chemin du volume directement
        volume_path = item.data(Qt.ItemDataRole.UserRole)
        if not volume_path:
            return
            
        # Récupérer le nom du favori pour l'afficher dans le message
        favorite = self.favorites.get_favorite(volume_path)
        if not favorite:
            return
            
        # Demander confirmation
        reply = QMessageBox.question(
            self,
            "Confirmation",
            f"Voulez-vous vraiment supprimer le favori {favorite['name']} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.favorites.remove_favorite(volume_path):
                self.log_message(f"Favori {favorite['name']} supprimé")
                # Rafraîchir la liste des favoris
                self._refresh_favorites()
            else:
                self.log_message(f"Erreur lors de la suppression du favori {favorite['name']}")
                QMessageBox.critical(
                    self,
                    "Erreur",
                    "Impossible de supprimer le favori"
                )
            
    def _refresh_favorites(self):
        """Rafraîchit la liste des favoris."""
        self.log_message("Début du rafraîchissement des favoris")
        
        # Rafraîchir la liste
        self.favorites_list.clear()
        favorites = self.favorites.get_favorites()
        self.log_message(f"Nombre de favoris trouvés : {len(favorites)}")
        
        for favorite in favorites:
            self.log_message(f"Ajout du favori : {favorite['name']} ({favorite['volume_path']})")
            item = QListWidgetItem(favorite['name'])
            item.setData(Qt.ItemDataRole.UserRole, favorite['volume_path'])
            item.setIcon(self.device_icon if favorite['is_device'] else self.file_icon)
            self.favorites_list.addItem(item)
            
        # Rafraîchir le menu des favoris
        self._refresh_favorites_menu()
        
        self.log_message("Fin du rafraîchissement des favoris")
        
    def _refresh_favorites_menu(self):
        """Rafraîchit le menu des favoris."""
        # Trouver le menu des favoris
        for action in self.menuBar().actions():
            if action.text() == "Favoris":
                favorites_menu = action.menu()
                # Effacer le menu
                favorites_menu.clear()
                
                # Ajouter les favoris au menu
                for favorite in self.favorites.get_favorites():
                    action = QAction(
                        self.device_icon if favorite['is_device'] else self.file_icon,
                        favorite['name'],
                        self
                    )
                    action.triggered.connect(
                        lambda checked, f=favorite: self._show_mount_dialog(f['is_device'], f['volume_path'])
                    )
                    favorites_menu.addAction(action)
                
                # Si aucun favori, ajouter une action désactivée
                if not self.favorites.get_favorites():
                    no_favorites = QAction("Aucun favori", self)
                    no_favorites.setEnabled(False)
                    favorites_menu.addAction(no_favorites)
                break
        
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
