import logging
import xml.etree.ElementTree as xmlParser
import sqlite3
from Sqlite3Mapper import Sqlite3Mapper as DAO
import copy
import datetime
import re
import shutil
from pathlib import Path

class TableUpdater():
  def readDdl(self, path):
    '''
    DDLファイル(XML形式)の読込み
    '''
    try:
      xml = xmlParser.parse(path)
      xmlRoot = xml.getroot()
    except Exception as exp:
      print('DDLの読込み異常', exp)

    dmlInfo = {'table': [], 'index': []}
    for child in xmlRoot:
      wk = self._oneLine(child.text)
      if wk.startswith('create table'):
        dmlInfo['table'].append(wk)
      elif wk.startswith('create index'):
        dmlInfo['index'].append(wk)
      else:
        logging.info('ignored :', wk)
    return dmlInfo

  def _oneLine(self, buf):
    '''
    複数行となる文字列を１行にする。
    先頭と末尾の空白も削除する。
    '''
    wk = buf.split('\n')
    return ''.join([x.strip() for x in wk])

  def seqAndStrip(self, buf, seqKey):
    return [n.strip() for n in buf.split(seqKey)]

  def getValue(self, typeList, typ):
    '''
    辞書から値を取得する
    辞書に指定のキーが存在しない時、Noneを戻す
    '''
    if typ in typeList:
      return typeList[typ]
    return None

  def hasNotNull(self, buf):
    '''
    NOT NULL制約の定義を検索する
    OUT : NOT NULL制約を見つけた場合、True
    '''
    for idx in range(0, len(buf)):
      if buf[idx] == 'not' and buf[idx+1] == 'null':
        return True
    return False

  def hasDefault(self, buf):
    '''
    default オプションを検索する
    OUT : defultオプションを見つけた場合、辞書
      {'value': 値}を戻す
      値に半角スペースを含まない事を前提とする
    '''
    for idx in range(0, len(buf)):
      if buf[idx] == 'default':
        return {'value': buf[idx + 1]}
    return None

  def now_datetime_str(self):
    '''
    日時を文字列で取得する
    '''
    n = datetime.datetime.now()
    return n.strftime('%Y%m%d_%H%M%S')

