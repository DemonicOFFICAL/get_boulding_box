#!/usr/bin/python3

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PIL import Image, ImageDraw, ImageFont
import sys
import os
import pandas as pd
import numpy as np

import matplotlib.pyplot as plt

class Box(object):
	def __init__(self, img, color, label=''):
		self.x = 0
		self.y = 0
		self.w = img.size[0]
		self.h = img.size[1]
		self.speed = 10
		self.color = tuple(color)
		self.border = 2
		self.img = img
		self.background_alpha = 63
		self.border_alpha = 255
		self.box_alpha = 0
		self.label = label
		self.font = ImageFont.truetype('Roboto.ttf', size=10)
		self.info = dict()
	
	def paint(self):
		img = self.img.copy()
		box_size = (self.w, self.h)
		border_size = (self.w + 2*self.border, self.h + 2*self.border)
		background_size = (
			self.img.size[0] + 2*self.border, 
			self.img.size[1] + 2*self.border
		)
		
		background_img = Image.new(
			'RGBA', 
			background_size, 
			self.color + (self.background_alpha,)
		)
		border_img = Image.new(
			'RGBA', 
			border_size, 
			self.color + (self.border_alpha,)
		)
		box_img = Image.new(
			'RGBA', 
			box_size, 
			self.color + (self.box_alpha,)
		)
		
		background_img.paste(border_img, (self.x, self.y))
		background_img.paste(
			box_img, 
			(self.x + self.border, self.y + self.border)
		)
		img.paste(
			background_img, 
			(-self.border, -self.border), 
			mask=background_img
		)
		
		return img
	
	def top_up(self):
		self.y -= self.speed
		self.h += self.speed
		if self.y < 0: self.y = 0
		if self.h > self.img.size[1]: self.h = self.img.size[1]
	
	def top_down(self):
		self.y += self.speed
		self.h -= self.speed
		if self.h < self.border: self.h = self.border
		if self.y > self.img.size[1]: self.y = self.img.size[1]
	
	def bottom_up(self):
		self.h -= self.speed
		if self.h < self.border: self.h = self.border
	
	def bottom_down(self):
		self.h += self.speed
		if self.h > self.img.size[1]: self.h = self.img.size[1]
	
	def left_left(self):
		self.x -= self.speed
		self.w += self.speed
		if self.x < 0: self.y = 0
		if self.w > self.img.size[0]: self.w = self.img.size[0]
	
	def left_right(self):
		self.x += self.speed
		self.w -= self.speed
		if self.w < self.border: self.w = self.border
		if self.x > self.img.size[1]: self.x = self.img.size[1]
	
	def right_left(self):
		self.w -= self.speed
		if self.w < self.border: self.w = self.border
	
	def right_right(self):
		self.w += self.speed
		if self.w > self.img.size[0]: self.w = self.img.size[0]
	
	def save(self):
		box_size = (self.w, self.h)
		border_size = (self.w + 2*self.border, self.h + 2*self.border+11)
		border_img = Image.new(
			'RGBA', 
			border_size, 
			self.color + (self.border_alpha,)
		)
		box_img = Image.new(
			'RGBA', 
			box_size, 
			self.color + (self.box_alpha,)
		)
		draw_text = ImageDraw.Draw(border_img)
		draw_text.text(
			(2, 0),
			self.label,
			font=self.font,
			fill=(255,255,255)
		)
		
		border_img.paste(box_img, (self.border, self.border+11))
		self.img.paste(
			border_img, 
			(self.x - self.border, self.y - self.border-11), 
			mask=border_img
		)
		box_center_x = round((self.x + self.w // 2) / self.img.size[0], 6)
		box_center_y = round((self.y + self.h // 2) / self.img.size[1], 6)
		box_w = round(self.w / self.img.size[0], 6)
		box_h = round(self.h / self.img.size[1], 6)
		self.info = {self.label:[box_center_x, box_center_y, box_w, box_w]}

class MainWindow(QScrollArea):
	def __init__(self, parent=None, img=None):
		super(MainWindow, self).__init__(parent)
		self.img = img
		self.k_zoom = 2
		self.zoom_img()
		self.menu_win = MenuWindow(parent_win=self)
		self.menu_win.show()
		self.menu_win.setFixedSize(self.menu_win.size())
		self.setMinimumSize(self.img.size[0]+2, self.img.size[1]+2)
		self.img_label = QLabel(self)
		self.img_label.setGeometry(0, 0, self.img.size[0], self.img.size[1])
		self.img_label.setPixmap(QPixmap(self.pil2qtim()))
		self.setWidget(self.img_label)
	
	def pil2qtim(self):
		data = self.img.tobytes('raw','RGB')
		qim = QImage(
			data, 
			self.img.size[0], 
			self.img.size[1], 
			QImage.Format_RGB888
		)
		return qim
	
	def zoom_img(self):
		self.img = self.img.resize(
			(self.k_zoom*self.img.size[0], self.k_zoom*self.img.size[1]), 
			Image.NEAREST
		)

class MyButton(QPushButton):
	def __init__(self, parent=None, text='', size=(100,25)):
		super(MyButton, self).__init__(parent)
		self.setText(text)
		self.setMinimumSize(size[0], size[1])
		self.setMaximumSize(size[0], size[1])
		self.setEnabled(False)

class MenuWindow(QWidget):
	def __init__(self, parent=None, parent_win=None):
		super(MenuWindow, self).__init__(parent)
		self.next_image  = MyButton(text='Next Image', size=(200,50))
		self.save_box    = MyButton(text='Save box', size=(100,50))
		self.new_box     = MyButton(text='New box', size=(100,50))
		self.speed_p     = MyButton(text='Speed\n+', size=(50,50))
		self.speed_m     = MyButton(text='Speed\n-', size=(50,50))
		self.zoom_p      = MyButton(text='Zoom\n+', size=(50,50))
		self.zoom_m      = MyButton(text='Zoom\n-', size=(50,50))
		self.top_up      = MyButton(text='/\\', size=(100,25))
		self.top_down    = MyButton(text='\\/', size=(100,25))
		self.bottom_up   = MyButton(text='/\\', size=(100,25))
		self.bottom_down = MyButton(text='\\/', size=(100,25))
		self.left_left   = MyButton(text='<', size=(25,100))
		self.left_right  = MyButton(text='>', size=(25,100))
		self.right_left  = MyButton(text='<', size=(25,100))
		self.right_right = MyButton(text='>', size=(25,100))
		self.grid_layout = QGridLayout(self)
		self.grid_layout.setVerticalSpacing(0)
		self.grid_layout.setHorizontalSpacing(0)
		self.grid_layout.addWidget(self.speed_p,     0, 0, 2, 2)
		self.grid_layout.addWidget(self.top_up,      0, 2, 1, 1)
		self.grid_layout.addWidget(self.speed_m,     0, 3, 2, 2)
		self.grid_layout.addWidget(self.top_down,    1, 2, 1, 1)
		self.grid_layout.addWidget(self.left_left,   2, 0, 2, 1)
		self.grid_layout.addWidget(self.left_right,  2, 1, 2, 1)
		self.grid_layout.addWidget(self.new_box,     2, 2, 1, 1)
		self.grid_layout.addWidget(self.right_left,  2, 3, 2, 1)
		self.grid_layout.addWidget(self.right_right, 2, 4, 2, 1)
		self.grid_layout.addWidget(self.save_box,    3, 2, 1, 1)
		self.grid_layout.addWidget(self.zoom_p,      4, 0, 2, 2)
		self.grid_layout.addWidget(self.bottom_up,   4, 2, 1, 1)
		self.grid_layout.addWidget(self.zoom_m,      4, 3, 2, 2)
		self.grid_layout.addWidget(self.bottom_down, 5, 2, 1, 1)
		self.grid_layout.addWidget(self.next_image,  6, 0, 1, 5)
		self.new_box.setEnabled(True)
		self.new_box.clicked.connect(self.new_box_button)
		self.parent_win = parent_win
		self.img = self.parent_win.img
		self.color = None
		self.label = None
		self.box_list = []
	
	def new_box_button(self):
		self.modal_window = ChoiseClassModalWindow(parent_win=self)
		self.modal_window.show()
		self.modal_window.setFixedSize(self.modal_window.size())
	
	def new_box_func(self):
		self.box = Box(self.img, self.color, label = self.label)
		self.speed_p.setEnabled(True)
		self.top_up.setEnabled(True)
		self.speed_m.setEnabled(True)
		self.top_down.setEnabled(True)
		self.left_left.setEnabled(True)
		self.left_right.setEnabled(True)
		self.right_left.setEnabled(True)
		self.right_right.setEnabled(True)
		self.save_box.setEnabled(True)
		self.right_right.setEnabled(True)
		self.bottom_up.setEnabled(True)
		self.bottom_down.setEnabled(True)
		self.next_image.setEnabled(True)

		self.top_up.clicked.connect(self.box.top_up)
		self.top_down.clicked.connect(self.box.top_down)
		self.left_left.clicked.connect(self.box.left_left)
		self.left_right.clicked.connect(self.box.left_right)
		self.right_left.clicked.connect(self.box.right_left)
		self.right_right.clicked.connect(self.box.right_right)
		self.bottom_up.clicked.connect(self.box.bottom_up)
		self.bottom_down.clicked.connect(self.box.bottom_down)
		self.save_box.clicked.connect(self.box_save)

		self.top_up.clicked.connect(self.paint_box)
		self.top_down.clicked.connect(self.paint_box)
		self.left_left.clicked.connect(self.paint_box)
		self.left_right.clicked.connect(self.paint_box)
		self.right_left.clicked.connect(self.paint_box)
		self.right_right.clicked.connect(self.paint_box)
		self.bottom_up.clicked.connect(self.paint_box)
		self.bottom_down.clicked.connect(self.paint_box)
		self.save_box.clicked.connect(self.paint_box)
		
	
	def paint_box(self):
		self.parent_win.img = self.box.paint()
		self.parent_win.img_label.setPixmap(
			QPixmap(self.parent_win.pil2qtim())
		)
	
	def box_save(self):
		self.box.save()
		self.box_list.append(self.box.info)
		print(self.box_list, end='\n\n')

class ChoiseClassModalWindow(QDialog):
	def __init__(self, parent=None, parent_win=None):
		super(ChoiseClassModalWindow, self).__init__(parent)
		self.settings_file = 'classes_color.json'
		self.read_classes()
		self.parent_win = parent_win
		self.setWindowModality(Qt.WindowModal)
		self.setAttribute(Qt.WA_DeleteOnClose, True)
		self.grid_layout = QGridLayout(self)
		self.grid_layout.setVerticalSpacing(0)
		self.grid_layout.setHorizontalSpacing(0)
		self.ok_button = QPushButton('Ok')
		self.comboBox = QComboBox(self)
		self.comboBox.addItem('Выбери класс')
		for key in self.settings.keys():
			self.comboBox.addItem(key)
		self.grid_layout.addWidget(self.comboBox,  0, 0, 1, 1)
		self.grid_layout.addWidget(self.ok_button, 1, 0, 1, 1)
		self.comboBox.activated.connect(self.choise_class)
		self.ok_button.clicked.connect(self.close)
	
	def read_classes(self):
		with open(self.settings_file, 'r', encoding='utf-8') as f:
			self.settings = eval(f.read())
	
	def choise_class(self):
		self.label = self.comboBox.currentText()
		if self.label != 'Выбери класс':
			self.color = self.settings[self.label]
		else:
			print('Не выбран класс')
			sys.exit(app.exec_())
	
	def close(self):
		self.parent_win.color = self.color
		self.parent_win.label = self.label
		self.parent_win.new_box_func()
		super(ChoiseClassModalWindow, self).close()


if __name__ == '__main__':
	font = ImageFont.truetype('Roboto.ttf', size=18)
	n = Image.open('0.jpg')
	app = QApplication(sys.argv)
	ex = MainWindow(img=n)
	ex.show()
	sys.exit(app.exec_())
