"""
Gestion des thèmes de l'application.
"""

from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtCore import Qt

THEMES = {
    'Clair': {
        'window': '#f0f0f0',
        'window_text': '#000000',
        'base': '#ffffff',
        'alternate_base': '#f7f7f7',
        'text': '#000000',
        'button': '#e0e0e0',
        'button_text': '#000000',
        'bright_text': '#ffffff',
        'light': '#ffffff',
        'midlight': '#e3e3e3',
        'dark': '#bdbdbd',
        'mid': '#a0a0a0',
        'shadow': '#696969',
        'highlight': '#308cc6',
        'highlighted_text': '#ffffff',
        'link': '#0000ff',
        'link_visited': '#800080'
    },
    'Sombre': {
        'window': '#2b2b2b',
        'window_text': '#ffffff',
        'base': '#1e1e1e',
        'alternate_base': '#232323',
        'text': '#ffffff',
        'button': '#353535',
        'button_text': '#ffffff',
        'bright_text': '#ffffff',
        'light': '#404040',
        'midlight': '#353535',
        'dark': '#1c1c1c',
        'mid': '#2b2b2b',
        'shadow': '#141414',
        'highlight': '#2d79b5',
        'highlighted_text': '#ffffff',
        'link': '#3391ff',
        'link_visited': '#ba8fff'
    },
    'Système': None  # Utilise le thème du système
}

def apply_theme(app, theme_name: str):
    """Applique un thème à l'application.
    
    Args:
        app: L'instance QApplication
        theme_name: Le nom du thème à appliquer
    """
    if theme_name not in THEMES:
        return
        
    # Si c'est le thème système, réinitialiser la palette
    if theme_name == 'Système':
        app.setPalette(QPalette())
        return
        
    # Créer une nouvelle palette
    palette = QPalette()
    colors = THEMES[theme_name]
    
    # Configurer les couleurs de la palette
    color_roles = {
        QPalette.ColorRole.Window: 'window',
        QPalette.ColorRole.WindowText: 'window_text',
        QPalette.ColorRole.Base: 'base',
        QPalette.ColorRole.AlternateBase: 'alternate_base',
        QPalette.ColorRole.Text: 'text',
        QPalette.ColorRole.Button: 'button',
        QPalette.ColorRole.ButtonText: 'button_text',
        QPalette.ColorRole.BrightText: 'bright_text',
        QPalette.ColorRole.Light: 'light',
        QPalette.ColorRole.Midlight: 'midlight',
        QPalette.ColorRole.Dark: 'dark',
        QPalette.ColorRole.Mid: 'mid',
        QPalette.ColorRole.Shadow: 'shadow',
        QPalette.ColorRole.Highlight: 'highlight',
        QPalette.ColorRole.HighlightedText: 'highlighted_text',
        QPalette.ColorRole.Link: 'link',
        QPalette.ColorRole.LinkVisited: 'link_visited'
    }
    
    for role, key in color_roles.items():
        palette.setColor(role, QColor(colors[key]))
        
    # Appliquer la palette
    app.setPalette(palette)
