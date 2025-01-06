"""
Fonctions utilitaires pour l'interface graphique.
"""

from PyQt6.QtWidgets import QDialog, QWidget
from PyQt6.QtCore import Qt

def center_window(window: QWidget, parent: QWidget = None):
    """Centre une fenêtre par rapport à son parent ou à l'écran."""
    if parent:
        # Centre par rapport au parent
        geometry = parent.geometry()
        center = geometry.center()
        window_geometry = window.geometry()
        window_geometry.moveCenter(center)
        window.setGeometry(window_geometry)
    else:
        # Centre par rapport à l'écran
        screen = window.screen().geometry()
        window_geometry = window.geometry()
        window_geometry.moveCenter(screen.center())
        window.setGeometry(window_geometry)

def setup_dialog(dialog: QDialog, parent: QWidget = None, title: str = None, width: int = None):
    """Configure un dialogue avec les paramètres communs."""
    if parent:
        dialog.setParent(parent)
    if title:
        dialog.setWindowTitle(title)
    if width:
        dialog.setMinimumWidth(width)
    dialog.setModal(True)
    center_window(dialog, parent)
