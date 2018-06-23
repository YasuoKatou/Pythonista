import sqlite3
from yks.or_mapper import ORMapper as ORM
import xml.etree.ElementTree as xmlParser
from pathlib import Path

class Sqlite3Mapper(ORM):
	def __init__(self, conn=None):
		ORM.__init__(self)
		if conn:
			self.conn = conn
	def connect(self, dbName, isolation_level=None):
		self.conn = sqlite3.connect(dbName, isolation_level=isolation_level)
	def create_tables(self, ddlPath):
		cr = self.conn.cursor()
		xml = xmlParser.parse(ddlPath)
		xmlRoot = xml.getroot()
		for child in xmlRoot:
			#print(child.text)
			cr.execute(child.text)
		#print('Pass')
		self.conn.commit()
	def close(self):
		self.conn.close()
	def commit(self):
		self.conn.commit()
	def rollback(self):
		self.conn.rollback()
	def getResult(self, cr):
		recList = []
		while True:
			row = cr.fetchone()
			if row:
				rec = {}
				for key in row.keys():
					rec[key] = row[key]
				recList.append(rec)
			else:
				break
		if len(recList) == 1:
			if len(rec) == 1:
				return list(rec.values())[0]
			else:
				return rec
		else:
			return recList
	def daoAccess(self, *argv):
		argc = len(argv)
		#print('start '+self.executeDaoName)
		xmlInfo = self._tagInfo[self.executeDaoName]
		if argc == 1:
			sqlParm = argv[0]
		else:
			sqlParm = {}
		text = super().prepareSQL(xmlInfo['source'], sqlParm)
		sql = super().replaceNamedStyle(text, sqlParm)
		#print(sql)
		''' SQLを実行する '''
		self.conn.row_factory = sqlite3.Row
		cr = self.conn.cursor()
		cr.execute(sql, sqlParm)
		#print('row count:'+str(cr.rowcount))
		''' 実行結果を編集 '''
		ret = False
		dmlType = xmlInfo['type'].upper()
		if dmlType == 'SELECT':
			#ret = cr.fetchone()
			#ret = cr.fetchall()
			ret = self.getResult(cr)
		else:		#insert, update, delete
			ret = cr.rowcount
			#print('rowcount:', ret)
		#self.conn.commit()		2018/04/13 del
		#if ret:							2018/04/13 chg(S)
		#	return ret
		return ret					 #2018/04/13 chg(E)
	def executeSql(self, sql):
		cr = self.conn.cursor()
		cr.execute(sql)
	@staticmethod
	def dbSize(dbName):
		p = Path(dbName)
		return p.stat().st_size


#[EOF]
