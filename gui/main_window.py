"""
Fenêtre principale de l'application VeraCrypt GUI.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, 
    QPushButton, QLabel, QTextEdit,
    QHBoxLayout, QFrame, QMessageBox,
    QSplitter, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt
from src.gui.mount_dialog import MountDialog
from src.gui.loading_dialog import LoadingDialog
from src.gui.mounted_volumes_list import MountedVolumesList
from src.utils import veracrypt, system
from src.utils.sudo_session import sudo_session
from src.constants import Constants
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.loading_dialog = None
        self.initUI()
        
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
        self.unmount_button.clicked.connect(self._on_unmount_volume)
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
            self._refresh_mounted_volumes()

    def _mount_device(self):
        """Gère le montage d'un périphérique."""
        dialog = MountDialog(self, is_device=True)
        self._center_dialog(dialog)
        if dialog.exec():
            self.log_message("Montage du périphérique terminé")
            self._refresh_mounted_volumes()

    def _refresh_mounted_volumes(self):
        """Rafraîchit la liste des volumes montés."""
        try:
            self.log_message("Rafraîchissement de la liste des volumes montés...")
            volumes = veracrypt.list_mounted_volumes()
            
            # Effacer la liste actuelle
            self.mounted_volumes_list.clear()
            
            if not volumes:
                self.log_message("Aucun volume monté")
                return
                
            # Ajouter les volumes à la liste
            for slot, mount_point in volumes:
                item = QListWidgetItem(f"{mount_point}")
                item.setData(Qt.ItemDataRole.UserRole, (slot, mount_point))
                self.mounted_volumes_list.addItem(item)
                
            self.log_message(f"Volumes chargés: {volumes}")
            
        except Exception as e:
            self.log_message(f"Erreur lors du rafraîchissement: {str(e)}")
            
    def _on_unmount_volume(self):
        """Appelé quand on clique sur le bouton de démontage."""
        # Récupérer le volume sélectionné
        current = self.mounted_volumes_list.currentItem()
        if not current:
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez sélectionner un volume à démonter"
            )
            return
            
        # Récupérer le point de montage
        _, mount_point = current.data(Qt.ItemDataRole.UserRole)
        
        # Démonter le volume
        success, error = veracrypt.unmount_volume(mount_point)
        
        if success:
            QMessageBox.information(
                self,
                "Succès",
                f"Le volume {mount_point} a été démonté avec succès"
            )
            # Rafraîchir la liste après le démontage
            self._refresh_mounted_volumes()
        else:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors du démontage: {error}"
            )

    def _on_volume_unmounted(self, mount_point: str):
        """Appelé quand un volume est démonté depuis la liste."""
        self.log_message(f"Signal de démontage reçu pour: {mount_point}")
        self._refresh_mounted_volumes()

    def _test_veracrypt_list(self):
        """Teste la commande veracrypt --list."""
        self.show_loading("Test de veracrypt --list...")
        try:
            success, stdout, stderr = veracrypt.run_veracrypt_command([
                system.Constants.VERACRYPT_PATH,
                '--text',
                '--non-interactive',
                '--test'
            ])
            
            if success:
                self.log_message("Auto-tests de tous les algorithmes réussis")
            else:
                self.log_message(f"Erreur:\n{stderr}")
                
            self._refresh_mounted_volumes()
        except Exception as e:
            self.log_message(f"Erreur lors du test: {str(e)}")
        finally:
            self.hide_loading()

    def _cleanup_mount_points(self):
        """Nettoie les points de montage."""
        self.show_loading("Nettoyage des points de montage...")
        try:
            # Démonter tous les volumes
            volumes = veracrypt.list_mounted_volumes()
            for slot, mount_point in volumes:
                success, error = veracrypt.unmount_volume(mount_point)
                if not success:
                    self.log_message(f"Erreur lors du démontage de {mount_point}: {error}")
                    
            # Rafraîchir la liste
            self._refresh_mounted_volumes()
            
            QMessageBox.information(
                self,
                "Succès",
                "Nettoyage des points de montage terminé"
            )
        except Exception as e:
            self.log_message(f"Erreur lors du nettoyage: {str(e)}")
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors du nettoyage:\n{str(e)}"
            )
        finally:
            self.hide_loading()

    def _load_mounted_volumes(self):
        """Charge la liste des volumes montés."""
        self.show_loading("Recherche des volumes montés...")
        try:
            volumes = veracrypt.list_mounted_volumes()
            
            # Mettre à jour la liste
            for slot, mount_point in volumes:
                item = QListWidgetItem(f"{mount_point}")
                item.setData(Qt.ItemDataRole.UserRole, (slot, mount_point))
                self.mounted_volumes_list.addItem(item)
                
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

    def _show_message(self, title: str, message: str, icon: QMessageBox.Icon = QMessageBox.Icon.Information):
        """Affiche une boîte de dialogue centrée."""
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        self._center_dialog(msg_box)
        msg_box.exec()
