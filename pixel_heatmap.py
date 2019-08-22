from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QTextEdit,\
	QGridLayout, QGroupBox, QPushButton, QMainWindow, QDesktopWidget, QWidget, QVBoxLayout, QComboBox, QSlider
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QThread, QSize, QPoint
from PyQt5.QtGui import QFont, QTextCursor, QTextDocument, QPalette, QAbstractTextDocumentLayout, QPainter, \
			QBrush, QPen, QPalette, QColor, QImage, QPixmap
import numpy as np
from scipy.stats import norm


class InfoSlider(QGroupBox):
	def __init__(self, start, max, min):
		super().__init__()

		self._slider = QSlider()

		self._slider.setMaximum(max)
		self._slider.setMinimum(min)
		self._slider.setValue(start)

		self.curr = start
		max_label = QLabel(str(max))
		min_label = QLabel(str(min))
		self.curr_label = QLabel(str(self.curr))

		layout = QGridLayout()
		layout.addWidget(max_label, 0, 0, 1, 1)
		layout.addWidget(min_label, 9, 0, 1, 1)
		layout.addWidget(self.curr_label, 5, 0, 1, 1)
		layout.addWidget(self._slider, 0, 2, 10, 2)

		self.setLayout(layout)

	def on_slide(self, funcs):
		for f in funcs:
			self._slider.sliderMoved.connect(f)

	def change_value(self, x):
		self.curr = x
		self.curr_label.setText(str(x))
		self._slider.setValue(x)


class PixelHeatMap(QWidget):
	def __init__(self):
		super().__init__()

		self.color_path = self.generate_color_path()

		c = self.rect()

		self.width = c.width()
		self.height = c.height()

		self.krad = 15
		self.kernel = None
		self.generate_gaussian_kernel()

		self.speed = 16

		self._heatmap = np.stack([np.zeros((self.height, self.width)),
								  np.zeros((self.height, self.width)),
								  255*np.ones((self.height, self.width))], axis=2).astype('uint8')
		self._heatmap_index = np.zeros((self.height, self.width), dtype='uint32')

		def index2color(idx, path):
			if idx < len(path):
				return path[idx]
			else:
				return path[-1]

		self.index2color_vectorizer = np.vectorize(index2color, excluded=['path'], otypes=[np.ndarray], signature='()->(n)')

		self.setMouseTracking(True)

	def reset(self):
		self._heatmap = np.stack([np.zeros((self.height, self.width)),
								  np.zeros((self.height, self.width)),
								  255*np.ones((self.height, self.width))], axis=2).astype('uint8')
		self._heatmap_index = np.zeros((self.height, self.width), dtype='uint32')

	@staticmethod
	def generate_color_path():
		path = []
		color = [0, 0, 255]
		step_dir = [0, 1, 0]

		while color != [255, 0, 0]:

			color = [x + y for x, y in zip(step_dir, color)]
			if color[1] > 255:
				step_dir = [0, 0, -1]
			if color[2] < 0:
				step_dir = [1, 0, 0]
			if color[0] > 255:
				step_dir = [0, -1, 0]

			color = [max(min(x, 255), 0) for x in color]
			path.append(np.array(color).astype('uint8'))

		return path

	def generate_gaussian_kernel(self):
		def dist(p1, p2):
			return np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

		def min_max_scale(x, mx, mn):
			return (x - mn)/(mx - mn)

		s = self.krad*2 + 1
		# check valid kernel size
		assert (s-1) % 2 == 0

		kernel = np.zeros((s, s))
		r = (s-1)/2
		for i in range(s):
			for j in range(s):
				d = dist((r, r), (i, j))
				if d < r:
					norm_d = d/r if d != 0 else d
					kernel[i, j] = norm.pdf(norm_d)
				else:
					kernel[i, j] = 0
		self.kernel = kernel

	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		self.draw_widget(qp)
		qp.end()

	def draw_widget(self, qp):
		heatmap = QImage(self._heatmap.tobytes(), self.width, self.height, 3*self.width, QImage.Format_RGB888)
		qp.drawImage(0, 0, heatmap)

	def mouseMoveEvent(self, event):
		coords = event.pos()
		x, y = coords.x(), coords.y()

		if 0 < x < self.width and 0 < y < self.height:

			h_before = int(x - self.krad)
			h_after = int(x + self.krad) + 1
			v_before = int(y - self.krad)
			v_after = int(y + self.krad) + 1

			# if any of the dimensions is negative, we must trim the kernel in that direction
			kernel = self.kernel

			if h_before < 0:
				kernel = kernel[:, abs(h_before):]
				h_before = 0
			if h_after > self.width:
				kernel = kernel[:, :-(h_after - self.width)]
				h_after = self.width
			if v_before < 0:
				kernel = kernel[abs(v_before):, :]
				v_before = 0
			if v_after > self.height:
				kernel = kernel[:-(v_after - self.height), :]
				v_after = self.height

			self._heatmap_index[v_before:v_after, h_before:h_after] += (kernel * self.speed).astype('uint32')

			mask = self._heatmap_index[v_before:v_after, h_before:h_after]

			self._heatmap[v_before:v_after, h_before:h_after, :] = self.index2color_vectorizer(mask, path=self.color_path).astype('uint8')
			self.repaint()


class HeatMapUI:
	def __init__(self):
		ui_name = "heatmap"
		self.app = QApplication([ui_name])
		self.app.setObjectName(ui_name)
		self.UI_name = ui_name
		# set app style
		self.app.setStyle("Fusion")
		# create main window
		self.window = QMainWindow()
		self.window.setWindowTitle(ui_name)
		self.window.setObjectName(ui_name)

		# create placeholders for widget
		self.heatmap = None

		self.add_widgets()

		# set window geometry
		ag = QDesktopWidget().availableGeometry()
		self.window.move(int(ag.width()*0.15), int(ag.height()*0.05))
		factor = 1.2
		self.window.setMinimumWidth(int(self.heatmap.width*factor))
		self.window.setMinimumHeight(int(self.heatmap.height))
		self.window.setMaximumWidth(int(self.heatmap.width*factor))
		self.window.setMaximumHeight(int(self.heatmap.height))

		# set layout inside window
		self.window.show()

	def start(self):
		return self.app.exec()

	def add_widgets(self):
		# set main group as central widget
		main_group = QGroupBox()
		self.window.setCentralWidget(main_group)

		# create main groups's layout
		main_layout = QGridLayout()

		# add heatmap inside a label
		self.heatmap = PixelHeatMap()
		main_layout.addWidget(self.heatmap, 0, 0, 10, 10)

		# add kernel size slider
		krad_slider = InfoSlider(20, 100, 0)
		krad_slider.on_slide([lambda x: setattr(self.heatmap, "krad", x if x % 2 else x-1),
							   self.heatmap.generate_gaussian_kernel,
							   lambda x: krad_slider.change_value(x if x % 2 else x-1)])
		main_layout.addWidget(krad_slider, 0, 13, 9, 1)

		speed_slider = InfoSlider(self.heatmap.speed, 100, 0)
		speed_slider.on_slide([lambda x: setattr(self.heatmap, "speed", 2*x),
							   lambda x: speed_slider.change_value(x)])
		main_layout.addWidget(speed_slider, 0, 12, 9, 1)

		# add reset heatmap button
		reset_button = QPushButton("Reset")
		reset_button.clicked.connect(self.heatmap.reset)
		main_layout.addWidget(reset_button, 9, 12, 1, 1)

		# set main group's layout
		main_group.setLayout(main_layout)


if __name__ == "__main__":
	ui = HeatMapUI()
	ui.start()