class SqliteTableUpdater(TableUpdater):
  #型名対応一覧(XML定義 : Sqliteの型)
  _CTYPE = {'char':'text', 'clob':'text', 'text':'text',
  'int':'integer','integer':'integer',
  'floa':'real', 'real':'real',
  'blob':'none', 'none':'none',
  'numeric':'numeric'}

  def __init__(self, ddl_path, db_path):
    self._backup(db_path)
    xml = super().readDdl(ddl_path)
    self._analizeXml(xml)
    self._analizeDb(db_path)
    self.db_path = db_path

  def _backup(self, db_path):
    '''
    DBファイルのバックアップを行う
    db_path + '.' + 日時(yyyymmdd_hhmmss)
    '''
    if not Path(db_path).exists():
      logging.info('no backup. no such file : ' + db_path)
      return
    #バックアップのファイル名を決定
    n = super().now_datetime_str()
    n = '{}.{}'.format(db_path, n)

    #ファイルコピー
    shutil.copy2(db_path, n)
    logging.info('backup to ' + n)

  def _analizeXml(self, xml):
    '''
    DDLファイルの解析
    '''
    self._xml_table_info = {}
    for wk in xml['table']:
      nm, info = self._analizeTable(wk)
      self._xml_table_info[nm] = info
    self._xml_index_info = {}
    for wk in xml['index']:
      nm, info = self._analizeIndex(wk) 
      self._xml_index_info[nm] = info

  def _analizeTable(self, buf):
    '''
    create table を解析する
    型名は、Sqlite標準の型名に変換する
    case 1)
      IN : 'colA char'
      OUT : {'name': 'colA', 'type': 'text'}
    case 2)
      IN : 'name text not null'
      OUT : {'name': 'name', 'type': 'text',
            'not_null':True}
    case 3)
      IN : 'col_def text default '---''
      OUT : {}
    '''
    p = buf.find('(')
    #テーブル名
    tn = buf[:p].split(' ')[2].strip()
    #カラム情報
    wk = buf[p+1:]
    wk = wk[:wk.rfind(')')]
    #カラム定義とprimary key定義を分離する
    cols, pk = self._separatePK(wk)
    td = {'source': buf,
      'colomn': self._analizeColumn(cols),
      'PK':self._getPKcols(pk)}
    return tn, td
  def _separatePK(self, buf):
    '''
    列定義の最後にある『primary key』定義を分離する
    また、列定義はカンマで分割する
    注意：列定義にカンマを含まない事
    IN : 
      create table (
        colA int,
        colB text,
        colC real,
        primary key (colA, colB)
      )
    OUT :
      (1) 列定義一覧
        ['colA int', 'colB text', 'colC real']
      (2) 'primary key (colA, colB)'
    '''
    wk = buf.lower()
    p = wk.find('primary key')
    if p < 0:
      return buf, ''  #PK定義なし
    return buf[:p].split(','), buf[p:]
  def _analizeColumn(self, cols):
    '''
    列定義を解析する
    '''
    colList = []
    for col in cols:
      col = col.strip()
      wk = super().seqAndStrip(col, ' ')
      if wk[0] != '':
        inf = {'name':wk[0].lower(),
        'type': super().getValue(self._CTYPE, wk[1].lower()),
        'not_null': super().hasNotNull(wk),
        'default': super().hasDefault(wk)}
        colList.append(inf)
    return colList
  def _getPKcols(self, pk):
    '''
    『primary key』に続く小括弧内の文字列を抽出し、
    カンマで分割する。
    IN : primary key (colA, colB, colC)
    OUT : ['colA', 'colB', 'colC']
    '''
    wk = pk.lower()
    if wk.find('primary key') < 0:
      return None
    p1 = pk.find('(')
    p2 = pk.rfind(')')
    wk = pk[p1+1:p2]
    return super().seqAndStrip(wk, ',')

  def _analizeIndex(self, buf):
    '''
    create index を解析する
    IN : 'create index (colA1, colA2)'
    OUT : ['colA1', 'colA2']
    '''
    p1 = buf.find('(')
    #インデックス名
    nm = buf[:p1].split(' ')[2].strip()
    p2 = buf.rfind(')')
    wk = buf[p1+1:p2]
    return nm, {'columns': super().seqAndStrip(wk, ','), 'source': buf}

  def _analizeDb(self, path):
    '''
    DBより、テーブル及びインデックスの情報を取得
    '''
    self.dao = DAO()
    id = 'getTblInfo'
    source = ['select * from sqlite_master',]
    self.dao.addQuery('select', id, source)
    self.dao.connect(path)
    self.path = path
    r = self.dao.getTblInfo()
    self.dao.close()

    self._db_index_info = {}
    self._db_table_info = {}
    if r:
      if not isinstance(r, list):
        r = [r,]
    for ddl in r:
      ddl_type = ddl['type']
      ddl_sql  = ddl['sql'].replace('\n', '')
      if ddl_type == 'table':
        nm, info = self._analizeTable(ddl_sql)
        self._db_table_info[nm] = info
      elif ddl_type == 'index':
        nm, info = self._analizeIndex(ddl_sql)
        self._db_index_info[nm] = info

  def execute(self):
    self.dao.connect(self.path)
    cr = self.dao.conn.cursor()
    self._execTable(cr)
    self._execIndex(cr)
    self.dao.close()

  def _execTable(self, cr):
    def _editColDef(d):
      s = ' ' + d['type']
      if d['not_null']:
        s += ' not null'
      if d['default']:
        s += ' {}'.format(d['default'])
      return s

    for xml_key in self._xml_table_info.keys():
      if xml_key not in self._db_table_info:
        #XMLにあって、DBに存在しない場合、テーブルを作成する
        info = self._xml_table_info[xml_key]
        #テーブルの作成
        logging.info('create table : ' + xml_key)
        ddl = info['source']
        logging.debug('\tddl : ' + ddl)
        cr.execute(ddl)
      else:
        #テーブルの更新をチェック
        upd_cols = False
        for md, xc, dc in self._checkTableColumn(xml_key):
          if md == 'AC':
            #カラムの追加
            msg = 'add column : {} in {}'.format(xc['name'], xml_key)
          elif md == 'DC':
            #カラムの削除
            msg = 'drop column : {} in {}'.format(dc['name'], xml_key)
          elif md == 'MC':
            #カラムの変更
            msg = 'modify column : {} in {}'.format(xc['name'], xml_key)
          else:
            logging.error('_checkTableColumn mode error : ' + md)
            continue
          logging.info(msg)
          upd_cols = True
        if upd_cols:
          #テーブル構造の変更
          self._updateTable(cr, xml_key)

    for db_key in self._db_table_info.keys():
      if db_key not in self._xml_table_info:
        #DBにあってXMLに存在しない場合、テーブルを削除する
        self._dropNotUseTbl(cr, db_key)

  def _updateTable(self, cr, tn):
    '''
    ワークテーブルに全レコードをコピーして、対象テーブルを再構築後、レコードを戻す
    '''
    #ワークテーブルの作成
    logging.debug('\n--- step1 : create work table')
    self._createWorkTable(cr, tn)
    #ワークテーブルに対象テーブルのレコードをコピー
    logging.debug('\n--- step2 : copy record to worktable')
    cpr = self._copy2WkTbl(cr, tn)
    #対象テーブルをdrop
    logging.debug('\n--- step3 : drop target table')
    self._dropCurTbl(cr, tn)
    #xmlより対象テーブルをcreate
    logging.debug('\n--- step4 : create target table')
    self._createUpdTbl(cr, tn)
    #ワークテーブルのレコードを対象テーブルにコピー
    logging.debug('\n--- step5 : copy record to target table')
    self._copy2TgtTbl(cr, tn, cpr)
    #ワークテーブルをdrop
    logging.debug('\n--- step6 : drop worktable')
    self._dropWkTbl(cr)

  def _createWorkTable(self, cr, refNm):
    '''
    step1:ワークテーブルを作成する
    IN : cr - カーソル
         refNm - 対象のテーブル名
         self._db_table_info
    OUT : self._wkTbNm - ワークテーブル名
          refNm + '_' + 日時(yyyymmdd_hhmmss)
    '''
    #ワークテーブル名を決定する
    n = super().now_datetime_str()
    self._wkTbNm = '{}_{}'.format(refNm, n)

    #create文を編集
    ddl = self._db_table_info[refNm]['source']
    ddl = ddl.replace(refNm, self._wkTbNm, 1)
    logging.debug('create work table : ' + ddl)

    #create文を実行
    cr.execute(ddl)
    logging.debug('create table(' + self._wkTbNm + ') success !!')

  def _copy2WkTbl(self, cr, tn):
    '''
    step2:対象テーブルの全レコードをワークテーブルにコピーする
    '''
    #select-insert文を編集
    cns = [cdf['name'] for cdf in self._db_table_info[tn]['colomn']]
    cns = ','.join(cns)
    dml = 'insert into ' + self._wkTbNm + ' (' + cns + ') select ' + cns + ' from ' + tn
    logging.debug(dml)

    #copy record
    cr.execute(dml)
    n = cr.rowcount
    logging.debug('copied to worktable ({}, {} records)'.format(self._wkTbNm, n))
    return n

  def _dropCurTbl(self, cr, tn):
    '''
    step3:更新対象のテーブルを削除
    '''
    #drop文の編集
    ddl = 'drop table ' + tn

    #drop文の実行
    cr.execute(ddl)
    logging.debug('dropped target table (' + tn + '). success !!')

  def _createUpdTbl(self, cr, tn):
    '''
    step4:更新対象のテーブルを作成
    '''
    ddl = self._xml_table_info[tn]['source']
    logging.debug(ddl)

    cr.execute(ddl)
    logging.debug('create table(' + tn + ') success !!')

  def _copy2TgtTbl(self, cr, tn, cpr):
    '''
    step5:ワークテーブルを全レコードを更新対象テーブルにコピーする
    ワークテーブルと更新対象テーブルの両テーブルの同名の列を対象にする
    '''
    #対象テーブルの列名一覧
    clx = [x['name'] for x in self._xml_table_info[tn]['colomn']]
    #ワークテーブルの列名一覧
    cld = [d['name'] for d in self._db_table_info[tn]['colomn']]
    #列名が一致する一覧
    cpc = ','.join([e for e in clx if e in cld])

    #テーブルコピーのDMLを編集
    dml = 'insert into ' + tn + ' (' + cpc + ') select ' + cpc + ' from ' + self._wkTbNm
    logging.debug(dml)

    #DMLを実行
    cr.execute(dml)
    n = cr.rowcount
    logging.debug('copy table ({}) success !!\nrecord : {} -> {}'.format(tn, cpr, n))

  def _dropWkTbl(self, cr):
    '''
    step6:ワークテーブルを削除する
    '''
    #drop文の編集
    ddl = 'drop table ' + self._wkTbNm

    #drop文を実行
    cr.execute(ddl)
    logging.debug('droped worktable (' + self._wkTbNm + '). success !!')

  def _dropNotUseTbl(self, cr, tn):
    '''
    未使用のテーブルを削除する
    '''
        #drop文の編集
    ddl = 'drop table ' + tn

    #drop文を実行
    cr.execute(ddl)
    logging.debug('droped table (' + tn + '). success !!')

  def _checkTableColumn(self, tn):
    '''
    テーブル列の差異をチェックする
    IN : tn - テーブル名
    OUT : mode(*1), xml定義(*2), db定義(*2)
      *1:'AC' 列追加、'DC' 列削除、'MC' 列変更
      *2:name属性以外の差分のみ
    '''
    def _copyColomnDef(d):
      return copy.deepcopy(d[tn]['colomn'])
    def _diffColumn(xml, db):
      def _delEqual(an):
        if xml[an] == db[an]:
          del xml[an]
          del db[an]
      _delEqual('type')
      _delEqual('not_null')
      _delEqual('default')
    def _getDef(l, n):
      r = [x for x in l if x['name'] == n]
      return None if len(r) == 0 else r[0]

    xt = _copyColomnDef(self._xml_table_info)
    dt = _copyColomnDef(self._db_table_info)
    for xc in xt:
      dc = _getDef(dt, xc['name'])
      if dc is not None:
        #xmlにもdbにも存在する
        _diffColumn(xc, dc)
        if len(xc) == 1 and len(dc) == 1:
          continue
        else:
          #差分あり(=列の変更が必要)
          yield 'MC', xc, dc
      else:
        #dbに存在しない(=列追加)
        yield 'AC', xc, None
    for dc in dt:
      xc = _getDef(xt, dc['name'])
      if xc is None:
        #xmlに存在しない(=列削除)
        yield 'DC', None, dc

  def _execIndex(self, cr):
    for xml_key in self._xml_index_info.keys():
      if xml_key not in self._db_index_info:
        #XMLにあって、DBに存在しない場合、インデックスを作成する
        self._createIndex(cr, xml_key)
      else:
        #インデックスの更新をチェック
        if self._checkIdxDiff(xml_key):
          #更新なしはreindexする
          #self._reindex(cr, xml_key)
          #テーブルを再構築した時、インデックスが消失するので、reindexできない
          self._dropIndex(cr, xml_key)
          self._createIndex(cr, xml_key)
        else:
        	#更新ありは、再作成する
          self._dropIndex(cr, xml_key)
          self._createIndex(cr, xml_key)
    for db_key in self._db_index_info.keys():
      if db_key not in self._xml_index_info:
        #DBにあってXMLに存在しない場合、インデックスをを削除する
        self._dropIndex(cr, db_key)

  def _createIndex(self, cr, inm):
    '''
    インデックスを作成する
    cr - カーソル
    inm - インデックス名
    '''
    ddl = self._xml_index_info[inm]['source']
    logging.debug(ddl)

    cr.execute(ddl)
    logging.debug('create index(' + inm + ') success !!')

  def _checkIdxDiff(self, inm):
    '''
    インデックスの差異をチェックする
    inm - インデックス名
    '''
    return self._xml_index_info[inm]['columns'] == self._db_index_info[inm]['columns']

  def _reindex(self, cr, inm):
    '''
    reindexを行う
    '''
    ddl = 'reindex ' + inm
    logging.debug('start reindex : ' + ddl)

    cr.execute(ddl)
    logging.debug('reindex (' + inm + '). success !!')

  def _dropIndex(self, cr, inm):
    '''
    インデックスをdropする
    cr - カーソル
    inm - インデックス名
    '''
    ddl = 'drop index ' + inm
    try:
      cr.execute(ddl)
      logging.debug('dropped target index (' + inm + '). success !!')
    except:
      logging.debug('non index (' + inm + ')')

if __name__ == "__main__":
  #_LOG_LEVEL = logging.DEBUG
  _LOG_LEVEL = logging.INFO
  logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=_LOG_LEVEL)

  #todo テスト用DDL定義ファイルのパス
  xp = './test01/DDL.xml'
  dp = './test01/xxxxDB'
  tu = SqliteTableUpdater(xp, dp)
  tu.execute()
  pass

#[EOF]
