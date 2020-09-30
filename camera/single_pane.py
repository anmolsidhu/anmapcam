#from library import *
from PyQt5 import QtWidgets, uic, QtGui, QtCore
from PyQt5.QtGui import QPixmap, QPainter
import sys
import os
import time
import math
from math import cos, sin, pi
import numpy as np
#import queue
import configparser

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import imutils
from imutils.video import WebcamVideoStream
from imutils.video import FPS
import cv2
import json

class MainWindow(QtWidgets.QMainWindow):

	def __init__(self, *args, **kwargs):
		super(MainWindow, self).__init__(*args, **kwargs)
		uic.loadUi('single_pane.ui', self)
		
		""" Init Timer """
		self.timer = QTimer()
		self.timer.timeout.connect(self.update)
		self.timer.start(10) # ms

		""" Init Variables """
		self.t0 = time.time()
		self.tLast = self.t0
		self.tNow = 0
		self.n = 0
		self.fps = 0
		self.firstCall = True
		self.camOpen = False
		self.chartOpen = False
		# Chart
		self.plotTime = np.linspace(-1, 0, num=200)
		self.plotRed = 0*self.plotTime
		self.plotGreen = 0*self.plotTime
		self.plotBlue = 0*self.plotTime

		""" Initialize """
		self.initUI()
		self.initCam()
		self.initChart()
		
	def update(self):
		""" Update internal variables """
		self.tNow = time.time() - self.t0 # update Time
		# execution rate
		if time.time() - self.tLast >= 1.0:
			self.fps = self.n
			self.n = 0
			self.tLast = time.time()          
		self.n = self.n + 1 
		StatusString = "Time: "+"{:.2f}".format(self.tNow) + " s, FPS: "+"{:.0f}".format(self.fps)# build status
		self.statusBar().showMessage(StatusString) 
		
		""" Read Camera and Update Image Label"""
		frame = self.vs.read()
		# Get frame size
		if self.firstCall:
			self.imgWidth = frame.shape[1]
			self.imgHeight = frame.shape[0]
			self.imgU1 = 0
			self.imgV1 = 0
			self.imgU2 = self.imgWidth
			self.imgV2 = self.imgHeight
		frame = imutils.resize(frame, width=self.imgLabelWidth) # adjust image size to image label size

		# RGB content
		meanB = np.mean(frame[self.imgU1:self.imgU2,self.imgV1:self.imgV2,0])
		meanG = np.mean(frame[self.imgU1:self.imgU2,self.imgV1:self.imgV2,1])
		meanR = np.mean(frame[self.imgU1:self.imgU2,self.imgV1:self.imgV2,2])

		""" Update Chart """
		if self.chartOpen:
			self.plotTime[:-1] = self.plotTime[1:]
			self.plotTime[-1] = self.tNow
			self.plotRed[:-1] = self.plotRed[1:]
			self.plotRed[-1] = meanR
			self.plotGreen[:-1] = self.plotGreen[1:]
			self.plotGreen[-1] = meanG
			self.plotBlue[:-1] = self.plotBlue[1:]
			self.plotBlue[-1] = meanB
			self.plotData()

		# Update image label
		if self.camOpen:
			img = cv2.cvtColor(frame[self.imgV1:self.imgV2, self.imgU1:self.imgU2], cv2.COLOR_BGR2RGB)
			img = QImage(img, img.shape[1], img.shape[0], 
					img.strides[0], QImage.Format_RGB888)
			self.imgLabel.setPixmap(QPixmap.fromImage(img))

		if self.firstCall:
			self.firstCall = False
	
	def plotData(self):
		self.p1.plot1.setData(self.plotTime, self.plotRed)
		self.p1.plot2.setData(self.plotTime, self.plotGreen)
		self.p1.plot3.setData(self.plotTime, self.plotBlue)

	def btnCamClicked(self):
		self.camOpen = not(self.camOpen)
		if self.camOpen:
			self.labelCamOn.setStyleSheet("background-color: lightgreen")
			self.labelCamOn.setText('On')
		else:
			self.labelCamOn.setStyleSheet("background-color: lightgray") 
			self.labelCamOn.setText('Off')

	def btnChartClicked(self):
		self.chartOpen = not(self.chartOpen)
		if self.chartOpen:
			self.labelChartOn.setStyleSheet("background-color: lightgreen")
			self.labelChartOn.setText('On')
		else:
			self.labelChartOn.setStyleSheet("background-color: lightgray") 
			self.labelChartOn.setText('Off')

	def initUI(self):
		""" Buttons and Clicks """
		self.btnCam.clicked.connect(self.btnCamClicked)
		self.btnChart.clicked.connect(self.btnChartClicked)
		
		""" Labels """
		self.labelCamOn.setText('Off')
		self.labelCamOn.setAlignment(QtCore.Qt.AlignCenter) 
		self.labelCamOn.setStyleSheet("background-color: lightgray") 

		self.labelChartOn.setText('Off')
		self.labelChartOn.setAlignment(QtCore.Qt.AlignCenter) 
		self.labelChartOn.setStyleSheet("background-color: lightgray") 

		""" Window and Layout """
		self.setWindowTitle("Visual Detection")
		self.setFixedSize(self.size())
		self.move(50, 50)
		self.layout = pg.GraphicsLayout(border=(0,0,0)) # layout central widget
		self.graphicsView.setFixedSize(self.graphicsView.width(), self.graphicsView.height())
		self.graphicsView.setCentralItem(self.layout)

	def initCam(self):
		self.vs = WebcamVideoStream(src=0).start()
		self.imgLabelWidth = self.imgLabel.width()

	def initChart(self):
		self.p1 = self.layout.addPlot(title="RGB")
		self.p1.plot1 = self.p1.plot([], [], pen=pg.mkPen(color=(255,0,0),width=2), name="Red")
		self.p1.plot2 = self.p1.plot([], [], pen=pg.mkPen(color=(0,255,0),width=2), name="Green")
		self.p1.plot3 = self.p1.plot([], [], pen=pg.mkPen(color=(0,0,255),width=2), name="Blue")
		#self.p1.setRange(xRange={-100,100})
		#self.p1.setRange(yRange={-1,11})
		self.p1.setLabel('left', "RGB Mean")
		self.p1.setLabel('bottom', "Time [s]")
		self.p1.showGrid(x=True, y=True)
      	
def main():
	app = QtWidgets.QApplication(sys.argv)
	mainwindow = MainWindow()
	mainwindow.show()
	sys.exit(app.exec_())

if __name__ == '__main__':         
	main()