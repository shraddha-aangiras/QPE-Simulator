import numpy as np
from PyQt5.QtWidgets import QFrame, QVBoxLayout, QLabel, QSpinBox, QPushButton, QHBoxLayout, QDoubleSpinBox, QDial
from PyQt5.QtCore import Qt
from app.components import SliderWithEdit
from app.style import UI_CONFIG, USE_RADIANS

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
        if USE_RADIANS:
            layout.addWidget(QLabel("Target Phase (φ): [0, 2π]"))
            # Max is 2*pi (~6.28)
            #self.phase_input = SliderWithEdit(self, min=0.0, max=2*np.pi, step=0.001)
            self.phase_input = SliderWithEdit(self, min=0.0, max=2.0, step=0.001)
            self.phase_input.setValue(0.5) # Default to pi
        else:
            layout.addWidget(QLabel("Target Phase (φ): [0, 1]"))
            self.phase_input = SliderWithEdit(self, min=0.0, max=1.0, step=0.001)
            self.phase_input.setValue(0.3)

        layout.addWidget(self.phase_input)
        
        # Shots
        layout.addWidget(QLabel("Shots:"))
        self.num_shots = QSpinBox()
        self.num_shots.setRange(1, 100000000)
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
                color: {UI_CONFIG['BTN_TEXT']}; 
                font-weight: bold; 
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {UI_CONFIG['BTN_HOVER']};
            }}
            QPushButton:pressed {{
                background-color: {UI_CONFIG['BTN_PRESSED']};
            }}
            QPushButton:disabled {{
                background-color: {UI_CONFIG['BTN_DISABLED_BG']};
                color: {UI_CONFIG['BTN_DISABLED_TEXT']};
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

class InterferometerControlPanel(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFixedWidth(320)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        title = QLabel("Interferometer Controls")
        title.setStyleSheet(f"font-size: 11pt; font-weight: bold; color: white; border-bottom: 2px solid {UI_CONFIG['COLORS'][1]}; padding-bottom: 5px;")
        layout.addWidget(title)
        layout.addSpacing(10)
        
        spin_hbox = QHBoxLayout()
        self.phase_spin = QDoubleSpinBox()
        self.phase_spin.setRange(0.0, 2.0)
        self.phase_spin.setSingleStep(0.05)
        self.phase_spin.setDecimals(3)
        self.phase_spin.setSuffix(" π")
        self.phase_spin.setStyleSheet("font-size: 14px; padding: 3px; background: #353535; color: white;")
        self.phase_spin.setFixedWidth(110)
        
        spin_lbl = QLabel("Angle (\u03B8):")
        spin_lbl.setStyleSheet("font-size: 14px; color: #ccc;")
        spin_hbox.addWidget(spin_lbl)
        spin_hbox.addWidget(self.phase_spin)
        spin_hbox.setAlignment(Qt.AlignCenter)
        layout.addLayout(spin_hbox)

        self.dial = QDial()
        self.dial.setRange(0, 2000) 
        self.dial.setNotchesVisible(True)
        self.dial.setFixedSize(100, 100)
        self.dial.setStyleSheet("background-color: #2b2b2b;")
        layout.addWidget(self.dial, alignment=Qt.AlignCenter)

        layout.addSpacing(20)

        # The Auto-Fire Toggle Button
        self.play_btn = QPushButton("Start Auto-Fire")
        self.play_btn.setCheckable(True)
        self.play_btn.setMinimumHeight(40)
        self.play_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {UI_CONFIG['COLORS'][4]}; 
                color: {UI_CONFIG['BTN_TEXT']}; 
                font-weight: bold; border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: {UI_CONFIG['BTN_HOVER']}; }}
            QPushButton:checked {{ background-color: #e74c3c; }}
        """)
        layout.addWidget(self.play_btn)

        # The Reset Button
        self.reset_btn = QPushButton("Reset Counts")
        self.reset_btn.setMinimumHeight(40)
        self.reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #555; color: white; 
                font-weight: bold; border-radius: 5px;
            }}
            QPushButton:hover {{ background-color: #666; }}
            QPushButton:pressed {{ background-color: #444; }}
        """)
        layout.addWidget(self.reset_btn)
        
        layout.addStretch()
        
        self.dial.valueChanged.connect(self.sync_dial_to_spin)
        self.phase_spin.valueChanged.connect(self.sync_spin_to_dial)
        self.play_btn.toggled.connect(self.on_play_toggled)

    def on_play_toggled(self, checked):
        if checked:
            self.play_btn.setText("Stop Auto-Fire")
        else:
            self.play_btn.setText("Start Auto-Fire")

    def sync_dial_to_spin(self, val):
        self.phase_spin.blockSignals(True)
        self.phase_spin.setValue(val / 1000.0)
        self.phase_spin.blockSignals(False)
        self.phase_spin.valueChanged.emit(val / 1000.0)

    def sync_spin_to_dial(self, val):
        self.dial.blockSignals(True)
        self.dial.setValue(int(val * 1000))
        self.dial.blockSignals(False)