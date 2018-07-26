from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
import reportlab.lib.pagesizes as PSF
from reportlab.lib.units import cm as CM
from reportlab.lib.fontfinder import FontFinder
#from font_list2 import getFontList
import font_list2 as FLM
from pathlib import Path

'''
フォントのパスが豆腐状態になるので、パスは
『HeiseiMin-W3』フォントを使って出力する。
'''

def p1_fonts(canvas):
  from reportlab.lib.units import inch
  text = "Now is the time for all good men to...こんにちは、世界！"
  x = 1.8*inch
  y = 2.7*inch
  for font in canvas.getAvailableFonts():
    canvas.setFont(font, 10)
    canvas.drawString(x,y,text)
    canvas.setFont("Helvetica", 10)
    canvas.drawRightString(x-10,y, font+":")
    y = y-13

_errFonts = []
def check_ttfont(fn, fp):
	global _errFonts
	try:
		ft = TTFont(fn, fp)
		pdfmetrics.registerFont(ft)
		return ft
	except:
		_errFonts.append(fp)
		#print('can not use : ' + fp)
		return None

pdfFilename = 'fonts_list4.pdf'
pdfFile = canvas.Canvas(pdfFilename)
#pdfFile.saveState()

#用紙サイズをA4に設定
page_size = 'A4'
pdfFile.setPageSize(page_size)
wh = getattr(PSF, page_size)

#用紙の向きを縦長に設定
#page_orientation = 'portrait'
#用紙の向きを横長に設定
page_orientation = 'landscape'
wh = getattr(PSF, page_orientation)(wh)

pdfFile.setPageSize(wh)
pdfFile.setAuthor('Yasuo Kato')
pdfFile.setTitle('font list for iOS')
pdfFile.setSubject('true type fonts')

#demo #1
p1_fonts(pdfFile)
pdfFile.showPage()		#改ページ

#共通で使うフォントを登録
#cmff = 'HeiseiMin-W3'
cmff = 'HeiseiKakuGo-W5'
cmf = UnicodeCIDFont(cmff)
pdfmetrics.registerFont(cmf)

left = 1 * CM
top = wh[1] - 1.5 * CM
bottom = 2 * CM

y = top
y_step = 1 * CM

nnm = 0
fno = 0
for fi in FLM.getFontList():
	fName = fi['name']
	if fName is None:
		nnm += 1
		fName = 'no name {}'.format(nnm)
	fFile = fi['file']
	ft = check_ttfont(fName, fFile)
	if not ft:
		continue
	pif = Path(fFile)
	dtl = 'ファイル : {}, パス : {}'.format(pif.name, pif.parent)
	pdfFile.setFont(cmff, 8)
	pdfFile.drawString(left, y, dtl)

	fno += 1
	dtl = 'No.{} name : {}, family : {}, japanese : こんにちは、世界！'.format(fno, fName, fi['family'])
	pdfFile.setFont(fName, 11)
	pdfFile.drawString(left+0.5*CM, y-0.4*CM, dtl)

	y -= y_step
	if y < bottom:
		# next page
		pdfFile.showPage()
		y = top

#bad files
bfs = FLM.getBadFiles()
if len(bfs) > 0:
	pdfFile.showPage()
	y = top
	pdfFile.setFont(cmff, 10)
	dtl = 'Appendix A : bad files'
	pdfFile.drawString(left, y, dtl)
	y -= 0.5 * CM
	pdfFile.setFont(cmff, 8)
	for p in bfs:
		pdfFile.drawString(left+0.5*CM, y, p)
		y -= 0.4 * CM

#todo error fonts
if len(_errFonts) > 0:
	pdfFile.showPage()
	y = top
	pdfFile.setFont(cmff, 10)
	dtl = 'Appendix B : error fonts'
	pdfFile.drawString(left, y, dtl)
	y -= 0.5 * CM
	pdfFile.setFont(cmff, 8)
	for p in _errFonts:
		pdfFile.drawString(left+0.5*CM, y, p)
		y -= 0.4 * CM

		if y < bottom:
			# next page
			pdfFile.showPage()
			pdfFile.setFont(cmff, 8)
			y = top

pdfFile.showPage()
pdfFile.save()

#[EOF]
