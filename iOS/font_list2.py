
from reportlab.lib.fontfinder import FontFinder
from yks.utils import getChildDirectories
from yks.utils import getAbsolutePath
from yks.utils import _b2s

_fontfinder = None

def getBadFiles():
	return _fontfinder._badFiles

def getFontList():
	global _fontfinder
	#iPhoneのフォントパスの一覧
	FPR = '/System/Library/Fonts'

	dirs = getChildDirectories(FPR)
	#DLしたフォントのパス
	_fontfinder = FontFinder(dirs)
	p = getAbsolutePath('~/Documents/fonts/ipag00303')
	_fontfinder.addDirectory(p)
		
	p = getAbsolutePath('~/Documents/fonts/ipam00303')
	_fontfinder.addDirectory(p)

	#利用可能なフォントを検索
	_fontfinder.search()

	#print(_fontfinder.getFamilyNames())
	for f in _fontfinder._fonts:
		familyName = _b2s(f.familyName)
		fileName = f.fileName
		fullName = _b2s(f.fullName)
		if fullName:
			atr = 'name:{}, familt:{}, file:{}'.format(fullName, familyName, fileName)
			#print(atr)
			yield {'name':fullName, 'family':familyName, 'file':fileName}
		else:
			yield {'name':None, 'family':familyName, 'file':fileName}

if __name__ == '__main__':
	for fi in getFontList():
		print(fi)
#[EOF]
