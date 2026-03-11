from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

USE_RADIANS = True

UI_CONFIG = dict(
    COLORS=["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71"],
    PLOT_BACKGROUND="#2b2b2b", 
    NUMERIC_FONT_SIZE=12,
    BTN_TEXT="white",
    BTN_HOVER="#3e5f41",
    BTN_PRESSED="#2c442e",
    BTN_DISABLED_BG="#555555",
    BTN_DISABLED_TEXT="#888888"
)

def get_dark_palette():
    palette = QPalette()
    
    # --- ACTIVE STATES ---
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.black)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)

    disabled_color = QColor(127, 127, 127)
    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled_color)
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled_color)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled_color)
    #palette.setColor(QPalette.Disabled, QPalette.Button, QColor(40, 40, 40)) 
    
    return palette