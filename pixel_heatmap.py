from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QTextEdit,\
	QGridLayout, QGroupBox, QPushButton, QMainWindow, QDesktopWidget, QWidget, QVBoxLayout, QComboBox, \
	QHBoxLayout, QStyleOptionComboBox, QStyle, QStyleOptionViewItem, QStylePainter, QTabWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QThread, QSize, QPoint
from PyQt5.QtGui import QFont, QTextCursor, QTextDocument, QPalette, QAbstractTextDocumentLayout, QPainter, \
			QBrush, QPen, QPalette, QColor, QImage
import numpy as np
from scipy.stats import norm


class PixelHeatMap(QWidget):
	def __init__(self):
		super().__init__()

		self.step_mod = 40
		self.color_path = self.generate_color_path()

		self.width = 400
		self.height = 400

		self._heatmap = np.stack([255*np.ones((self.width, self.height)), np.zeros((self.width, self.height)), np.zeros((self.width, self.height))], axis=2)
		# self._heatmap = np.stack([255*np.ones((self.width, self.height)), 255*np.ones((self.width, self.height)), 255*np.ones((self.width, self.height))], axis=2)
		self._heatmap_index = np.zeros((self.width, self.height))

		self.setMouseTracking(True)

	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		self.draw_widget(qp)
		qp.end()

	def draw_widget(self, qp):
		height, width, channel = self._heatmap.shape
		heatmap = QImage(self._heatmap.tobytes(), width, height, 3*width, QImage.Format_RGB666)
		qp.drawImage(0, 0, heatmap)

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
			path.append(color)

		return path

	def mouseMoveEvent(self, event):
		coords = event.pos()
		print(coords)
		x, y = coords.x(), coords.y()

		if x <= self.width and y <= self.height:
			self._heatmap_index[x, y] += 1
			self._heatmap[x, y, :] = self.color_path[int(self._heatmap_index[x, y])]
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
		# ag = QDesktopWidget().availableGeometry()
		# self.window.move(int(ag.width()*0.15), int(ag.height()*0.05))
		# window_dim = 0.4
		# self.window.setMinimumWidth(int(ag.width()*window_dim))
		# self.window.setMinimumHeight(int(ag.height()*window_dim))
		# self.window.setMaximumWidth(int(ag.width()*window_dim))
		# self.window.setMaximumHeight(int(ag.height()*window_dim))

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
