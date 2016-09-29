#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pickle

class DataBase:
	'''
	Database is a dictionary that is stored and read from a file.
	'''
	def __init__(self, fileName):
		try:
			with open(fileName, "rb") as f:
				self.data = pickle.load(f)
				self.fileName = fileName
		except:
			self.op = dict()

	def load(self):
		''' Try to load the data sotred in *fileName*.'''
		with open(self.fileName, 'rb') as fh:
			obj = pickle.load(fh)
		self.data = obj

	def save(self):
		''' Saves the data to a file '''
		with open(self.fileName, 'wb') as fh:
			pickle.dump(self.data, fh, pickle.HIGHEST_PROTOCOL)