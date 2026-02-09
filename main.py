import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget, QScrollArea
from PyQt5 import QtCore

# Import from our new modules
from style import get_dark_palette
from calc import get_qpe_data
from controls import QPEControlPanel
from views import CountsViewTab, MultiQubitPainter

class QPE_LabInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quantum Phase Estimation")
        self.resize(1280, 800)
        
        self.use_poisson_noise = False 
        
        self.setPalette(get_dark_palette())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        
        # Left Panel (Controls)
        self.controls = QPEControlPanel()
        main_layout.addWidget(self.controls)
        
        # Right Tabs (Views)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; top: -1px; }
            QTabBar::tab { background: #353535; color: #aaa; padding: 8px 20px; border: 1px solid #444; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; margin-right: 2px; }
            QTabBar::tab:selected { background: #2b2b2b; color: white; border-top: 2px solid #3498db; }
        """)
        
        self.tab_counts = CountsViewTab()
        self.tabs.addTab(self.tab_counts, "Counts View")
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: #2b2b2b;")
        self.tab_scaling = MultiQubitPainter()
        self.scroll_area.setWidget(self.tab_scaling)
        self.tabs.addTab(self.scroll_area, "1-10 Qubit Scaling")
        
        main_layout.addWidget(self.tabs)
        
        # Connections
        self.controls.phase_input.valueChanged.connect(self.update_all)
        self.controls.num_shots.valueChanged.connect(self.update_all)
        self.controls.num_qubits.valueChanged.connect(self.update_all)
        self.controls.num_photons.valueChanged.connect(self.update_all)
        self.controls.refresh_btn.clicked.connect(self.update_all)
        
        # Trigger initial update
        self.update_all()

    def update_all(self):
        phase = self.controls.phase_input.value()
        raw_shots = self.controls.num_shots.value()
        photons = self.controls.num_photons.value()
        n = self.controls.num_qubits.value()
        
        # Update tab 1
        data = get_qpe_data(n, phase, raw_shots, photons, self.use_poisson_noise)
        self.tab_counts.update_data(data, phase, n)
        
        # Update tab 2
        self.tab_scaling.set_parameters(phase, raw_shots, photons, self.use_poisson_noise)


if __name__ == "__main__":
    if hasattr(QtCore.Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
    if hasattr(QtCore.Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = QPE_LabInterface()
    window.show()
    
    sys.exit(app.exec_())