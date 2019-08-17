from PyQt5.QtWidgets import QApplication, QLabel, QFileDialog, QTextEdit,\
	QGridLayout, QGroupBox, QPushButton, QMainWindow, QDesktopWidget, QWidget, QVBoxLayout, QComboBox, \
	QHBoxLayout, QStyleOptionComboBox, QStyle, QStyleOptionViewItem, QStylePainter, QTabWidget
from PyQt5.QtCore import Qt, QObject, pyqtSignal, pyqtSlot, QThread, QSize, QPoint
from PyQt5.QtGui import QFont, QTextCursor, QTextDocument, QPalette, QAbstractTextDocumentLayout, QPainter, \
			QBrush, QPen, QPalette, QColor


class TileWidget(QWidget):
	tile_emitter = pyqtSignal(object)

	def __init__(self):
		super().__init__()
		self.value = 0
		self.color = [0, 0, 255]
		self.step_dir = [0, 1, 0]
		self.step_mod = 5
		self.size = 15
		self.tile_emitter.connect(lambda x: self.update_tile(x))
		self.setMouseTracking(True)

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
		qp.drawRect(0, 0, self.size, self.size)

		# qp.setFont(QFont("times", 12))
		# qp.setPen(QPen(Qt.white, 12, Qt.SolidLine))
		# qp.drawText(c_coords[0] - 3, c_coords[1] + 7, str(self.heat))

		return

	def heat_up(self, step_mod = None):
		self.value += 1

		new_color = [x + y for x, y in zip([x*self.step_mod for x in self.step_dir], self.color)]
		print(new_color)
		if new_color[1] > 255:
			self.step_dir = [0, 0, -1]
		if new_color[2] < 0:
			self.step_dir = [1, 0, 0]
		if new_color[0] > 255:
			self.step_dir = [0, -1, 0]

		self.color = [max(min(x, 255), 0) for x in new_color]

	def mouseMoveEvent(self, event):
		self.heat_up()
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
		self.window.setMinimumWidth(int(ag.width()*0.7))
		self.window.setMinimumHeight(int(ag.height()*0.7))
		self.window.setMaximumWidth(int(ag.width()*0.7))
		self.window.setMaximumHeight(int(ag.height()*0.7))

		# create placeholders for widgets
		self.pressure_map_group =None
		self.raw_value_group = None
		self.point_labels = []
		self.point_values = []

		self.heatmap_height = 40
		self.heatmap_width = 140

		self.add_widgets()

		# set layout inside window
		self.window.show()

	def start(self):
		return self.app.exec()

	def add_widgets(self):
		self.pressure_map_group = QGroupBox("Pressure map")
		layout = QGridLayout()
		tiles = []
		# create grid of tiles
		for i in range(self.heatmap_height):
			for j in range(self.heatmap_width):
				tile = TileWidget()
				tiles.append(tile)
				layout.addWidget(tile, i, j, 1, 1)
		# feed neighbours to each tile

		layout.setSpacing(0)
		self.pressure_map_group.setLayout(layout)

		# set main group as central widget
		self.window.setCentralWidget(self.pressure_map_group)


if __name__ == "__main__":
	ui = HeatMapUI()
	ui.start()
