#! /usr/bin/env python3

import logging
logger = logging.getLogger('PDFinfo')
debug, info, warning, error, panic = logger.debug, logger.info, logger.warning, logger.error, logger.critical

from collections import OrderedDict
import os, os.path
import re
import string
import subprocess

import dateutil.parser

def parse_timestamp(*args, **kwargs):
	try:
		return dateutil.parser.parse(*args, **kwargs)
	except:
		return args[0]

class PDFinfo:
	def __init__(self, filename):
		p = subprocess.Popen(['pdfinfo', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		text, stderr = p.communicate()
		self.filename, self.text, self.errors = filename, text, []
		if stderr:
			lines = stderr.decode().split('\n')
			error( "{}: {} errors from pdfinfo:".format(filename, len(lines)) )
			last = ''
			for line in lines:
				if line and (line != last):
					self.errors.append(line)
					error(line)
					last = line
	def items(self, pattern=re.compile('\n?(.*)[:]\s+')):
		parsed = pattern.sub('\x1E\\1\x1F', self.text.decode())
		for lineno, line in enumerate(parsed.split('\x1E')):
			if line:
				k, v = line.split('\x1F', 1)
				
				if k in ['CreationDate', 'ModDate']:
					if v:
						yield k, parse_timestamp(v)
				elif v in ['yes', 'no']:
					yield k, (v == 'yes')
				elif v.upper() in [ 'NONE' ]:
					yield k, None
				elif k in ['File size']:
					yield k, int(re.sub(' bytes$', '', v, re.IGNORECASE))
				else:
					try:
						yield k, int(v)
					except ValueError:
						yield k, v
					
	def as_dict(self):
		return OrderedDict(self.items())
	def __str__(self):
		return '\n'.join('{}:\t{}'.format(k, v) for k, v in self.items())
	def getTitle(self, default=''):
		t = default
		if not t:
			_, basename = os.path.split(self.filename)
			t, _ = os.path.splitext(basename)
			t = string.capwords(t.replace('_', ' '))
		d = self.as_dict()
		if 'Title' in d:
			t = d['Title'].strip()
		return t
	def getYear(self):
		d = self.as_dict()
		if 'CreationDate' in d:
			return d['CreationDate'].year
		if 'ModDate' in d:
			return d['ModDate'].year
		return 0
