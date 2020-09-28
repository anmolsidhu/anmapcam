from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QPixmap, QPainter
import sys
import os
import time
import math
from math import cos, sin, sqrt, pi
import numpy as np
import configparser

from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

""" Vehicle Triangle for Plot """
def veh_triangle(veh):
#veh = np.array([20, 10, 45]) #east, north, heading (deg),
	vehBody = 5*np.array([[1.5, -1.5, -1.5, 1.5], [0, -0.8, 0.8, 0.0]])
	vehBody_ = 0*vehBody
	vehBody_[0] = vehBody[0]*cos(veh[2]*np.pi/180) - vehBody[1]*sin(veh[2]*np.pi/180)
	vehBody_[1] = vehBody[1]*cos(veh[2]*np.pi/180) + vehBody[0]*sin(veh[2]*np.pi/180)
	vehBody[0] = vehBody_[0] + veh[1] # body x, i.e. body[0] is veh north, i.e. veh[1]
	vehBody[1] = vehBody_[1] + veh[0] # body y, i.e. body[1] is veh east, i.e. veh[0]
	return vehBody[1], vehBody[0] # east, north

""" Lat Long to East North """
_e = 0.0818191908426
_R = 6378137

class LL_NE(object):
    def __init__(self, refLat=0, refLong=0):
        self.update(refLat, refLong)

    def update(self, refLat, refLong):
        self.RefLat = refLat
        self.RefLong = refLong
        self.EN_factors(refLat)

    def EN_factors(self, RefLat):
        self.eFactor = cos(RefLat*pi/180)*_R/sqrt(1-(sin(RefLat*pi/180)**2*_e**2))*pi/180
        self.nFactor = (1-_e**2)*_R/((1-(sin(RefLat*pi/180)**2*_e**2))*sqrt(1-(sin(RefLat*pi/180)**2*_e**2)))*pi/180

    def LL2NE(self, latitude, longitude):
        pos_east = (longitude - self.RefLong) * self.eFactor
        pos_north = (latitude - self.RefLat) * self.nFactor
        return pos_north, pos_east

    def NE2LL(self, pos_north, pos_east):
        longitude = (pos_east/self.eFactor) + self.RefLong 
        latitude = (pos_north/self.nFactor) + self.RefLat
        return latitude, longitude

""" East North to UV Image Cooridnates"""
class EN_UV(object):
    def __init__(self, ref1E=0, ref1N=0, ref1U=0, ref1V=0, ref2E=1, ref2N=1, ref2U=1, ref2V=1):
        self.update(ref1E, ref1N, ref1U, ref1V, ref2E, ref2N, ref2U, ref2V)

    def update(self, ref1E, ref1N, ref1U, ref1V, ref2E, ref2N, ref2U, ref2V):
        self.m2pix = math.hypot(ref1U-ref2U, ref1V-ref2V)/math.hypot(ref1E-ref2E, ref1N-ref2N)
        self.E1 = ref1E
        self.N1 = ref1N
        self.U1 = ref1U
        self.V1 = ref1V

    def EN2UV(self, east, north):
        u = (east - self.E1) * self.m2pix + self.U1
        v = -(north - self.N1) * self.m2pix + self.V1
        return u, v

""" Load Entire List of Paths """
def load_mapne(map_dir, refLat, refLong, pathlist):
	mapne = []
	for pathname in pathlist:
		fn = os.path.join(os.path.split(os.path.split(map_dir)[0])[0], 'paths', pathname+'.txt')
		path_lat, path_long = [], []
		llne = LL_NE()
		llne.update(refLat, refLong)
		with open(fn, 'r') as f:
			f.readline()
			lines = f.readlines()
			for line in lines:
				[lat, long] = [float(x) for x in line.strip('\n').split('\t')]
				north, east = llne.LL2NE(lat, long)
				mapne.append([north, east])
	return mapne

""" Read Map Metadata """
def map_metadata(map_dir):
	mapMetafile = os.path.join(map_dir, 'map_metadata.ini')
	mapParser = configparser.ConfigParser()
	mapParser.read(mapMetafile)
	path_files = mapParser['General']['Path_Files'][1:-1].replace(" ", "")
	originLat = float(mapParser['General']['Reference_Latitude'])
	originLong = float(mapParser['General']['Reference_Longitude'])
	caldata = {}
	caldata['ref1Lat'] = float(mapParser['Calibration']['Reference_1_Latitude'])
	caldata['ref1Long'] = float(mapParser['Calibration']['Reference_1_Longitude'])
	caldata['ref1U'] = int(mapParser['Calibration']['Reference_1_U'])
	caldata['ref1V'] = int(mapParser['Calibration']['Reference_1_V'])
	caldata['ref2Lat'] = float(mapParser['Calibration']['Reference_2_Latitude'])
	caldata['ref2Long'] = float(mapParser['Calibration']['Reference_2_Longitude'])
	caldata['ref2U'] = int(mapParser['Calibration']['Reference_2_U'])
	caldata['ref2V'] = int(mapParser['Calibration']['Reference_2_V'])
	return path_files, originLat, originLong, caldata

