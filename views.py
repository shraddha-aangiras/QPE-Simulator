import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, 
    QFrame, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath

from style import UI_CONFIG
from calc import get_qpe_data

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
        col_box = QColor(UI_CONFIG["COLORS"][1]) 
        col_box.setAlpha(80)
        col_box_border = QColor(UI_CONFIG["COLORS"][1])
        col_star = QColor(UI_CONFIG["COLORS"][3]) 
        
        painter.setFont(QFont("Arial", 11))

        for i, n in enumerate(self.qubit_range):
            cy = i * row_h + 35
            
            painter.setPen(col_text)
            painter.drawText(10, cy + 5, f"{n} qubits")
            
            line_start = margin_left
            line_end = margin_left + line_w
            painter.setPen(QPen(col_line, 2))
            painter.drawLine(line_start, cy, line_end, cy)
            painter.drawLine(line_start, cy-5, line_start, cy+5)
            painter.drawLine(line_end, cy-5, line_end, cy+5)
            
            data = self.results[n]
            est = data['phase_est']
            
            # Circular difference
            diff = abs(est - self.phase_true)
            err = min(diff, 1.0 - diff)
            
            uncertainty = 1.0 / (2**n)
            est_px = int(margin_left + est * line_w)
            box_w_px = int(uncertainty * line_w)
            
            painter.setBrush(QBrush(col_box))
            painter.setPen(QPen(col_box_border, 1))
            box_x = est_px - box_w_px // 2
            
            if box_x < line_start: box_x = line_start
            if box_x + box_w_px > line_end: box_w_px = line_end - box_x
            
            painter.drawRect(box_x, cy - 8, box_w_px, 16)
            self.draw_star(painter, est_px, cy, size=8, color=col_star)
            
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
        
        self.lbl_err = QLabel("Err: 0.0000")
        self.lbl_err.setFont(font_res)
        self.lbl_err.setStyleSheet(f"color: {UI_CONFIG['COLORS'][3]};") 

        bar_layout.addWidget(self.lbl_est)
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
        
        est = data['phase_est']
        
        # Circular difference
        diff = abs(est - true_phase)
        err = min(diff, 1.0 - diff)
        
        self.lbl_est.setText(f"Est Phase: {est:.5f}")
        self.lbl_err.setText(f"Error: {err:.5f}")