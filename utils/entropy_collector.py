"""
Collecteur d'entropie pour la génération de nombres aléatoires.
"""

import time
import random
from typing import List, Tuple
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar

class EntropyCollector(QWidget):
    """Widget pour collecter l'entropie via les mouvements de la souris."""
    
    # Signal émis quand assez d'entropie a été collectée
    entropy_collected = pyqtSignal(str)
    
    def __init__(self, min_points: int = 320, parent=None):
        """Initialise le collecteur d'entropie.
        
        Args:
            min_points: Nombre minimum de points à collecter
            parent: Widget parent
        """
        super().__init__(parent)
        self.min_points = min_points
        self.points: List[Tuple[int, int, int]] = []  # x, y, timestamp
        self.collecting = False
        
        # Configuration de l'interface
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)  # Marges uniformes
        layout.setSpacing(10)  # Espacement entre les widgets
        
        # Label d'instructions
        self.label = QLabel(
            "Déplacez votre souris dans le carré ci-dessous pour générer de l'aléatoire"
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        
        # Widget pour la zone de dessin
        self.draw_widget = QWidget()
        self.draw_widget.setFixedSize(360, 100)  # Taille fixe pour la zone de dessin
        self.draw_rect = QRect(0, 0, 360, 100)
        layout.addWidget(self.draw_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Barre de progression
        self.progress = QProgressBar()
        self.progress.setMinimum(0)
        self.progress.setMaximum(min_points)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        
        self.setLayout(layout)
        self.setFixedWidth(400)  # Largeur fixe
        
        # Activer le suivi de la souris
        self.setMouseTracking(True)
        self.draw_widget.setMouseTracking(True)
        
    def start_collecting(self):
        """Démarre la collecte d'entropie."""
        self.points.clear()
        self.collecting = True
        self.progress.setValue(0)
        self.update()
        
    def mouseMoveEvent(self, event):
        """Gère les mouvements de la souris."""
        if not self.collecting:
            return
            
        # Convertir les coordonnées en relatif à la zone de dessin
        point = self.draw_widget.mapFrom(self, event.pos())
        
        # Vérifier si le point est dans la zone de dessin
        if not self.draw_rect.contains(point):
            return
            
        # Ajouter les coordonnées et le timestamp
        self.points.append((point.x(), point.y(), time.time_ns() & 0xFFFFFFFF))
        
        # Mettre à jour la progression
        self.progress.setValue(len(self.points))
        
        # Vérifier si on a assez de points
        if len(self.points) >= self.min_points:
            self.finish_collecting()
            
    def paintEvent(self, event):
        """Dessine la zone de collecte."""
        painter = QPainter(self.draw_widget)
        
        # Fond gris clair
        painter.fillRect(self.draw_rect, QColor(240, 240, 240))
        
        # Bordure
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(self.draw_rect)
        
    def finish_collecting(self):
        """Termine la collecte et génère la chaîne aléatoire."""
        self.collecting = False
        
        # Mélanger les points
        random.shuffle(self.points)
        
        # Générer la chaîne aléatoire
        entropy = []
        for x, y, t in self.points:
            # Combiner les valeurs pour générer un caractère
            value = (x * y * t) & 0xFF
            entropy.append(chr(32 + (value % 94)))  # Caractères ASCII imprimables
            
        # Émettre le signal avec la chaîne générée
        self.entropy_collected.emit(''.join(entropy))
