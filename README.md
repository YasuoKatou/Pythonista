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
