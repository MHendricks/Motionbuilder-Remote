# A Gui interface allowing the binary illiterate to figure out the ip address the Arduino has been assigned.

import os
import re
from PySide.QtCore import QFile, QMetaObject, QSignalMapper, Slot, QRegExp
from PySide.QtGui import QDialog, QPushButton, QRegExpValidator
from PySide.QtUiTools import QUiLoader

class IPHelper(QDialog):
	def __init__(self, parent=None):
		super(IPHelper, self).__init__(parent)
		f = QFile(os.path.join(os.path.split(__file__)[0], 'iphelper.ui'))
		loadUi(f, self)
		f.close()
		self.ipAddress = None
		
		# create validators
		validator = QRegExpValidator(QRegExp('\d{,3}'))
		self.uiFirstTetTXT.setValidator(validator)
		self.uiSecondTetTXT.setValidator(validator)
		self.uiThirdTetTXT.setValidator(validator)
		self.uiFourthTetTXT.setValidator(validator)
		
		# build a map of the buttons
		self.buttons = [None]*16
		self.signalMapper = QSignalMapper(self)
		self.signalMapper.mapped.connect(self.tetMap)
		for button in self.findChildren(QPushButton):
			match = re.findall(r'^uiTrellis(\d{,2})BTN$', button.objectName())
			if match:
				i = int(match[0])
				self.buttons[i] = button
				if i >= 12:
					self.signalMapper.setMapping(button, i)
					button.clicked.connect(self.signalMapper.map)
		self.tetMap(12)

	@Slot()
	def accept(self):
		self.ipAddress = '{}.{}.{}.{}'.format(self.uiFirstTetTXT.text(), self.uiSecondTetTXT.text(), self.uiThirdTetTXT.text(), self.uiFourthTetTXT.text())
		super(IPHelper, self).accept()

	@Slot(int)
	def tetMap(self, index):
		button = self.buttons[index]
		if not button.isChecked():
			return
		for i in range(12, 16):
			b = self.buttons[i]
			if b != button:
				b.setChecked(False)
		# update the buttons to match the current value of the text
		for edit in (self.uiFirstTetTXT, self.uiSecondTetTXT, self.uiThirdTetTXT, self.uiFourthTetTXT):
			edit.setProperty('active', False)
		if index == 12:
			val = int(self.uiFourthTetTXT.text())
			self.uiFourthTetTXT.setProperty('active', True)
		elif index == 13:
			val = int(self.uiThirdTetTXT.text())
			self.uiThirdTetTXT.setProperty('active', True)
		elif index == 14:
			val = int(self.uiSecondTetTXT.text())
			self.uiSecondTetTXT.setProperty('active', True)
		elif index == 15:
			val = int(self.uiFirstTetTXT.text())
			self.uiFirstTetTXT.setProperty('active', True)
		for i in range(8):
			b = self.buttons[i]
			b.blockSignals(True)
			b.setChecked(2**i & val)
			b.blockSignals(False)
		# force a refresh of the styleSheet
		self.setStyleSheet(self.styleSheet())

	@Slot()
	def buttonPressed(self):
		total = 0
		for i in range(8):
			if self.buttons[i].isChecked():
				total += 2**i
		total = unicode(total)
		if self.uiTrellis12BTN.isChecked():
			self.uiFourthTetTXT.setText(total)
		elif self.uiTrellis13BTN.isChecked():
			self.uiThirdTetTXT.setText(total)
		elif self.uiTrellis14BTN.isChecked():
			self.uiSecondTetTXT.setText(total)
		elif self.uiTrellis15BTN.isChecked():
			self.uiFirstTetTXT.setText(total)


# Code to load a ui file like using PyQt4
class MyQUiLoader(QUiLoader):
	def __init__(self, baseinstance):
		super(MyQUiLoader, self).__init__()
		self.baseinstance = baseinstance

	def createWidget(self, className, parent=None, name=""):
		widget = super(MyQUiLoader, self).createWidget(className, parent, name)
		if parent is None:
			return self.baseinstance
		else:
			setattr(self.baseinstance, name, widget)
			return widget

def loadUi(uifile, baseinstance=None):
	loader = MyQUiLoader(baseinstance)
	ui = loader.load(uifile)
	QMetaObject.connectSlotsByName(ui)
	return ui
