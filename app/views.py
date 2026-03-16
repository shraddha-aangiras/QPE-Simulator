import numpy as np
import os
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, 
    QFrame, QLabel, QDial, QDoubleSpinBox, QPushButton, QSizePolicy, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QPointF, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QBrush, QPolygonF, QPixmap
from PyQt5.QtSvg import QSvgWidget  
from app.calc import get_theoretical_curve, qpe_p
from app.style import UI_CONFIG, USE_RADIANS

class ResponsiveImageOverlay(QWidget):
    def __init__(self, image_path, max_w_pct=0.55, max_h_pct=0.55, v_offset=0):
        super().__init__()
        self.pixmap = QPixmap(image_path)
        self.v_offset = v_offset
        self.setMinimumSize(300, 200)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.max_screen_w_pct = max_w_pct
        self.max_screen_h_pct = max_h_pct

    def paintEvent(self, event):
        if self.pixmap.isNull(): return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        from PyQt5.QtWidgets import QApplication
        screen_rect = QApplication.primaryScreen().availableGeometry()
        max_w = screen_rect.width() * self.max_screen_w_pct
        max_h = screen_rect.height() * self.max_screen_h_pct

        target_size = self.size()
        if target_size.width() > max_w:
            target_size.setWidth(int(max_w))
        if target_size.height() > max_h:
            target_size.setHeight(int(max_h))

        scaled_pix = self.pixmap.scaled(target_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        img_x = (self.width() - scaled_pix.width()) // 2 + self.v_offset
        img_y = (self.height() - scaled_pix.height()) // 2 + self.v_offset
        painter.drawPixmap(img_x, img_y, scaled_pix)
        self.draw_custom_overlays(painter, img_x, img_y, scaled_pix)

    def draw_custom_overlays(self, painter, img_x, img_y, scaled_pix):
        pass


class InterferometerOverlay(ResponsiveImageOverlay):
    def __init__(self, image_path, max_w_pct=0.55, max_h_pct=0.55):
        super().__init__(image_path, max_w_pct, max_h_pct)
        
        self.p0 = 1.0
        self.p1 = 0.0
        self.count0 = 0
        self.count1 = 0
        
        self.flash0 = False
        self.flash1 = False

        self.det0_x_pct = 0.93
        self.det0_y_pct = 0.10

        self.det1_x_pct = 1.055
        self.det1_y_pct = 0.4

    def set_probabilities(self, p0, p1):
        self.p0 = p0
        self.p1 = p1
        self.update() 

    def set_counts(self, c0, c1):
        self.count0 = c0
        self.count1 = c1
        self.update()

    def trigger_flash(self, det_idx):
        if det_idx == 0:
            self.flash0 = True
        else:
            self.flash1 = True
        self.update()

    def reset_flashes(self):
        self.flash0 = False
        self.flash1 = False
        self.update()

    def draw_custom_overlays(self, painter, img_x, img_y, scaled_pix):
        scale = min(scaled_pix.height() / 400.0, 1.3)

        d0_cx = img_x + (scaled_pix.width() * self.det0_x_pct)
        d0_cy = img_y + (scaled_pix.height() * self.det0_y_pct)
        self.draw_detector(painter, d0_cx, d0_cy, "0", self.p0, self.count0, self.flash0, QColor("#3498db"), scale)

        d1_cx = img_x + (scaled_pix.width() * self.det1_x_pct)
        d1_cy = img_y + (scaled_pix.height() * self.det1_y_pct)
        self.draw_detector(painter, d1_cx, d1_cy, "1", self.p1, self.count1, self.flash1, QColor("#e74c3c"), scale)

    def draw_detector(self, painter, cx, cy, label_text, prob, count, is_flashing, on_color, scale):
        radius = int(22 * scale)
        big_font = max(10, int(18 * scale))
        small_font = max(8, int(13 * scale))

        painter.setPen(QPen(QColor("#222"), max(2, int(3 * scale))))
        brush_color = on_color if is_flashing else QColor("#353535")
        painter.setBrush(QBrush(brush_color))

        if is_flashing:
            painter.setPen(QPen(Qt.white, max(1, int(2 * scale))))

        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", big_font, QFont.Bold))
        text_x = cx + radius + int(10 * scale)
        painter.drawText(int(text_x), int(cy + (big_font/3)), label_text)

        prob_text = f"Probability: {prob * 100:.1f}%"
        counts_text = f"Counts: {count}"
        
        painter.setFont(QFont("Arial", small_font))
        painter.setPen(QColor("#aaa"))
        
        info_x = text_x + int(15 * scale) + big_font
        painter.drawText(int(info_x), int(cy - (small_font/4)), prob_text)
        
        painter.setPen(QColor("#fff")) 
        painter.drawText(int(info_x), int(cy + small_font + 2), counts_text)

class MultiQubitPainter(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(850)
        self.phase_true = 0.0
        self.results = {}
        
        self.c_true_line = QColor("#3498db")    
        self.c_limit_border = QColor("#7f8c8d") 
        self.c_est = QColor("#f1c40f")          
        self.c_conf = QColor(UI_CONFIG["COLORS"][0]) 
        self.c_conf.setAlpha(100) 
        self.c_text = Qt.white
        self.c_grid = QColor("#444")
        self.c_shots = QColor("#bdc3c7")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        margin_left = 120
        margin_right = 220
        top_offset = 80 
        row_h = 70
        line_w = w - margin_left - margin_right

        if USE_RADIANS:
            norm_true_phase = self.phase_true / 2.0
        else:
            norm_true_phase = self.phase_true

        self.draw_legend(painter, w, top_offset)
        
        header_y = top_offset + 10
        painter.setPen(QColor("#aaa"))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.drawText(10, header_y, "Resource Setup")
        painter.drawText(margin_left, header_y, "Experiment Result")
        painter.drawText(w - margin_right + 20, header_y, "Metrics")
        
        painter.setPen(QPen(self.c_grid, 1))
        painter.drawLine(0, header_y + 10, w, header_y + 10)

        for i, n in enumerate(range(1, 11)):
            cy = top_offset + 30 + (i * row_h) + 35
            
            data = self.results.get(n, {})
            est = data.get('phase_est', 0.0)  
            shots_disp = data.get('shots_count', 0)
            std_err = data.get('std_error', 1.0)
            
            if i % 2 == 0:
                painter.fillRect(0, cy - 35, w, row_h, QColor(255, 255, 255, 5))

            painter.setPen(self.c_text)
            painter.setFont(QFont("Arial", 12, QFont.Bold))
            painter.drawText(15, cy - 5, f"{n} Qubits")
            painter.setFont(QFont("Arial", 9))
            painter.setPen(self.c_shots)
            painter.drawText(15, cy + 12, f"Cost: {shots_disp} shots")

            painter.setPen(QPen(QColor("#666"), 2))
            painter.drawLine(margin_left, cy, margin_left + line_w, cy)
            
            N_bins = 2**n
            bin_w = 1.0 / N_bins

            ideal_idx = int(round(norm_true_phase * N_bins)) % N_bins
            ideal_center = ideal_idx / N_bins

            b_left = ideal_center - (bin_w / 2.0)
            b_right = ideal_center + (bin_w / 2.0)

            self.draw_wrapped_box(painter, b_left, b_right, margin_left, line_w, cy)

            est_px = int(margin_left + est * line_w)
            
            true_px = int(margin_left + norm_true_phase * line_w)

            conf_width = std_err * 4.0
            conf_px = int(conf_width * line_w)
            
            c_box_x = est_px - conf_px // 2
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(self.c_conf))
            painter.drawRect(c_box_x, cy - 4, conf_px, 8)

            painter.setPen(QPen(self.c_true_line, 2))
            painter.drawLine(true_px, cy - 20, true_px, cy + 20)

            self.draw_star(painter, est_px, cy, 10, self.c_est)

            metrics_x = w - margin_right + 20
            
            est_idx = int(round(est * N_bins)) % N_bins
            is_resolved = (est_idx == ideal_idx)
            
            dist = abs(est - norm_true_phase)
            dist = min(dist, 1.0 - dist) 

            if USE_RADIANS:
                disp_est = f"{est * 2:.5f}π"
                disp_err = f"{dist * 2:.5f}π"
                disp_bin = f"{bin_w * 2:.5f}π"
            else:
                disp_est = f"{est:.5f}"
                disp_err = f"{dist:.5f}"
                disp_bin = f"{bin_w:.5f}"
            
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            if is_resolved:
                painter.setPen(QColor("#2ecc71"))
                painter.drawText(metrics_x, cy - 10, "✔ Correct Bin")
            else:
                painter.setPen(QColor("#e67e22"))
                painter.drawText(metrics_x, cy - 10, "⚠ Incorrect Bin")
            
            painter.setFont(QFont("Arial", 9))
            painter.setPen(QColor("#f1c40f")) 
            painter.drawText(metrics_x, cy + 2, f"Est:    {disp_est}")
            painter.setPen(QColor("#bbb"))
            painter.drawText(metrics_x, cy + 14, f"Err:    {disp_err}")
            painter.setPen(QColor("#7f8c8d"))
            painter.drawText(metrics_x, cy + 26, f"Bin Size: {disp_bin}")
            

    def draw_wrapped_box(self, painter, left_val, right_val, x_start, width, cy):
        painter.setPen(QPen(self.c_limit_border, 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)

        def draw_rect(v1, v2):
             px1 = int(x_start + v1 * width)
             w_px = max(int((v2 - v1) * width), 2)
             painter.drawRect(px1, cy - 15, w_px, 30)

        if left_val >= 0 and right_val <= 1.0:
            draw_rect(left_val, right_val)
            
        elif left_val < 0:
            draw_rect(0.0, right_val) 
            draw_rect(1.0 + left_val, 1.0)

        elif right_val > 1.0:
            draw_rect(left_val, 1.0) 
            draw_rect(0.0, right_val - 1.0)

    def draw_legend(self, painter, w, h_offset):
        painter.setBrush(QColor(30, 30, 30))
        painter.setPen(Qt.NoPen)
        painter.drawRect(0, 0, w, h_offset)
        
        y = 20
        spacing = 180
        x = 20
        font = QFont("Arial", 10)
        painter.setFont(font)
        
        painter.setPen(QPen(self.c_true_line, 2))
        painter.drawLine(x, y+10, x, y-10)
        painter.setPen(Qt.white)
        painter.drawText(x + 10, y + 5, "True Phase")
        
        x += spacing
        painter.setPen(QPen(self.c_limit_border, 1, Qt.DashLine))
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(x, y - 10, 20, 20)
        painter.setPen(Qt.white)
        painter.drawText(x + 30, y + 5, "Target Bin (Centered)")
        
        x += spacing + 30
        self.draw_star(painter, x, y, 8, self.c_est)
        painter.setPen(Qt.white)
        painter.drawText(x + 15, y + 5, "Estimate")
        
        x += spacing
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
            rad = math.radians(angle_deg)
            points.append(QPointF(cx + radius * math.cos(rad), cy + radius * math.sin(rad)))
        painter.drawPolygon(QPolygonF(points))

class CountsViewTab(QWidget):
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
        self.theory_curve = pg.PlotCurveItem(
            pen=pg.mkPen(color='#FFFFFF', width=2, style=Qt.DashLine)
        )
        self.graph_widget.addItem(self.theory_curve)
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
            if USE_RADIANS:
                txt_phase = f"{(phase_val * 2):.4f}π"
            else:
                txt_phase = f"{phase_val:.4f}"
            item_state = QTableWidgetItem(f"|{state_idx:0{n_qubits}b}>")
            item_phase = QTableWidgetItem(txt_phase)
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
        total_shots = np.sum(counts) if np.sum(counts) > 0 else 100 
        
        x_smooth, y_smooth = get_theoretical_curve(n_qubits, true_phase, total_shots)
        self.theory_curve.setData(x_smooth, y_smooth)
        
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
                      if USE_RADIANS:
                          label = f"{(phase_val * 2):.2f}π"
                      else:
                          label = f"{phase_val:.3f}"
                      ticks.append((x, label))
            ax.setTicks([ticks])
        else:
            self.graph_widget.setXRange(0, N)

        est = data['phase_est']
        diff = abs(est - true_phase)

        if USE_RADIANS:
            val_est = est * 2 
            val_err = abs(val_est - true_phase) 
            val_err = min(val_err, 2.0 - val_err) 
            
            self.lbl_est.setText(f"Est Phase: {val_est:.5f}π")
            self.lbl_err.setText(f"Error: {val_err:.5f}π")
            
            prec_val = data.get('std_error', 0.0) * 2 
            self.lbl_spread.setText(f"Standard Error: ±{prec_val:.5f}π")
        else:
            err = min(diff, 1.0 - diff)
            self.lbl_est.setText(f"Est Phase: {est:.5f}")
            self.lbl_err.setText(f"Error: {err:.5f}")
            prec_val = data.get('std_error', 0.0)
            self.lbl_spread.setText(f"Standard Error: ±{prec_val:.5f}") 
    
    def set_y_range(self, max_val):
        self.graph_widget.setYRange(0, max_val, padding=0.1)
        self.graph_widget.enableAutoRange(axis='y', enable=False)

class PhotonLight(QWidget):
    def __init__(self, color_on="#f1c40f", color_off="#353535"):
        super().__init__()
        self.color_on = QColor(color_on)
        self.color_off = QColor(color_off)
        self.is_on = False
        self.setFixedSize(80, 80)

    def turn_on(self):
        self.is_on = True
        self.update()

    def turn_off(self):
        self.is_on = False
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        painter.setPen(QPen(QColor("#222"), 4))
        
        color = self.color_on if self.is_on else self.color_off
        painter.setBrush(QBrush(color))
        
        if self.is_on:
            painter.setPen(QPen(Qt.white, 2))
            
        painter.drawEllipse(10, 10, 60, 60)

class SinglePhotonTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(current_dir)
        
        #image_path_1 = os.path.join(root_dir, "Fig1.png")
        image_path_1 = os.path.join(root_dir, "Circuit1.png")
        image_path_2 = os.path.join(root_dir, "Fig2.png")
        image_path_if = os.path.join(root_dir, "Interferometer.png")
        
        self.overlay = InterferometerOverlay(image_path_if, max_w_pct=0.4, max_h_pct=0.4)
        layout.addWidget(self.overlay, stretch=3) 

        #layout.addSpacing(10)

        # 1 qubit diagram
        # self.diagram_overlay = ResponsiveImageOverlay(image_path_1, max_w_pct=0.40, max_h_pct=0.30)
        # layout.addWidget(self.diagram_overlay, stretch=2)

        #layout.addSpacing(20)

        row_layout = QHBoxLayout()
        row_layout.setSpacing(0)
        row_layout.addStretch(1)
        
        self.diagram_overlay = ResponsiveImageOverlay(image_path_1, max_w_pct=0.60, max_h_pct=0.60)
        row_layout.addWidget(self.diagram_overlay, stretch=2) 
        self.prediction_widget = QubitPredictionWidget(num_qubits=1)
        self.prediction_widget.setContentsMargins(-250, 0, 0, 0) 
        row_layout.addWidget(self.prediction_widget, stretch=1)
        
        row_layout.addStretch(1)
        layout.addLayout(row_layout, stretch = 2)

        # 2 qubit diagram

        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(0) 
        row2_layout.addStretch(1)
        
        self.circuit_diagram_overlay = ResponsiveImageOverlay(image_path_2, max_w_pct=0.25, max_h_pct=0.25, v_offset=18)
        row2_layout.addWidget(self.circuit_diagram_overlay, stretch=2)
        
        self.multi_prediction_widget = QubitPredictionWidget(num_qubits=2)        
        self.multi_prediction_widget.setContentsMargins(-200, 20, 0, 0)
        row2_layout.addWidget(self.multi_prediction_widget, stretch=1)

        row2_layout.addStretch(1) 
        layout.addLayout(row2_layout, stretch = 2)

        # Timers
        self.auto_timer = QTimer()
        self.auto_timer.setInterval(500)
        self.auto_timer.timeout.connect(self.fire_photon)

        self.flash_timer = QTimer()
        self.flash_timer.setSingleShot(True)
        self.flash_timer.timeout.connect(self.reset_lights)

        self.multi_timer = QTimer()
        self.multi_timer.setInterval(1500)
        self.multi_timer.timeout.connect(self.fire_multi_photon)
        
        self.p0 = 1.0
        self.p1 = 0.0
        self.c0 = 0
        self.c1 = 0
        self.current_phase_val = 0.0

    def update_probabilities(self, val):
        self.reset_experiment()
        theta = val * np.pi
        self.current_phase_val = val / 2 #here change?
        self.p0 = (np.cos(theta / 2))**2
        self.p1 = (np.sin(theta / 2))**2
        self.overlay.set_probabilities(self.p0, self.p1)

    def toggle_auto(self, is_playing):
        if is_playing:
            self.fire_photon()
            self.fire_multi_photon()
            self.auto_timer.start()
            self.multi_timer.start() 
        else:
            self.auto_timer.stop()
            self.multi_timer.stop()
            self.reset_lights()

    def reset_experiment(self):
        self.c0 = 0
        self.c1 = 0
        self.overlay.set_counts(self.c0, self.c1)
        self.reset_lights()

        if hasattr(self, 'prediction_widget'):
            self.prediction_widget.reset()

        if hasattr(self, 'multi_prediction_widget'):
            self.multi_prediction_widget.reset()

    def fire_photon(self):
        self.reset_lights()
        measured_state = np.random.choice([0, 1], p=[self.p0, self.p1])
        
        if measured_state == 0:
            self.c0 += 1
            self.overlay.trigger_flash(0)
        else:
            self.c1 += 1
            self.overlay.trigger_flash(1)
            
        self.overlay.set_counts(self.c0, self.c1)
        self.prediction_widget.update_prediction(measured_state, self.current_phase_val)
        self.flash_timer.start(200)

    def fire_multi_photon(self):
        a, b, c, d = qpe_p(2, 0, self.current_phase_val), qpe_p(2, 1, self.current_phase_val), qpe_p(2, 2, self.current_phase_val), qpe_p(2, 3, self.current_phase_val)
        measured_state = np.random.choice([0, 1, 2, 3], p=[a, b, c, d])
        
        self.multi_prediction_widget.update_prediction(measured_state, self.current_phase_val)

    def reset_lights(self):
        self.overlay.reset_flashes()


class QubitPredictionWidget(QFrame):
    def __init__(self, num_qubits=1):
        super().__init__()
        self.num_qubits = num_qubits
        
        self.setFixedWidth(650) 
        
        main_layout = QHBoxLayout(self) 
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        squares_layout = QVBoxLayout()
        squares_layout.setAlignment(Qt.AlignVCenter)
        squares_layout.setSpacing(10)
        self.default_style = "border: 2px solid #555; border-radius: 8px; background-color: #353535; color: white; font-size: 28px; font-weight: bold;"
        
        self.squares = []
        self.glows = []

        # Generate the squares and glows dynamically
        for _ in range(num_qubits):
            sq = QLabel("-")
            sq.setFixedSize(60, 60)
            sq.setAlignment(Qt.AlignCenter)
            sq.setStyleSheet(self.default_style)
            
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(40)
            glow.setOffset(0, 0)
            glow.setColor(Qt.white)
            glow.setEnabled(False)
            sq.setGraphicsEffect(glow)
            
            squares_layout.addWidget(sq)
            self.squares.append(sq)
            self.glows.append(glow)


        # Text readouts
        stacker = QVBoxLayout()
        stacker.setAlignment(Qt.AlignVCenter)
        stacker.setSpacing(5)
        self.lbl_predicted = QLabel("Shot Phase: --")
        self.lbl_predicted.setStyleSheet("font-size: 14px; color: #fff; margin-top: 10px;")
        
        # self.lbl_error = QLabel("Error: --")
        # self.lbl_error.setStyleSheet("font-size: 14px; color: #ccc;")

        stacker.addWidget(self.lbl_predicted)
        # stacker.addWidget(self.lbl_error)

        # For counts
        counts_layout = QVBoxLayout()
        counts_layout.setAlignment(Qt.AlignVCenter)
        counts_layout.setSpacing(10)
        
        self.count_labels = []
        num_states = 2 ** num_qubits
        for i in range(num_states):
            state_str = format(i, f'0{num_qubits}b')
            state_phase = i * (1.0 / (2 ** num_qubits)) * 2 # Fixed math logic here
            lbl = QLabel(f"{state_phase}π ({state_str}): 0")
            lbl.setStyleSheet("font-size: 14px; color: #ccc;")
            counts_layout.addWidget(lbl)
            self.count_labels.append(lbl)
            
        self.state_counts = {i: 0 for i in range(num_states)}
        
        cumul_layout = QVBoxLayout()
        cumul_layout.setAlignment(Qt.AlignVCenter)
        cumul_layout.setSpacing(5)
        
        self.lbl_cumul_phase = QLabel("Cumulative Phase: --")
        self.lbl_cumul_phase.setStyleSheet("font-size: 14px; color: #fff;")
        
        self.lbl_cumul_error = QLabel("Error: --")
        self.lbl_cumul_error.setStyleSheet("font-size: 14px; color: #ccc;")
        
        cumul_layout.addWidget(self.lbl_cumul_phase)
        cumul_layout.addWidget(self.lbl_cumul_error)
        
        self.total_phase_sum = 0.0
        self.total_shots = 0
        
        main_layout.addLayout(squares_layout)
        main_layout.addLayout(stacker)
        main_layout.addSpacing(25)
        main_layout.addLayout(counts_layout)
        main_layout.addSpacing(25)
        main_layout.addLayout(cumul_layout)

        self.glow_timer = QTimer()
        self.glow_timer.setSingleShot(True)
        self.glow_timer.timeout.connect(self.remove_glow)

    def update_prediction(self, state_val, true_phase_pi):
        # Update each square using bitwise math
        for i in range(self.num_qubits):
            bit = (state_val >> (self.num_qubits - 1 - i)) & 1
            sq = self.squares[i]
            glow = self.glows[i]
            
            sq.setText(str(bit))
            
            if bit == 0:
                sq.setStyleSheet("border: 2px solid #3498db; border-radius: 8px; background-color: #2980b9; color: white; font-size: 28px; font-weight: bold;")
            else:
                sq.setStyleSheet("border: 2px solid #e74c3c; border-radius: 8px; background-color: #c0392b; color: white; font-size: 28px; font-weight: bold;")
            
            glow.setEnabled(True)

        # Standard QPE phase mapping
        # if self.num_qubits == 1:
        #     predicted_val = float(state_val) # 0.0 or 1.0
        #     pred_str = "0π" if state_val == 0 else "π"
        # else:
        #     multiplier = 1.0 / (2 ** self.num_qubits)
        #     predicted_val = state_val * multiplier * 2 # e.g., 0.25, 0.50, 0.75
        #     pred_str = f"{predicted_val:.2f} π"

        multiplier = 1.0 / (2 ** self.num_qubits)
        predicted_val = state_val * multiplier * 2 # e.g., 0.25, 0.50, 0.75
        pred_str = f"{predicted_val:.2f} π"
            
        self.lbl_predicted.setText(f"Shot Phase: {pred_str}")
        
        # Calculate circular phase error 
        # error_val = abs(predicted_val - (true_phase_pi * 2))
        # if error_val > 1.0:
        #     error_val = 2.0 - error_val
            
        # self.lbl_error.setText(f"Error: {error_val:.3f} π")
        
        # if error_val == 0.0:
        #     self.lbl_error.setStyleSheet("font-size: 14px; color: #2ecc71; font-weight: bold;") 
        # else:
        #     self.lbl_error.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
            
        self.state_counts[state_val] += 1
        state_str = format(state_val, f'0{self.num_qubits}b')
        self.count_labels[state_val].setText(f"{predicted_val}π ({state_str}): {self.state_counts[state_val]}")
        
        self.total_shots += 1
        self.total_phase_sum += predicted_val
        cumul_phase = self.total_phase_sum / self.total_shots
        
        self.lbl_cumul_phase.setText(f"Cumulative Phase: {cumul_phase:.3f} π")
        
        cumul_error_val = abs(cumul_phase - (true_phase_pi * 2))
        if cumul_error_val > 1.0:
            cumul_error_val = 2.0 - cumul_error_val
            
        self.lbl_cumul_error.setText(f"Error: {cumul_error_val:.3f} π")
        
        if cumul_error_val == 0.0:
            self.lbl_cumul_error.setStyleSheet("font-size: 14px; color: #2ecc71; font-weight: bold;") 
        else:
            self.lbl_cumul_error.setStyleSheet("font-size: 14px; color: #e74c3c; font-weight: bold;")
            
        self.glow_timer.start(300)

    def remove_glow(self):
        for glow in self.glows:
            glow.setEnabled(False)

    def reset(self):
        # Cleanly resets all squares and text to default
        for sq in self.squares:
            sq.setText("-")
            sq.setStyleSheet(self.default_style)
        self.lbl_predicted.setText("Shot Phase: --")
        # self.lbl_error.setText("Error: --")
        # self.lbl_error.setStyleSheet("font-size: 14px; color: #ccc;")
        
        # Reset running counts
        num_states = 2 ** self.num_qubits
        self.state_counts = {i: 0 for i in range(num_states)}
        for i in range(num_states):
            state_str = format(i, f'0{self.num_qubits}b')
            state_phase = i * (1.0 / (2 ** self.num_qubits)) * 2
            self.count_labels[i].setText(f"{state_phase}π ({state_str}): 0")
            
        self.total_phase_sum = 0.0
        self.total_shots = 0
        self.lbl_cumul_phase.setText("Cumulative Phase: --")
        self.lbl_cumul_error.setText("Error: --")
        self.lbl_cumul_error.setStyleSheet("font-size: 14px; color: #ccc;")