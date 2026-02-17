import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, 
    QFrame, QLabel
)
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPainterPath, QPolygonF

from app.style import UI_CONFIG

class MultiQubitPainter(QWidget):
    """Bottom Tab: Custom painted visualization of 1-10 qubits."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(850)
        self.phase_true = 0.0
        self.results = {}
        
        # Colors
        self.c_true_line = QColor("#3498db")    # Blue
        self.c_limit_border = QColor("#7f8c8d") # Grey
        self.c_est = QColor("#f1c40f")          # Gold
        self.c_conf = QColor(UI_CONFIG["COLORS"][0]) 
        self.c_conf.setAlpha(100) 
        self.c_text = Qt.white
        self.c_grid = QColor("#444")
        self.c_shots = QColor("#bdc3c7")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        
        # Layout
        margin_left = 120
        margin_right = 220
        top_offset = 80 
        row_h = 70
        line_w = w - margin_left - margin_right

        # --- 1. Draw Legend ---
        self.draw_legend(painter, w, top_offset)

        # --- 2. Headers ---
        header_y = top_offset + 10
        painter.setPen(QColor("#aaa"))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(10, header_y, "Resource Setup")
        painter.drawText(margin_left, header_y, "Experiment Result")
        painter.drawText(w - margin_right + 20, header_y, "Metrics")
        
        painter.setPen(QPen(self.c_grid, 1))
        painter.drawLine(0, header_y + 10, w, header_y + 10)

        # --- 3. Rows ---
        for i, n in enumerate(range(1, 11)):
            cy = top_offset + 30 + (i * row_h) + 35
            
            data = self.results.get(n, {})
            est = data.get('phase_est', 0.0)
            shots_disp = data.get('shots_count', 0)
            std_err = data.get('std_error', 1.0)
            
            # Row Bg
            if i % 2 == 0:
                painter.fillRect(0, cy - 35, w, row_h, QColor(255, 255, 255, 5))

            # Left Text
            painter.setPen(self.c_text)
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            painter.drawText(15, cy - 5, f"{n} Qubits")
            
            painter.setFont(QFont("Arial", 9))
            painter.setPen(self.c_shots)
            painter.drawText(15, cy + 12, f"Cost: {shots_disp} shots")

            # Center Visualization
            line_start = margin_left
            line_end = margin_left + line_w
            
            # Axis Line
            painter.setPen(QPen(QColor("#666"), 2))
            painter.drawLine(line_start, cy, line_end, cy)
            
            est_px = int(margin_left + est * line_w)
            true_px = int(margin_left + self.phase_true * line_w)
            
            # --- Hardware Limit (Containing Bin) ---
            N_bins = 2**n
            
            # Find the bin index containing the true phase (floor)
            bin_idx = int(np.floor(self.phase_true * N_bins))
            if bin_idx >= N_bins: bin_idx = N_bins - 1
            
            bin_start_val = bin_idx / N_bins
            bin_width_val = 1.0 / N_bins
            
            # Draw from left edge of bin
            box_start_px = int(margin_left + bin_start_val * line_w)
            box_width_px = max(int(bin_width_val * line_w), 4)
            
            painter.setPen(QPen(self.c_limit_border, 1, Qt.DashLine))
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(box_start_px, cy - 15, box_width_px, 30)

            # --- Uncertainty (Purple Bar) ---
            conf_width = std_err * 4.0
            conf_px = int(conf_width * line_w)
            c_box_x = est_px - conf_px // 2
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.c_conf))
            painter.drawRect(c_box_x, cy - 4, conf_px, 8)

            # --- True Phase Line ---
            painter.setPen(QPen(self.c_true_line, 2))
            painter.drawLine(true_px, cy - 20, true_px, cy + 20)

            # --- Estimate Star ---
            self.draw_star(painter, est_px, cy, 10, self.c_est)

            # --- Right: Metrics ---
            dist = abs(est - self.phase_true)
            dist = min(dist, 1.0 - dist) # Circular distance
            
            threshold = (1.0 / N_bins) / 2.0
            is_resolved = dist < (threshold + 1e-9)
            
            metrics_x = w - margin_right + 20
            
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            if is_resolved:
                painter.setPen(QColor("#2ecc71"))
                painter.drawText(metrics_x, cy - 10, "✔ Correct Bin")
            else:
                painter.setPen(QColor("#e67e22"))
                painter.drawText(metrics_x, cy - 10, "⚠ Incorrect Bin")
            
            painter.setFont(QFont("Arial", 9))
            
            painter.setPen(QColor("#f1c40f")) 
            painter.drawText(metrics_x, cy + 2, f"Est:    {est:.5f}")
            
            painter.setPen(QColor("#bbb"))
            painter.drawText(metrics_x, cy + 14, f"Err:    {dist:.5f}")
            
            painter.setPen(QColor("#7f8c8d"))
            painter.drawText(metrics_x, cy + 26, f"Bin Size: {bin_width_val:.5f}")

    def draw_legend(self, painter, w, h_offset):
        painter.setBrush(QColor(30, 30, 30))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, w, h_offset)
        
        y = 20
        spacing = 180
        x = 20
        font = QFont("Arial", 10)
        painter.setFont(font)
        
        # True Phase
        painter.setPen(QPen(self.c_true_line, 2))
        painter.drawLine(x, y+10, x, y-10)
        painter.setPen(Qt.white)
        painter.drawText(x + 10, y + 5, "True Phase")
        
        x += spacing
        # Hardware Limit
        painter.setPen(QPen(self.c_limit_border, 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(x, y - 10, 20, 20)
        painter.setPen(Qt.white)
        painter.drawText(x + 30, y + 5, "Hardware Resolution")
        
        x += spacing + 30
        # Estimate
        self.draw_star(painter, x, y, 8, self.c_est)
        painter.setPen(Qt.white)
        painter.drawText(x + 15, y + 5, "Estimate")
        
        x += spacing
        # Uncertainty
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(self.c_conf))
        painter.drawRect(x, y - 4, 20, 8)
        painter.setPen(Qt.white)
        painter.drawText(x + 30, y + 5, "Shot Noise")

    def draw_star(self, painter, cx, cy, radius, color):
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(Qt.black, 1))
        
        points = []
        import math
        for i in range(5):
            angle_deg = 270 + (i * 144)
            angle_rad = math.radians(angle_deg)
            px = cx + radius * math.cos(angle_rad)
            py = cy + radius * math.sin(angle_rad)
            points.append(QPointF(px, py))
            
        painter.drawPolygon(QPolygonF(points))

class CountsViewTab(QWidget):
    """Top Tab: Table and Bar Graph."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        
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
        
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground(UI_CONFIG["PLOT_BACKGROUND"])
        self.graph_widget.getAxis('left').setPen('#888')
        self.graph_widget.getAxis('bottom').setPen('#888')
        self.bar_item = pg.BarGraphItem(x=[0], height=[0], width=0.6, brush=UI_CONFIG["COLORS"][1], pen=None)
        self.graph_widget.addItem(self.bar_item)
        splitter.addWidget(self.graph_widget)
        
        splitter.setSizes([350, 600])
        layout.addWidget(splitter, 1)

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
        
        if len(nonzero_indices) > 0:
            first_state = np.min(nonzero_indices)
            last_state  = np.max(nonzero_indices)
            buffer = 3
            min_x = max(0, first_state - buffer)
            max_x = min(N - 1, last_state + buffer)
            self.graph_widget.setXRange(min_x, max_x, padding=0)
            
            ax = self.graph_widget.getAxis('bottom')
            ticks = []
            step = 1
            if (max_x - min_x) > 20: step = int((max_x - min_x) / 10)
            
            for x in range(int(min_x), int(max_x) + 1, step):
                if 0 <= x < len(counts):
                      phase_val = x / (2**n_qubits)
                      label = f"{phase_val:.3f}"
                      ticks.append((x, label))
            ax.setTicks([ticks])
        else:
            self.graph_widget.setXRange(0, N)

        est = data['phase_est']
        diff = abs(est - true_phase)
        err = min(diff, 1.0 - diff)
        
        self.lbl_est.setText(f"Est Phase: {est:.5f}")
        self.lbl_err.setText(f"Error: {err:.5f}")

        prec_val = data.get('std_error', 0.0)
        self.lbl_spread.setText(f"Standard Error: ±{prec_val:.5f}") 
    
    def set_y_range(self, max_val):
        self.graph_widget.setYRange(0, max_val, padding=0.1)
        self.graph_widget.enableAutoRange(axis='y', enable=False)