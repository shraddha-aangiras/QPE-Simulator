import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTabWidget, QScrollArea, QLabel
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer
import numpy as np

from app.style import get_dark_palette
from app.calc import get_ideal_probs, get_circular_stats
from app.controls import QPEControlPanel
from app.views import CountsViewTab, MultiQubitPainter
from app.views import CountsViewTab, MultiQubitPainter, SinglePhotonTab

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

        # Connecting tab
        self.tab_connector = SinglePhotonTab()
        self.tabs.addTab(self.tab_connector, "Single shot interferometer")

        # Counts View Tab
        self.tab_counts = CountsViewTab()
        self.tabs.addTab(self.tab_counts, "Counts View")
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none; background-color: #2b2b2b;")
        self.tab_scaling = MultiQubitPainter()
        self.scroll_area.setWidget(self.tab_scaling)
        self.tabs.addTab(self.scroll_area, "1-10 Qubit Scaling")
        
        main_layout.addWidget(self.tabs)
        self.tabs.currentChanged.connect(self.disconnect_refresh_tab)
        
        self.controls.phase_input.valueChanged.connect(self.trigger_animation)
        self.controls.num_shots.valueChanged.connect(self.trigger_animation)
        self.controls.num_qubits.valueChanged.connect(self.trigger_animation)
        self.controls.num_photons.valueChanged.connect(self.trigger_animation)
        self.controls.refresh_btn.clicked.connect(self.trigger_animation)
        
        # Animation State
        self.timer = QTimer()
        self.timer.timeout.connect(self.animation_step)
        shots = self.controls.num_shots.value()
        self.anim_duration = 5 if shots > 20 else (shots / 4) # seconds
        self.frame_rate = 30      # FPS
        self.timer_interval = int(1000 / self.frame_rate)
        
        # Start initial
        self.trigger_animation()
        self.disconnect_refresh_tab(self.tabs.currentIndex())

    def trigger_animation(self):
        """Prepares state and starts the timer."""
        self.timer.stop()
        
        self.tgt_phase = self.controls.phase_input.value()
        self.tgt_shots = self.controls.num_shots.value()
        self.tgt_photons = self.controls.num_photons.value()
        self.tgt_n = self.controls.num_qubits.value()
        
        self.anim_duration = 5 if self.tgt_shots > 20 else max((self.tgt_shots / 4.0), 0.1)
        resource_budget = self.tgt_n * self.tgt_shots
        self.tab_scaling.phase_true = self.tgt_phase
        
        for n in range(1, 11):
            # Calculate shots based on budget
            target_shots_n = int(resource_budget / n)
            target_shots_n = max(1, target_shots_n)
            
            # Generate full result immediately
            probs_n = get_ideal_probs(n, self.tgt_phase)
            total_events_n = int(target_shots_n * self.tgt_photons)
            
            counts_n = np.random.multinomial(total_events_n, probs_n)
            
            s_mean, s_std = get_circular_stats(counts_n, n)
            s_total = np.sum(counts_n)
            s_err = s_std / np.sqrt(s_total) if s_total > 0 else 1.0
            
            # Store result
            self.tab_scaling.results[n] = {
                "phase_est": s_mean,
                "std_error": s_err,
                "shots_count": target_shots_n
            }
        
        self.tab_scaling.update()

        # --- TAB 1: ANIMATION SETUP ---
        self.total_expected_events = int(self.tgt_shots * self.tgt_photons)
        self.main_probs = get_ideal_probs(self.tgt_n, self.tgt_phase)
        self.main_counts_accum = np.zeros(len(self.main_probs), dtype=int)

        # Fix Y-axis to prevent jumping
        # max_prob = np.max(self.main_probs)
        # expected_peak = max_prob * self.total_expected_events
        # y_limit = expected_peak + 4 * np.sqrt(expected_peak)

        y_limit = self.total_expected_events
        y_limit = max(y_limit, 10)
        self.tab_counts.set_y_range(y_limit)
        
        self.current_events = 0
        self.start_time = QtCore.QTime.currentTime()
        
        self.timer.start(self.timer_interval)

    def animation_step(self):
        elapsed = self.start_time.msecsTo(QtCore.QTime.currentTime()) / 1000.0
        
        if elapsed >= self.anim_duration:
            target_now = self.total_expected_events
            is_finished = True
        else:
            progress = elapsed / self.anim_duration
            target_now = int(progress * self.total_expected_events)
            is_finished = False

        batch_size = target_now - self.current_events
        
        if batch_size > 0:
            self.current_events += batch_size
            
            # Update Tab 1 Data
            new_counts = np.random.multinomial(batch_size, self.main_probs)
            self.main_counts_accum += new_counts
            
            mean_est, std_dev = get_circular_stats(self.main_counts_accum, self.tgt_n)
            total_seen = np.sum(self.main_counts_accum)
            std_error = std_dev / np.sqrt(total_seen) if total_seen > 0 else 1.0

            data_packet = {
                "x": np.arange(len(self.main_probs)),
                "counts": self.main_counts_accum,
                "phase_est": mean_est,
                "std_dev_fraction": std_dev,
                "std_error": std_error,
                "counts": self.main_counts_accum,
                "N": len(self.main_probs)
            }
            self.tab_counts.update_data(data_packet, self.tgt_phase, self.tgt_n)
            
        if is_finished:
            self.timer.stop()
    def disconnect_refresh_tab(self, index):
        if index == 0:
            self.controls.refresh_btn.setEnabled(False)
        else:
            self.controls.refresh_btn.setEnabled(True)

    # def update_all(self):
    #     phase = self.controls.phase_input.value()
    #     raw_shots = self.controls.num_shots.value()
    #     photons = self.controls.num_photons.value()
    #     n = self.controls.num_qubits.value()
        
    #     # Update tab 1
    #     data = get_qpe_data(n, phase, raw_shots, photons, self.use_poisson_noise)
    #     self.tab_counts.update_data(data, phase, n)
        
    #     # Update tab 2
    #     self.tab_scaling.set_parameters(phase, raw_shots, photons, self.use_poisson_noise)


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