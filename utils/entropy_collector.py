"""
Collecteur d'entropie pour la génération de nombres aléatoires.
"""

import time
import random
from typing import List, Tuple
from PyQt6.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QPen, QPaintEvent
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QTextEdit

class EntropyCollector(QWidget):
    """Widget pour collecter l'entropie via les mouvements de la souris."""
    
    # Signal émis quand assez d'entropie a été collectée
    entropy_collected = pyqtSignal(str)
    
    def __init__(self, min_points: int = 640, parent=None):
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
        
        # Label d'instructions principal
        self.label = QLabel(
            "Pour générer une clé de chiffrement sécurisée, déplacez votre souris de manière aléatoire dans la zone ci-dessous"
        )
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)  # Permettre le retour à la ligne
        layout.addWidget(self.label)
        
        # Widget pour la zone de dessin
        self.draw_widget = DrawingArea(self)
        self.draw_widget.setFixedSize(360, 200)  # Zone plus haute pour le texte
        layout.addWidget(self.draw_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Zone de texte pour afficher les données collectées
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setFixedHeight(100)
        self.text_area.setPlaceholderText("Les données collectées apparaîtront ici...")
        layout.addWidget(self.text_area)
        
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
        self.text_area.clear()
        self.draw_widget.update()
        
    def mouseMoveEvent(self, event):
        """Gère les mouvements de la souris."""
        if not self.collecting:
            return
            
        # Convertir les coordonnées en relatif à la zone de dessin
        point = self.draw_widget.mapFrom(self, event.pos())
        
        # Vérifier si le point est dans la zone de dessin
        if not self.draw_widget.rect().contains(point):
            return
            
        # Ajouter les coordonnées et le timestamp
        self.points.append((point.x(), point.y(), time.time_ns() & 0xFFFFFFFF))
        
        # Mettre à jour la progression
        self.progress.setValue(len(self.points))
        
        # Mettre à jour le texte
        self.text_area.setText(f"Points collectés : {len(self.points)}/{self.min_points}\n"
                             f"Dernière position : ({point.x()}, {point.y()})")
        
        # Mettre à jour l'affichage
        self.draw_widget.update()
        
        # Vérifier si on a assez de points
        if len(self.points) >= self.min_points:
            self.finish_collecting()
            
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

class DrawingArea(QWidget):
    """Widget pour la zone de dessin."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
    def paintEvent(self, event: QPaintEvent):
        """Dessine la zone de collecte."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Fond blanc
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # Bordure épaisse
        painter.setPen(QPen(QColor(100, 100, 100), 3))
        painter.drawRect(self.rect().adjusted(1, 1, -1, -1))
        
        # Texte d'instruction dans la zone
        if not getattr(self.parent, 'points', []):
            painter.setPen(QColor(120, 120, 120))
            font = painter.font()
            font.setPointSize(10)
            painter.setFont(font)
            
            text = "Déplacez votre souris ici\nde manière aléatoire"
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
        
        # Dessiner les points collectés
        if hasattr(self.parent, 'points') and self.parent.points:
            painter.setPen(QPen(QColor(0, 120, 215), 2))
            for x, y, _ in self.parent.points[-50:]:
                painter.drawPoint(x, y)
