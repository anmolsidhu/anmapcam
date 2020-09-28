import sys
import time

#from PyQt5.QtGui import *
#from PyQt5.QtCore import *
#from PyQt5.QtWidgets import *

from PyQt4.QtGui import *
from PyQt4 import QtGui, QtCore

#from pyqtgraph.Qt import QtGui, QtCore
#from PyQt5 import QtWidgets, uic

""" Cam Viewer """
class CamWindow(QtGui.QWidget):
	def __init__(self):
		QtGui.QWidget.__init__(self)
		self.setup_ui()

	def setup_ui(self):
		"""Initialize widgets.
		"""
		self.setWindowTitle("Camera")
		self.resize(192, 108)
		self.image_label = QtGui.QLabel()
		self.image_label.resize(320, 240)
		self.quit_button = QtGui.QPushButton("Quit")
		self.quit_button.clicked.connect(self.close)
		self.main_layout = QtGui.QGridLayout()
		self.main_layout.addWidget(self.image_label, 0, 0)
		self.setLayout(self.main_layout)
		self.state = ""
		self.U1 = 0
		self.U2 = 0
		self.V1 = 0
		self.V2 = 0
		self.timeEvent = time.time()
		self.show()

	def update_image(self, img):
		img = QImage(img, img.shape[1], img.shape[0], 
					img.strides[0], QImage.Format_RGB888)
		self.image_label.setPixmap(QPixmap.fromImage(img))

	def mousePressEvent(self, event):
		if event.button() == QtCore.Qt.LeftButton:
			if self.state == "":
				self.U1 = event.x()
				self.V1 = event.y()
				self.state = "zoom1"
				self.timeEvent = time.time()
			if self.state == "zoom1" and time.time()-self.timeEvent > 0.2:
				self.U2 = event.x()
				self.V2 = event.y()
				self.state = ""
				self.timeEvent = time.time()
				print("zoom:", self.U1, self.U2, self.V1, self.V2)
		else:
			print("right")

	def closeEvent(self, event):
		#self.timer.stop()
		print("Camera Closed")
		event.accept() # let the window close
 
def main():
	app = QtWidgets.QApplication(sys.argv)
	camwindow = CamWindow()
	sys.exit(app.exec_())

if __name__ == '__main__':         
	main()
