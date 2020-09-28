#!/usr/bin/python
import sys
#from PyQt4.QtWidgets import QApplication, QWidget, QMainWindow, QLabel, QPushButton
#from PyQt4 import QtWidgets, QtGui, QtCore
#from PyQt4.QtGui import QIcon
import time

from PyQt4.QtGui import *
#from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from library_cam import *
import imutils
from imutils.video import WebcamVideoStream
from imutils.video import FPS
import cv2
import json
import pyqtgraph as pg


class GraphWindow():
    def __init__(self):

        self.win = pg.GraphicsWindow(title="Graphs 1")
        self.win.move(700, 10)
        # cannvas 1
        self.canvas1 = self.win.addPlot(title="Plot 1", labels={'left': 'RGB', 'bottom': 'Time (sec)'})	
        self.canvas1.plot1 = self.canvas1.plot(pen='r')
        self.canvas1.plot2 = self.canvas1.plot(pen='g')
        self.canvas1.plot3 = self.canvas1.plot(pen='b')
        # canvas 2
        #self.canvas2 = self.win.addPlot(title="Plot 2", labels={'left': ('Y Label 2'), 'bottom': ('X Label 2')})
        #self.canvas2.plot1 = self.canvas2.plot(pen='r')
        #self.canvas2.plot2 = self.canvas2.plot(pen='g')


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
        srcCam = 0
        self.plotTime = np.linspace(-1, 0, num=150)
        self.plotRed = 0*self.plotTime
        self.plotGreen = 0*self.plotTime
        self.plotBlue = 0*self.plotTime
        self.chart = True
        self.n = 0
        self.fps = 0
        self.camOpen = False

        # Open Config
        self.rgbDelta = [50, 50, 50]
        self.rgbDelta, ROI = self.openConfig()

        # Initialize RGB Logic Variables
        self.imgU1 = ROI[0]
        self.imgV1 = ROI[1]
        self.imgU2 = ROI[2]
        self.imgV2 = ROI[3]      
        self.resetN = 0
        self.moveN = 20
        self.arrR = 0*np.linspace(0, 0, self.moveN)
        self.arrG = self.arrR*0
        self.arrB = self.arrR*0
        self.alert = False
        self.baseR = 0
        self.baseG = 0
        self.baseB = 0
        self.firstCall = True

        # Initialize Camera
        self.vs = WebcamVideoStream(src=srcCam).start()
        #self.vs = cv2.VideoCapture(0)
        #self.fps = FPS().start()
        
        # Initialize Main Timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(10) # ms

        # Initialize Time
        self.t0 = time.time()
        self.tLast = time.time()
        self.tNow = 0.0
	
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

        """ Read Camera """
        frame = self.vs.read()

        # Get frame size
        if self.firstCall:
            self.imgWidth = frame.shape[1]
            self.imgHeight = frame.shape[0]
            print(frame.shape)
            # dont set image size, instead read from config
            #self.imgU2 = self.imgWidth
            #self.imgV2 = self.imgHeight

        #(grabbed, frame) = self.vs.read()
        #frame = 
        #frame = imutils.resize(frame, width=400)
        meanB = np.mean(frame[self.imgU1:self.imgU2,self.imgV1:self.imgV2,0])
        meanG = np.mean(frame[self.imgU1:self.imgU2,self.imgV1:self.imgV2,1])
        meanR = np.mean(frame[self.imgU1:self.imgU2,self.imgV1:self.imgV2,2])

        """ Update Chart """
        if self.chart and self.resetN >= self.moveN:
            self.plotTime[:-1] = self.plotTime[1:]
            self.plotTime[-1] = self.tNow
            self.plotRed[:-1] = self.plotRed[1:]
            self.plotRed[-1] = meanR
            self.plotGreen[:-1] = self.plotGreen[1:]
            self.plotGreen[-1] = meanG
            self.plotBlue[:-1] = self.plotBlue[1:]
            self.plotBlue[-1] = meanB
            self.plotData()

        """ RGB Logic """
        # compute moving average of past points
        movMeanR = np.mean(self.arrR) 
        movMeanG = np.mean(self.arrG)
        movMeanB = np.mean(self.arrB)

        # rgb check for alert rising edge
        rgbCheck = [False, False, False]
        if self.resetN >= self.moveN: # check only if not in reset condition
            if not self.alert:
                ### red check
                if self.rgbDelta[0] == 0: # don't check red [0]
                    rgbCheck[0] = True
                elif self.rgbDelta[0] > 0:
                    if meanR - movMeanR >= self.rgbDelta[0]:
                        rgbCheck[0] = True
                else:
                    if meanR - movMeanR <= self.rgbDelta[0]:
                        rgbCheck[0] = True
                ### green check
                if self.rgbDelta[1] == 0: # don't check green [1]
                    rgbCheck[1] = True
                elif self.rgbDelta[1] > 0:
                    if meanG - movMeanG >= self.rgbDelta[1]:
                        rgbCheck[1] = True
                else:
                    if meanG - movMeanG <= self.rgbDelta[1]:
                        rgbCheck[1] = True
                ### blue check
                if self.rgbDelta[2] == 0: # don't check blue [2]
                    rgbCheck[2] = True
                elif self.rgbDelta[2] > 0:
                    if meanB - movMeanB >= self.rgbDelta[2]:
                        rgbCheck[2] = True
                else:
                    if meanB - movMeanB <= self.rgbDelta[2]:
                        rgbCheck[2] = True
                # if all conditions met, set alert TRUE
                if all(rgbCheck):
                    self.alert = True
                    self.baseR = movMeanR
                    self.baseG = movMeanG
                    self.baseB = movMeanB
                    self.labelVisual.setStyleSheet("background-color: lightgreen") 

        # rgb check for alert falling edge
        if self.alert:
            rgbCheck = [True, True, False]
            ### red check
            if self.rgbDelta[0] == 0: # don't check red [0]
                rgbCheck[0] = True
            else:
                if abs(self.baseR - meanR) <= 0.5*abs(self.rgbDelta[0]):
                    rgbCheck[0] = True
            ### green check
            if self.rgbDelta[1] == 0: # don't check green [1]
                rgbCheck[1] = True
            else:
                if abs(self.baseG - meanG) <= 0.5*abs(self.rgbDelta[1]):
                    rgbCheck[1] = True
            ### blue check
            if self.rgbDelta[2] == 0: # don't check blue [2]
                rgbCheck[2] = True
            else:
                if abs(self.baseB - meanB) <= 0.5*abs(self.rgbDelta[2]):
                    rgbCheck[2] = True
            # if all conditions met, set alert FALSE
                if all(rgbCheck):
                    self.alert = False
                    self.labelVisual.setStyleSheet("background-color: lightgray") 
        
        # if reset then make all zeros (might be unnecessary)
        if self.resetN == 0:
            self.arrR = 0*np.linspace(0, 0, self.moveN)
            self.arrG = self.arrR*0
            self.arrB = self.arrR*0     

        # start incrementing to measure reset in progress
        if self.resetN < self.moveN:
            self.resetN = self.resetN + 1
            self.alert = False

        # add the new point to past
        self.arrR[:-1] = self.arrR[1:]
        self.arrR[-1] = meanR
        self.arrG[:-1] = self.arrG[1:]
        self.arrG[-1] = meanG
        self.arrB[:-1] = self.arrB[1:]
        self.arrB[-1] = meanB

        #cv2.imshow("Frame", frame)
        #key = cv2.waitKey(1) & 0xFF
        if self.camOpen:
                """ Update Cam """
                self.camWindow.update_image(cv2.cvtColor(frame[self.imgV1:self.imgV2, self.imgU1:self.imgU2], cv2.COLOR_BGR2RGB))
        #self.fps.update()

        if self.firstCall:
            self.firstCall = False
    
    def plotData(self):
        self.graphWindow1.canvas1.plot1.setData(self.plotTime, self.plotRed)
        self.graphWindow1.canvas1.plot2.setData(self.plotTime, self.plotGreen)
        self.graphWindow1.canvas1.plot3.setData(self.plotTime, self.plotBlue)
        #self.graphWindow1.canvas2.plot1.setData(self.tarr, self.xarr)
        #self.graphWindow1.canvas2.plot2.setData(self.tarr, 2*self.xarr)

    def openConfig(self):
        # Open config json and populate rgb delta as well as controls on GUI
        with open('config.txt') as json_file:
            rgbDelta = [50, 50, 50]
            ROI = [0, 100, 0, 100]
            config = json.load(json_file)
            for item in config['Color_Threshold']:
                if item['color'] == 'red':
                    rgbDelta[0] = item['value']
                    self.numRthresh.setText(str(rgbDelta[0])) # gui R
                elif item['color'] == 'green':
                    rgbDelta[1] = item['value']
                    self.numGthresh.setText(str(rgbDelta[1])) # gui G
                elif item['color'] == 'blue':
                    rgbDelta[2] = item['value']
                    self.numBthresh.setText(str(rgbDelta[2])) # gui B
            for item in config['ROI']:
                if item['position'] == 'U1':
                    ROI[0] = int(item['value'])
                elif item['position'] == 'V1':
                    ROI[1] = int(item['value'])
                elif item['position'] == 'U2':
                    ROI[2] = int(item['value'])
                elif item['position'] == 'V2':
                    ROI[3] = int(item['value'])
        return rgbDelta, ROI

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.statusBar().showMessage('Message in statusbar.')
        
        """ Cam Button """
        self.btnCam = QPushButton(self)
        self.btnCam.setGeometry(10, 10, 200, 80)
        self.btnCam.setText('Cam')
        self.btnCam.clicked.connect(self.btnCamClicked)

        """ Chart Button """
        self.btnChart = QPushButton(self)
        self.btnChart.setGeometry(10, 110, 200, 80)
        self.btnChart.setText('Chart')
        self.btnChart.clicked.connect(self.btnChartClicked)

        """ Reset Button """
        self.btnReset = QPushButton(self)
        self.btnReset.setGeometry(240, 110, 200, 80)
        self.btnReset.setText('Reset')
        self.btnReset.clicked.connect(self.btnResetClicked)

        """ Label Visual Alert """
        self.labelVisual = QLabel(self) 
        self.labelVisual.setGeometry(240, 10, 200, 80) 
        self.labelVisual.setText('Visual')
        self.labelVisual.setAlignment(QtCore.Qt.AlignCenter) 
        self.labelVisual.setStyleSheet("background-color: lightgray") 

        """ Save Button """
        self.btnSave = QPushButton(self)
        self.btnSave.setGeometry(240, 370, 200, 80)
        self.btnSave.setText('Save')
        self.btnSave.clicked.connect(self.btnSaveClicked)

        """ Zoom Button """
        self.btnZoom = QPushButton(self)
        self.btnZoom.setGeometry(10, 370, 200, 80)
        self.btnZoom.setText('Zoom')
        self.btnZoom.clicked.connect(self.btnZoomClicked)

        """ Fit Button """
        self.btnFit = QPushButton(self)
        self.btnFit.setGeometry(10, 280, 200, 80)
        self.btnFit.setText('Fit')
        self.btnFit.clicked.connect(self.btnFitClicked)

        """ Controls """
        # Red
        self.labelRthresh = QLabel(self) 
        self.labelRthresh.setGeometry(260, 210, 50, 40) 
        self.labelRthresh.setText('R')
        self.labelRthresh.setAlignment(QtCore.Qt.AlignCenter) 
        self.numRthresh = QLineEdit(self)
        self.numRthresh.setGeometry(300, 210, 100, 40)
        self.numRthresh.setAlignment(QtCore.Qt.AlignLeft) 
        # Green
        self.labelGthresh = QLabel(self) 
        self.labelGthresh.setText('G')
        self.labelGthresh.setGeometry(260, 260, 50, 40) 
        self.labelGthresh.setAlignment(QtCore.Qt.AlignCenter) 
        self.numGthresh = QLineEdit(self)
        self.numGthresh.setGeometry(300, 260, 100, 40)
        self.numGthresh.setAlignment(QtCore.Qt.AlignLeft) 
        # Blue
        self.labelBthresh = QLabel(self) 
        self.labelBthresh.setGeometry(260, 310, 50, 40) 
        self.labelBthresh.setText('B')
        self.labelBthresh.setAlignment(QtCore.Qt.AlignCenter) 
        self.numBthresh = QLineEdit(self)
        self.numBthresh.setGeometry(300, 310, 100, 40)
        self.numBthresh.setAlignment(QtCore.Qt.AlignLeft) 

        """ Chart Window """
        self.graphWindow1 = GraphWindow()
        self.graphWindow1.canvas1.setRange(yRange={-1,256})

        self.show()

    def btnCamClicked(self):
        self.camWindow = CamWindow()
        self.camOpen = True

    def btnChartClicked(self):
        self.chart = not(self.chart)

    def btnResetClicked(self):
        self.resetN = 0
        self.alert = False
        self.labelVisual.setStyleSheet("background-color: lightgray") 

    def btnSaveClicked(self):   
        config = {}
        config['Color_Threshold'] = []
        config['Color_Threshold'].append({
            'color': 'red',
            'value': int(self.numRthresh.text())
        })
        config['Color_Threshold'].append({
            'color': 'green',
            'value': int(self.numGthresh.text())
        })
        config['Color_Threshold'].append({
            'color': 'blue',
            'value': int(self.numBthresh.text())
        })

        config['ROI'] = []
        config['ROI'].append({
            'position': 'U1',
            'value': self.imgU1
        })
        config['ROI'].append({
            'position': 'V1',
            'value': self.imgV1
        })
        config['ROI'].append({
            'position': 'U2',
            'value': self.imgU2
        })
        config['ROI'].append({
            'position': 'V2',
            'value': self.imgV2
        })
        
        with open('config.txt', 'w') as outfile:
            json.dump(config, outfile, indent=4)

    def btnZoomClicked(self):
        if self.camOpen:
            self.imgU1 = self.camWindow.U1 - 12 # 25 is standard window border for some reason
            self.imgU2 = self.camWindow.U2 - 12
            self.imgV1 = self.camWindow.V1 - 12
            self.imgV2 = self.camWindow.V2 - 12

    def btnFitClicked(self):
        if self.camOpen:
            self.imgU1 = 0
            self.imgU2 = self.imgWidth
            self.imgV1 = 0
            self.imgV2 = self.imgHeight

    def closeEvent(self, event):
        #self.fps.stop()
        self.vs.stop()
        #cv2.destroyAllWindows()
        self.timer.stop()
        print("Main Closed")
        event.accept() 

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
