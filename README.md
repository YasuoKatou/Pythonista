# Pythonista

## yks.utils
Pyrhon2,3でstrの扱いが変わったので、bytesからstrへ変換またはその逆を行う関数をまとめた。

## yks.Sqlite3Mapper, yks.or_mapper
簡易ORMです。SQLite3で使用しています。

### テーブルの作成

#### XML形式でCREATE TABLEを作成
```
<ddl>
  <table>
    ceate table xxx (
       col_XA,
         :
        PRIMARY KEY( ... )
     )
  </table>
  <table>
    ceate table yyy (
       col_YA,
         :
        PRIMARY KEY( ... )
     )
  </table>
</ddl>
```

#### プログラムより、DDLを実行（１回だけ実行）
```
  dao = Sqlite3Mapper()
  dao.connect('./sample.db')
  dao.create_table(./sample_ddl.xml)
  dao.close()
```


### データアクセス

#### XML形式でINSERT,UPDATE,DELETE,SELECTを作成
```
<dao>
  <insert id="insert_append">
    INSERT INTO TABLE_A (
      col_a,
      col_b,
      col_c
    ) values (
      #{a_val},
      #{b_val},
      #{c_val},
     }
  </insert>
</dao>
```

#### プログラムより、DMLを実行
```
vals = {'a_val': x, 'b_val': y, 'c_val': z}
dao = Sqlite3Mapper(con=False)
dao.connect()
n = dao.insert_append(vals)
dao.close()
```
## yks.TableUpdater（SQLite3用）
XMLで定義したテーブル及びインデックス定義とDBの内容を比較し、テーブルの追加／削除、カラムの追加／変更を行う（テーブル／カラムの変更は行わない）。また、本クラスを実行した場合、処理の開始前にバックアップを作成する。

## ReportLabでPDF出力(中断)
  結論から言うとReportLabでFontの取扱いに満足できないので中断する。ReportLabは、True Type Fontに対応しているが、iPhone標準（/System/Library/Fonts配下）のフォントで日本語が使えるFontがない。

  ノートPCだったら、普通にフリーフォントをＤＬしても良かったが、ポリシー（？）に反するためやめておく。

  ちなみに、
  DL（ipag00303.zipやipam00303.zip）したフォントファイルを解凍後、ReportLabでPDF出力はできた。

  今回作成したPythonスクリプト
  ・iOS/font_list2.py
    利用可能なフォントの一覧を作成
  ・iOS/font_list_pdf4.py
   利用可能なフォントの一覧を使ってPDF出力する。
  実行結果サンプル
  ・iOS/fonts_list4.pdf
    １ページ目にReportLabのサンプルを実行
    ２ページ目以降でフォントのサンプルを出力
    DLしたフォント（2種類）も出力しています(No16, 91)
    Appendix A にReportLabで使用できないフォントファイルの一覧を出力（bad files）
    Appendix B にPDF出力時にエラーになったフォントファイルの一覧を出力（error fits）
