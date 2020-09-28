#!/usr/bin/env python

'''#!/usr/bin/python'''
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QLabel, QPushButton
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
import time
from pyqtgraph.Qt import QtGui, QtCore
import pyqtgraph as pg
import numpy as np
from library_map import MapWindow, LL_NE

class App(QMainWindow):
 
    def __init__(self):
        super().__init__()
        self.title = 'Main'
        self.left = 100
        self.top = 100
        self.width = 500
        self.height = 500
        self.initUI()
		
		# Initialize Variables
        self.t0 = time.time()
        self.tNow = 0.0
        self.n = 0
        self.mapOpen = False
        
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(40) # ms
	
    def update(self):   
		
        """ Update internal variables """
        self.tNow = time.time() - self.t0 # update Time
        TimeString = "Time: " + "{:.2f}".format(self.tNow) + " s" # build Time string
        self.statusBar().showMessage(TimeString)           
        self.n = self.n + 1 # print execution rate

        """ Update map """
        #40.308240
        #-83.546643
        #40.305305
        #-83.541693
        if self.mapOpen:
            self.mapWindow.draw_veh([40.308240, -83.546643, self.n])
            #self.mapWindow.draw_veh([40.305305, -83.541693, self.n])
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.statusBar().showMessage('Message in statusbar.')
        
        """ Map Button """
        self.btnMap = QPushButton(self)
        self.btnMap.setGeometry(10, 10, 200, 80)
        self.btnMap.setText('Map')
        self.btnMap.clicked.connect(self.btnMapClicked)

        self.show()

    def btnMapClicked(self):
        self.initMap()
        
    def initMap(self):
        self.mapWindow = MapWindow()
        self.mapOpen = True
 
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
	

