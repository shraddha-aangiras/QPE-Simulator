from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSlider, QDoubleSpinBox, QLabel
from app.style import USE_RADIANS

class SliderWithEdit(QWidget):
    """A combined Slider and SpinBox for float values."""
    valueChanged = QtCore.pyqtSignal(float)

    def __init__(self, parent=None, min=0, max=100, step=1, unit="", vertical=False):
        super(SliderWithEdit, self).__init__(parent)
        self.scale = 1000 
        
        if vertical:
            layout = QVBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.slider = QSlider(QtCore.Qt.Vertical)
        else:
            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            self.slider = QSlider(QtCore.Qt.Horizontal)

        self.edit = QDoubleSpinBox(self)
        
        # Connect internal signals
        self.slider.valueChanged.connect(self.slider_changed)
        self.edit.valueChanged.connect(self.spinbox_changed)
        
        self.edit.setSuffix(f" {unit}")
        self.edit.setDecimals(4) 
        self.edit.setMinimum(min)
        self.edit.setMaximum(max)
        self.edit.setSingleStep(step)
        
        self.slider.setMinimum(int(min * self.scale))
        self.slider.setMaximum(int(max * self.scale))
        self.slider.setSingleStep(int(step * self.scale))

        if vertical:
            layout.addWidget(self.edit)
            if USE_RADIANS:
                pi_label = QLabel("π")
                layout.addWidget(pi_label)
            layout.addWidget(self.slider)
        else:
            layout.addWidget(self.slider)
            layout.addWidget(self.edit)
            if USE_RADIANS:
                pi_label = QLabel("π")
                layout.addWidget(pi_label)
            
        self.setLayout(layout)

    def slider_changed(self):
        val = self.slider.value() / self.scale
        self.edit.blockSignals(True)
        self.edit.setValue(val)
        self.edit.blockSignals(False)
        self.valueChanged.emit(val)

    def spinbox_changed(self):
        val = self.edit.value()
        self.slider.blockSignals(True)
        self.slider.setValue(int(val * self.scale))
        self.slider.blockSignals(False)
        self.valueChanged.emit(val)

    def setValue(self, val):
        self.edit.setValue(val)

    def value(self):
        return self.edit.value()