""" Map Window Object """
class MapWindow(QtWidgets.QMainWindow):

	def __init__(self, *args, **kwargs):
		super(MapWindow, self).__init__(*args, **kwargs)
		uic.loadUi('map.ui', self)
		self.setWindowTitle("Map")
		#self.setFixedSize(self.size())
		win_width = 1500
		win_height = 1000
		self.setGeometry(1000, 500, win_width, win_height)
		self.setFixedSize(win_width, win_height)
		self.map_frame.setGeometry(0, 0, win_width, win_height) 
		app_root = os.path.split(os.path.split(os.getcwd())[0])[0]
		map_dir = os.path.join(app_root, 'maps/map_T')
		self.init(map_dir) # initial loading of map
		self.show()  

	def init(self, map_dir):
		# map image
		mapImgfile = os.path.join(map_dir, 'map.jpg')
		self.pixmap = QPixmap(mapImgfile) # make pixmap
		# metadata
		path_files, originLat, originLong, caldata = map_metadata(map_dir)
		self.mapne = load_mapne(map_dir, originLat, originLong, path_files.split(','))
		# setup en to uv conversion
		self.llne = LL_NE()
		self.llne.update(originLat, originLong)
		n1, e1 = self.llne.LL2NE(caldata['ref1Lat'], caldata['ref1Long'])
		n2, e2 = self.llne.LL2NE(caldata['ref2Lat'], caldata['ref2Long'])
		self.enuv = EN_UV()
		self.enuv.update(e1,n1,caldata['ref1U'],caldata['ref1V'],e2,n2,caldata['ref2U'],caldata['ref2V'])
		# dimensions
		wmap = self.pixmap.size().width()
		hmap = self.pixmap.size().height()
		wlabel = self.map_frame.size().width()
		hlabel = self.map_frame.size().height()
		# scaling
		if wlabel/wmap < hlabel/hmap:
			self.pixmap = self.pixmap.scaledToWidth(wlabel)
			self.scale = wlabel/wmap
			#print("scaled to width:", self.scale)
		else:
			self.pixmap = self.pixmap.scaledToHeight(hlabel)
			self.scale = hlabel/hmap
			#print("scaled to height:", self.scale)
		# set pixmap
		self.pixmap0 = self.pixmap # initial pixmap
		self.setFixedSize(int(wmap*self.scale), int(hmap*self.scale)) # set size
		self.map_frame.setPixmap(self.pixmap) # set image
		# draw full path ne array
		self.draw_on_map(self.mapne, True, False) # data, persist, joint
		
		""" Start timer """
		#self.timer = QTimer(self)
		#self.timer.timeout.connect(self.draw_map)
		#self.timer.start(10)

	def draw_on_map(self, xyarr, persist=False, join=False, brushSize=3, brushColor='red'):
		self.pixmap = self.pixmap0.copy(0,0,self.pixmap0.size().width(), self.pixmap0.size().height()) 
		p = QPainter(self.pixmap)
		brush = QBrush()
		pen = QPen(brush, brushSize, Qt.SolidLine, Qt.RoundCap)
		pen.setColor(QColor(brushColor))
		p.setPen(pen)
		if join:
		# join points
			for n in range(len(xyarr)-1):
				x1 = xyarr[n][1] # north 1
				y1 = xyarr[n][0] # east 0
				x2 = xyarr[n+1][1] # north 1
				y2 = xyarr[n+1][0] # east 0
				u1, v1 = self.enuv.EN2UV(x1, y1)
				u1 = u1 * self.scale
				v1 = v1 * self.scale
				u2, v2 = self.enuv.EN2UV(x2, y2)
				u2 = u2 * self.scale
				v2 = v2 * self.scale
				p.drawLine(u1, v1, u2, v2)
		else:
			# just points, no join
			for n in range(len(xyarr)):
				x = xyarr[n][1] # north 1
				y = xyarr[n][0] # east 0
				u, v = self.enuv.EN2UV(x, y)
				u = u * self.scale
				v = v * self.scale
				p.drawPoint(u, v)
		p.end()
		self.map_frame.setPixmap(self.pixmap)
		if persist:
			self.pixmap0 = self.pixmap # initial pixmap

	def draw_veh(self, veh):
		north, east = self.llne.LL2NE(veh[0], veh[1]) # lat, long
		veh[0] = east
		veh[1] = north
		xyarr = []
		earr, narr = veh_triangle(veh)
		for i in range(0, len(earr)):
			xyarr.append([narr[i], earr[i]])
		self.draw_on_map(xyarr, brushColor='green', join=True)
	
def main():
	app = QtWidgets.QApplication(sys.argv)
	mainwindow = MapWindow()
	#mainwindow.show()
	sys.exit(app.exec_())

if __name__ == '__main__':         
	main()