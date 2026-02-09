import numpy as np
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QSpinBox, QPushButton
from app.components import SliderWithEdit
from app.style import UI_CONFIG

class QPEControlPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedWidth(320)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        title = QLabel("Experiment Controls")
        title.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: white; border-bottom: 2px solid {UI_CONFIG['COLORS'][1]}; padding-bottom: 5px;")
        layout.addWidget(title)
        layout.addSpacing(5)
        
        # Phase Control
        layout.addWidget(QLabel("Target Phase (φ): [0, 1]"))
        self.phase_input = SliderWithEdit(self, min=0.0, max=1.0, step=0.001)
        self.phase_input.setValue(0.125)
        layout.addWidget(self.phase_input)
        
        # Shots
        layout.addWidget(QLabel("Shots:"))
        self.num_shots = QSpinBox()
        self.num_shots.setRange(1, 100000)
        self.num_shots.setValue(100)
        self.num_shots.setSingleStep(100)
        layout.addWidget(self.num_shots)
        
        # Photons
        layout.addWidget(QLabel("Photons per Shot:"))
        self.num_photons = QSpinBox() 
        self.num_photons.setRange(1, 1000)
        self.num_photons.setValue(1)
        self.num_photons.setSingleStep(1)
        layout.addWidget(self.num_photons)

        # Refresh Button
        self.refresh_btn = QPushButton("Refresh Simulation")
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UI_CONFIG['COLORS'][4]}; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: #3e5f41;
            }}
            QPushButton:pressed {{
                background-color: #2c442e;
            }}
        """)
        layout.addWidget(self.refresh_btn)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Active Qubits
        layout.addWidget(QLabel("Active Qubits (Detail View):"))
        self.num_qubits = QSpinBox()
        self.num_qubits.setRange(1, 10)
        self.num_qubits.setValue(3)
        self.num_qubits.setPrefix("n = ")
        layout.addWidget(self.num_qubits)

        layout.addStretch()