# -*- coding: utf-8 -*-
import os.path as osPath
import re
import xml.sax
from abc import ABCMeta, abstractmethod

class ORMapperException(Exception):
	def __init__(self, message):
		self.message = message
'''
	DaoXml ファイルの読込を行う
'''
class DaoReader(xml.sax.handler.ContentHandler):
	def __init__(self):
		self.id_list = {}
		self._curIdTag = None
		self._curSubTag = None
		self._trace = False
	def startElement(self, tag, attr):
		if self._trace:
			print('>>> start', tag, attr.getNames())
		if 'id' in attr.getNames():
			idName = attr.getValue('id')
			self._curIdTag = {'type': tag, 'source':[]}
			self.id_list[idName] = self._curIdTag
		elif self._curIdTag:
			subTag = {'tag': tag, 'attributes':attr,
			 'source':[]}
			self._curSubTag = subTag
			self._curIdTag['source'].append(subTag)
	def endElement(self, tag):
		if self._trace:
			print('<<< end', tag)
		if self._curSubTag:
			self._curSubTag = None
		elif self._curIdTag:
			self._curIdTag = None
	def characters(self, content):
		if self._trace:
			print('content', content)
		str = content.strip()
		if len(str) == 0:
			return
		if self._curIdTag and not self._curSubTag:
			self._curIdTag['source'].append(str)
		elif self._curSubTag:
			self._curSubTag['source'].append(str)

class IfTestChecker():
	def isNone(self, value):
		return True if value == None else False
	def isNotNone(self, value):
		return not self.isNone(value)
	def isTrue(self, value):
		return True if value == True else False

class ORMapper(metaclass=ABCMeta):
	@abstractmethod
	def daoAccess(self, argv):
		pass

	def __init__(self, ifChecker = None):
		self.colNameReg = re.compile(r'#\{[\w]*\}')
		self._ifFncReg = re.compile(r'.+\(.*\)')	#ゆるいかも
		self._ifChecker = ifChecker if ifChecker else IfTestChecker()
	def __getattr__(self, name):
		#print("[%s]"%name)
		if name in self._tagInfo:
			self.executeDaoName = name
			#print(name)
			return self.daoAccess
		else:
			raise ORMapperException('no such method (%s)' % name)

	def createDao(self, filePath):
		''' パスの存在を確認 '''
		if osPath.exists(filePath) == False:
			raise ORMapperException('file not found (%s)' % filePath)
		''' ファイルの存在を確認 '''
		if osPath.isfile(filePath) == False:
			raise ORMapperException('%s is not a file' % filePath)
		''' 読込み '''
		try:
			reader = DaoReader()
			xml.sax.parse(filePath, reader)
			self._tagInfo = {}
			for idTagName in reader.id_list.keys():
				self._tagInfo[idTagName] = reader.id_list[idTagName]
			return self
		except Exception as exp:
			raise ORMapperException('read error (%s)' % exp)

	def _replaceIfTest(self, testStr, sqlParm):
		work = testStr
		match = re.findall(self.colNameReg, work)
		#print(work, match)
		if match:
			for kw1 in match:
				kw2 = kw1[2:-1] # '#{xxx}' -> xxx
				if kw2 in sqlParm:
					val = sqlParm[kw2]
					if isinstance(val, str):
						val = "'%s'" % val
					else:
						val = str(val)
				else:
					val = 'None'
					#print('key', kw1, 'not found')
				work = work.replace(kw1, val)
		return work

	def _execIfTest(self, testStr, sqlParm):
		text = self._replaceIfTest(testStr, sqlParm)
		if re.match(self._ifFncReg, text):
			text = 'self._ifChecker.' + text
		return eval(text)

	def prepareSQL(self, strings, sqlParm):
		ret = []
		for wk in strings:
			if isinstance(wk, str):
				ret.append(wk)
			elif wk['tag'] == 'if':
				ifTest = wk['attributes'].get('test')
				if self._execIfTest(ifTest, sqlParm):
					for ln in wk['source']:
						ret.append(ln)
			else:
				print(wk)
		return ret

	'''
	#{xxx}を:xxxに置換する。
	named placeholders (named style) を使った sql
	を実行するための編集
	'''
	def replaceNamedStyle(self, sql, entity):
		#print('[sql]', sql)
		work = '\n'.join(sql)
		match = re.findall(self.colNameReg, work)
		if match:
			#print(match)
			for kw1 in match:
				kw1 = kw1.strip()
				kw2 = kw1[2:-1] # '#{xxx}' -> xxx
				if kw2 in entity:
					val = ':' + kw2
					work = work.replace(kw1, val)
		return work

	def _prepareSQL4UnitTest(self, executeDaoName, entity):
		''' assert で確認のため改行を削除 '''
		source = self._tagInfo[executeDaoName]['source']
		sql = ' '.join(source)
		''' 注入する値のキーワードを検索 '''
		match = re.findall(self.colNameReg, sql)
		if match:
			for kw1 in match:
				kw1 = kw1.strip()
				kw2 = kw1[2:-1] # '#{xxx}' -> xxx
				val = entity[kw2]
				if isinstance(val, int):
					val = str(val)
				else:
					val = "'%s'" % val
				sql = sql.replace(kw1, val)
		return sql

#[EOF]
