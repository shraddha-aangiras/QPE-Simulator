import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, 
    QFrame, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath

from app.style import UI_CONFIG
from app.calc import get_qpe_data

class MultiQubitPainter(QWidget):
    """Bottom Tab: Custom painted visualization of 1-10 qubits."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(700)
        self.phase_true = 0.0
        self.shots = 100
        self.mean_photons = 1.0 
        self.use_poisson = True
        self.qubit_range = range(1, 11)
        self.results = {}
        self.update_simulation()

    def set_parameters(self, phase, shots, photons, use_poisson):
        self.phase_true = phase
        self.shots = shots
        self.mean_photons = photons
        self.use_poisson = use_poisson
        self.update_simulation()
        self.update()

    def update_simulation(self):
        for n in self.qubit_range:
            self.results[n] = get_qpe_data(n, self.phase_true, self.shots, self.mean_photons, self.use_poisson)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        row_h = 60
        margin_left = 90 
        margin_right = 200
        line_w = w - margin_left - margin_right
        
        col_text = Qt.white
        col_line = QColor("#888")
        
        col_hardware = QColor("#777") 
        col_hardware.setAlpha(40)
        
        col_confidence = QColor(UI_CONFIG["COLORS"][1]) 
        col_confidence.setAlpha(150)
        col_conf_border = QColor(UI_CONFIG["COLORS"][1])
        
        col_true = QColor("#3498db")
        col_est = QColor(UI_CONFIG["COLORS"][3])
        
        painter.setFont(QFont("Arial", 11))

        for i, n in enumerate(self.qubit_range):
            cy = i * row_h + 35
            
            data = self.results.get(n, {})
            est = data.get('phase_est', 0.0)
            shots_disp = data.get('shots_count', 0)
            std_err = data.get('std_error', 1.0)
            
            painter.setPen(col_text)
            painter.setFont(QFont("Arial", 11, QFont.Bold))
            painter.drawText(10, cy - 2, f"{n} qubits")
            
            painter.setFont(QFont("Arial", 9))
            painter.setPen(QColor("#bbb"))
            painter.drawText(10, cy + 14, f"({shots_disp} shots)")
            painter.setFont(QFont("Arial", 11))

            line_start = margin_left
            line_end = margin_left + line_w
            painter.setPen(QPen(col_line, 2))
            painter.drawLine(line_start, cy, line_end, cy)
            painter.drawLine(line_start, cy-5, line_start, cy+5)
            painter.drawLine(line_end, cy-5, line_end, cy+5)
            
            est_px = int(margin_left + est * line_w)
            true_px = int(margin_left + self.phase_true * line_w)
            
            diff = abs(est - self.phase_true)
            err = min(diff, 1.0 - diff)
            
            limit_width = 1.0 / (2**n)
            limit_px = int(limit_width * line_w)
            
            conf_px = int((std_err * 4.0) * line_w)
            conf_px = max(conf_px, 2)
            
            painter.setBrush(QBrush(col_hardware))
            painter.setPen(Qt.NoPen)
            
            l_box_x = est_px - limit_px // 2
            if l_box_x < line_start: l_box_x = line_start
            draw_lw = limit_px
            if l_box_x + draw_lw > line_end: draw_lw = line_end - l_box_x
            
            painter.drawRect(l_box_x, cy - 12, draw_lw, 24)
            
            painter.setBrush(QBrush(col_confidence))
            painter.setPen(QPen(col_conf_border, 1))
            
            c_box_x = est_px - conf_px // 2
            if c_box_x < line_start: c_box_x = line_start
            draw_cw = conf_px
            if c_box_x + draw_cw > line_end: draw_cw = line_end - c_box_x
            
            painter.drawRect(c_box_x, cy - 6, draw_cw, 12)

            painter.setPen(QPen(col_true, 3))
            painter.drawLine(true_px, cy - 15, true_px, cy + 15)
            
            square_size = 14
            painter.setBrush(QBrush(col_est))
            painter.setPen(QPen(Qt.black, 1)) 
            painter.drawRect(est_px - square_size // 2, cy - square_size // 2, square_size, square_size)
            
            painter.setPen(col_text)
            painter.setFont(QFont("Courier New", 10)) 
            painter.drawText(line_end + 15, cy + 5, f"Err: {err:.4f}")
            painter.setFont(QFont("Arial", 11))

    def draw_star(self, painter, x, y, size, color):
        path = QPainterPath()
        import math
        path.moveTo(x, y - size)
        for i in range(5):
            theta = math.radians(144 * i)
            path.lineTo(x + size * math.sin(theta), y - size * math.cos(theta))
        path.closeSubpath()
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)

    


class CountsViewTab(QWidget):
    """Top Tab: Table and Bar Graph."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["State |x>", "Phase", "Counts"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setStyleSheet("QTableWidget { border: none; }")
        splitter.addWidget(self.table)
        
        # Graph
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground(UI_CONFIG["PLOT_BACKGROUND"])
        self.graph_widget.getAxis('left').setPen('#888')
        self.graph_widget.getAxis('bottom').setPen('#888')
        self.bar_item = pg.BarGraphItem(x=[0], height=[0], width=0.6, brush=UI_CONFIG["COLORS"][1], pen=None)
        self.graph_widget.addItem(self.bar_item)
        splitter.addWidget(self.graph_widget)
        
        splitter.setSizes([350, 600])
        layout.addWidget(splitter, 1)

        # Bottom Analysis Frame
        self.analysis_frame = QFrame()
        self.analysis_frame.setFrameShape(QFrame.StyledPanel)
        bar_layout = QHBoxLayout(self.analysis_frame)
        
        font_res = QFont("Arial", 12, QFont.Bold)
        
        self.lbl_est = QLabel("Est: 0.0000")
        self.lbl_est.setFont(font_res)
        self.lbl_est.setStyleSheet(f"color: {UI_CONFIG['COLORS'][1]};")
        
        self.lbl_spread = QLabel("Spread: 0.00")
        self.lbl_spread.setFont(font_res)
        self.lbl_spread.setStyleSheet(f"color: {UI_CONFIG['COLORS'][2]};")

        self.lbl_err = QLabel("Err: 0.0000")
        self.lbl_err.setFont(font_res)
        self.lbl_err.setStyleSheet(f"color: {UI_CONFIG['COLORS'][3]};") 

        bar_layout.addWidget(self.lbl_est)
        bar_layout.addStretch()
        bar_layout.addWidget(self.lbl_spread)
        bar_layout.addStretch()
        bar_layout.addWidget(self.lbl_err)
        
        layout.addWidget(self.analysis_frame)

    def update_data(self, data, true_phase, n_qubits):
        N = data['N']
        counts = data['counts']
        
        # Only show rows with non-zero counts
        nonzero_indices = np.where(counts > 0)[0]

        self.table.setRowCount(len(nonzero_indices))
        max_c = np.max(counts) if len(counts) > 0 else 0
        
        for row_idx, state_idx in enumerate(nonzero_indices):
            count_val = counts[state_idx]
            phase_val = state_idx / N
            
            item_state = QTableWidgetItem(f"|{state_idx:0{n_qubits}b}>")
            item_phase = QTableWidgetItem(f"{phase_val:.4f}")
            item_count = QTableWidgetItem(str(count_val))
            
            item_state.setTextAlignment(Qt.AlignCenter)
            item_phase.setTextAlignment(Qt.AlignCenter)
            item_count.setTextAlignment(Qt.AlignCenter)
            
            # Highlight max count
            if count_val == max_c:
                c = QColor(UI_CONFIG["COLORS"][1])
                item_state.setForeground(c)
                item_count.setForeground(c)
                item_phase.setForeground(c)
                f = item_count.font()
                f.setBold(True)
                item_count.setFont(f)
            else:
                c = QColor(220, 220, 220)
                item_state.setForeground(c)
                item_count.setForeground(c)
                item_phase.setForeground(c)

            self.table.setItem(row_idx, 0, item_state)
            self.table.setItem(row_idx, 1, item_phase)
            self.table.setItem(row_idx, 2, item_count)
            
        self.bar_item.setOpts(x=data['x'], height=counts, width=0.6)
        
        # -- I'm trying to see how to change ticks without screwing over scaling
        if len(nonzero_indices) > 0:
            # First and last non zero states
            first_state = np.min(nonzero_indices)
            last_state  = np.max(nonzero_indices)
            buffer = 3
            
            min_x = max(0, first_state - buffer)
            max_x = min(N - 1, last_state + buffer)
        
            self.graph_widget.setXRange(min_x, max_x, padding=0)
            
            ax = self.graph_widget.getAxis('bottom')
            ticks = []
            
            for x in range(int(min_x), int(max_x) + 1):
                if 0 <= x < len(counts):
                    if counts[x] > 0:
                        # Phase calc
                        phase_val = x / (2**n_qubits)
                        label = f"{phase_val:.4f}"
                        ticks.append((x, label))
            
            ax.setTicks([ticks])
            
        else:
            self.graph_widget.setXRange(0, N)
        # -----------
        est = data['phase_est']
        
        # Circular difference
        diff = abs(est - true_phase)
        err = min(diff, 1.0 - diff)
        
        self.lbl_est.setText(f"Est Phase: {est:.5f}")
        self.lbl_err.setText(f"Error: {err:.5f}")

        prec_val = data.get('std_error', 0.0)
        self.lbl_spread.setText(f"Standard Error: ±{prec_val:.5f}") 
        self.lbl_spread.setToolTip("Standard Error of the Mean (Shrinks with more shots)")
    
    def set_y_range(self, max_val):
        """Fixes the Y-axis range to prevent jumping during animation."""
        self.graph_widget.setYRange(0, max_val, padding=0.1)
        self.graph_widget.enableAutoRange(axis='y', enable=False)

