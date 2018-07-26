# -*- coding:utf-8 -*-
import os
from pathlib import Path
'''
'''
def _b2s(v):
	'''
	bytes型をstr型に変換する。
	'''
	return v.decode('utf-8').strip() if isinstance(v,bytes) else v

def _s2b(v):
	'''
	str型をbytes型に変換する。
	'''
	return v.encode('utf-8') if isinstance(v,str) else v

def _s2s(v):
	'''
	
	'''
	r = []
	for x in v:
		r.append(_b2s(x))
	return set(r)

def _db2ds(d):
	'''
	辞書型に設定されたキー及び値でbytes型をstr型に変換する。
	'''
	r = {}
	for k,v in d.items():
		r[_b2s(k)] = _b2s(v)
	return r

def _ds2db(d):
	'''
	辞書型に設定されたキー及び値でstr型をbytes型に変換する。
	'''
	r = {}
	for k,v in d.items():
		r[_s2b(k)] = _s2b(v)
	return r

def _v2s(v):
	if isinstance(v, str):
		return v
	elif isinstance(v, bytes):
		return v.decode('utf-8').strip()
	elif isinstance(v, tuple):
		r = []
		for x in v:
			r.append(_v2s(x))
		return tuple(r)
	elif isinstance(v, dict):
		return _db2ds(v)
	elif isinstance(v, set):
		return _s2s(v)
	else:
		return v

def decoToStr(func):
	'''
	デコレータ：引数のbytes型をstr型に変換する。
	クラスメソッド用
	'''
	def wrapper(self, *args):
		p = []
		for arg in args:
			if isinstance(arg, dict):
				p.append(_db2ds(arg))
			else:
				p.append(_b2s(arg))
		return func(self, *p)
	return wrapper

def decoToBytes(func):
	'''
	デコレータ：引数のstr型をbytes型に変換する。
	クラスメソッド用
	'''
	def wrapper(*args):
		p = []
		for arg in args:
			if isinstance(arg, dict):
				p.append(_ds2db(arg))
			elif isinstance(arg, list):
				p.append([_s2b(x) for x in arg])
			else:
				p.append(_s2b(arg))
		return func(*p)
	return wrapper

def decoToStrF(func):
	'''
	デコレータ：引数のbytes型をstr型に変換する。
	関数用
	'''
	def wrapper(*args):
		p = []
		for arg in args:
			if isinstance(arg, dict):
				p.append(_db2ds(arg))
			else:
				p.append(_b2s(arg))
		return func(*p)
	return wrapper

def decoRetToStr(func):
	'''
	デコレータ：メソッド及び関数の戻り値でbytes型をstr型に変換する。
	'''
	def wrapper(self, *args):
		a, *b = [func(self, *args)]
		if a:
			return _v2s(a)
		else:
			return None
	return wrapper

def isiOs():
	import sys
	return sys.platform == 'ios'

def getChildDirectories(path_root):
	fpl = []
	for w1 in os.listdir(path_root):
		w2 = os.path.join(path_root, w1)
		if os.path.isdir(w2): fpl.append(w2)
	#print(fpl)
	return fpl

def getAbsolutePath(path):
	if path.startswith('~'):
		h = Path().home()
		return str(h) + path[1:]
	else:
		return str(Path(path).absolute())

#[EOF]
