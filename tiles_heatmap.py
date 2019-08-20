from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QTextEdit,\
	QGridLayout, QGroupBox, QPushButton, QMainWindow, QDesktopWidget, QWidget, QVBoxLayout, QComboBox, \
	QHBoxLayout, QStyleOptionComboBox, QStyle, QStyleOptionViewItem, QStylePainter, QTabWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QThread, QSize, QPoint
from PyQt5.QtGui import QFont, QTextCursor, QTextDocument, QPalette, QAbstractTextDocumentLayout, QPainter, \
			QBrush, QPen, QPalette, QColor
import numpy as np
from scipy.stats import norm


class TileWidget(QWidget):
	tile_emitter = pyqtSignal(object)

	def __init__(self, step_mod, nradius):
		super().__init__()
		self.nradius = nradius
		self.value = 0
		self.color = [0, 0, 255]
		self.step_dir = [0, 1, 0]
		self.step_mod = step_mod
		self.width = 4
		self.height = 7
		self.tile_emitter.connect(lambda x: self.update_tile(x))
		self.setMouseTracking(True)
		self.neighbours = []

	def update_tile(self, new_heat):
		self.value = new_heat
		self.repaint()

	def paintEvent(self, e):
		qp = QPainter()
		qp.begin(self)
		self.draw_widget(qp)
		qp.end()

	def draw_widget(self, qp):

		c = self.rect().center()
		c_coords = c.x(), c.y()

		background_color = self.palette().color(QPalette.Background)

		# draw wheel ring
		qp.setPen(QPen(QColor(*self.color), 3, Qt.SolidLine))
		qp.setBrush(QBrush(QColor(*self.color), Qt.SolidPattern))
		qp.drawRect(0, 0, self.width, self.height)

		# qp.setFont(QFont("times", 12))
		# qp.setPen(QPen(Qt.white, 12, Qt.SolidLine))
		# qp.drawText(c_coords[0] - 3, c_coords[1] + 7, str(self.heat))

		return

	def add_neighbour(self, neighbour_tile, d):
		self.neighbours.append((neighbour_tile, d))

	def heat_up(self, step_mod=None):
		self.value += 1

		if not step_mod:
			step_mod = self.step_mod

		new_color = [x + y for x, y in zip([x*step_mod for x in self.step_dir], self.color)]
		if new_color[1] > 255:
			self.step_dir = [0, 0, -1]
		if new_color[2] < 0:
			self.step_dir = [1, 0, 0]
		if new_color[0] > 255:
			self.step_dir = [0, -1, 0]

		self.color = [max(min(x, 255), 0) for x in new_color]
		print(self.color)

	def mouseMoveEvent(self, event):
		self.heat_up(step_mod=int(norm.pdf(0)*self.step_mod))
		self.repaint()

		for neighbour, d in self.neighbours:
			neighbour.heat_up(int((norm.pdf(d/self.nradius))*self.step_mod))
			neighbour.repaint()


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
		window_dim = 0.15
		self.window.setMinimumWidth(int(ag.width()*window_dim))
		self.window.setMinimumHeight(int(ag.height()*window_dim*2))
		self.window.setMaximumWidth(int(ag.width()*window_dim))
		self.window.setMaximumHeight(int(ag.height()*window_dim*2))

		# create placeholders for widget
		self.pressure_map_group = None
		self.raw_value_group = None
		self.point_labels = []
		self.point_values = []

		self.heatmap_height = 80
		self.heatmap_width = 80

		self.nradius = 8
		self.step_mod = 256

		self.add_widgets()

		# set layout inside window
		self.window.show()

	def start(self):
		return self.app.exec()

	def add_widgets(self):
		self.pressure_map_group = QGroupBox("Pressure map")
		layout = QGridLayout()
		tiles_grid = []
		# create grid of tiles
		for i in range(self.heatmap_height):
			row = []
			for j in range(self.heatmap_width):
				tile = TileWidget(step_mod=self.step_mod, nradius=self.nradius)
				row.append((tile, (i, j)))
				layout.addWidget(tile, i, j, 1, 1)
			tiles_grid.append(row)
		# feed neighbours to each tile

		def dist(p1, p2):
			return np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

		# we now iterate over the grid of tiles
		for row in tiles_grid:
			for tile, coords in row:
				i, j = coords
				# now for the neighbours in as square neighbourhood of side nradius, we check who is at a distance d
				for neighbour_row in tiles_grid[max(0, i - self.nradius):min(self.heatmap_height, i + self.nradius)]:
					for neighbour_tile in neighbour_row[max(0, j - self.nradius):min(self.heatmap_width, j + self.nradius)]:
						ncoords = neighbour_tile[1]
						ntile = neighbour_tile[0]
						d = dist(coords, ncoords)
						if coords != ncoords and d < self.nradius:
							tile.add_neighbour(ntile, d)

		# remove space between tiles
		layout.setSpacing(0)
		self.pressure_map_group.setLayout(layout)

		# set main group as central widget
		self.window.setCentralWidget(self.pressure_map_group)


if __name__ == "__main__":
	ui = HeatMapUI()
	ui.start()
