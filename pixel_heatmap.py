from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QTextEdit,\
	QGridLayout, QGroupBox, QPushButton, QMainWindow, QDesktopWidget, QWidget, QVBoxLayout, QComboBox, \
	QHBoxLayout, QStyleOptionComboBox, QStyle, QStyleOptionViewItem, QStylePainter, QTabWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QThread, QSize, QPoint
from PyQt5.QtGui import QFont, QTextCursor, QTextDocument, QPalette, QAbstractTextDocumentLayout, QPainter, \
			QBrush, QPen, QPalette, QColor, QImage
import numpy as np
from scipy.stats import norm
from scipy.stats import norm


class PixelHeatMap(QWidget):
	def __init__(self):
		super().__init__()

		self.color_path = self.generate_color_path()

		self.width = 400
		self.height = 400

		self.kernel_size = 31
		self.krad = int((self.kernel_size - 1) / 2)
		self.kernel = self.generate_gaussian_kernel(self.kernel_size)

		self.step = 16

		self._heatmap = np.stack([np.zeros((self.width, self.height)),
								  np.zeros((self.width, self.height)),
								  255*np.ones((self.width, self.height))], axis=2).astype('uint8')
		self._heatmap_index = np.zeros((self.width, self.height), dtype='uint32')

		def index2color(idx, path):
			if idx < len(path):
				return path[idx]
			else:
				return path[-1]

		self.index2color_vectorizer = np.vectorize(index2color, excluded=['path'], otypes=[np.ndarray], signature='()->(n)')

		self.setMouseTracking(True)

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

	@staticmethod
	def generate_gaussian_kernel(s):
		def dist(p1, p2):
			return np.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

		# check valid kernel size
		assert (s-1) % 2 == 0

		kernel = np.zeros((s, s))
		r = (s-1)/2
		for i in range(s):
			for j in range(s):
				d = dist((r, r), (i, j))
				if d < r:
					norm_d = d/s if d != 0 else d
					kernel[i, j] = norm.pdf(norm_d)
				else:
					kernel[i, j] = 0
		return kernel

	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		self.draw_widget(qp)
		qp.end()

	def draw_widget(self, qp):

		# transposed_heatmap = np.transpose(self._heatmap, axes=(1, 0, 2))
		transposed_heatmap = self._heatmap
		width, height, channels = transposed_heatmap.shape

		heatmap = QImage(transposed_heatmap.tobytes(), width, height, 3*width, QImage.Format_RGB888)
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

			self._heatmap_index[v_before:v_after, h_before:h_after] += (kernel * self.step).astype('uint32')

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
		# set window geometry
		ag = QDesktopWidget().availableGeometry()
		self.window.move(int(ag.width()*0.15), int(ag.height()*0.05))
		window_dim = 0.8
		self.window.setMinimumWidth(int(ag.width()*window_dim))
		self.window.setMinimumHeight(int(ag.height()*window_dim))
		self.window.setMaximumWidth(int(ag.width()*window_dim))
		self.window.setMaximumHeight(int(ag.height()*window_dim))

		# create placeholders for widget
		self.heatmap = None

		self.heatmap_height = 80
		self.heatmap_width = 80

		self.nradius = 8
		self.step_mod = 128

		self.add_widgets()

		# set layout inside window
		self.window.show()

	def start(self):
		return self.app.exec()

	def add_widgets(self):
		self.heatmap = PixelHeatMap()
		# set main group as central widget
		self.window.setCentralWidget(self.heatmap)


if __name__ == "__main__":
	ui = HeatMapUI()
	ui.start()
