import streamlit as st
import pandas as pd

# SQLiteを実施
import sqlite3

# 地図の表示に使用
import folium
from streamlit_folium import st_folium

set_madori_list = {
    "2K" : "2K",
    "2DK" : "2DK",
    "2LDK" : "2LDK"
}

set_erea_list = {
    "目黒区" : "megro",
    "渋谷区" : "shibuya",
}

set_display_number_list = {
    "10件" : 10,
    "20件" : 20,
    "30件" : 30
}

# 保存したdbの読み込んで確認
dbname = "Chintai_test.db"  # テスト中
tablename = "meguro_2K2DK2LDK"


#<条件設定> キーワード・ソースのデフォルト値を設定
if 'set_madori' not in st.session_state:
    st.session_state.set_madori = "2LDK"
    st.session_state.set_erea = "目黒区"

st.title("賃貸検索アプリ")
st.session_state.set_madori = st.sidebar.multiselect("間取りを選択", set_madori_list.keys())
st.session_state.set_erea = st.sidebar.multiselect("エリアを選択", set_erea_list.keys())


value = st.sidebar.slider("価格範囲を指定してください[万円]", 0.0, 50.0, (20.0,30.0))

st.write(st.session_state.set_madori[0])
st.write(st.session_state.set_erea[0])
st.write(set_erea_list[st.session_state.set_erea[0]])

st.write(str(value[0])+"万円～"+str(value[1])+"万円")

# 検索条件からクエリを作成する


# DBは区毎に作成し、各DBに対して指定したクエリを投げる関数を作成
# データベースに接続
conn = sqlite3.connect(dbname)  # 渡した名前でデータベースを作成（すでに存在していれば、それに接続する）

# SQLクエリを使用してデータの読み込んで、DataFrameへ変換
query = "SELECT * FROM " + tablename
df_read = pd.read_sql_query(query, conn)

# 接続を閉じる（必須）
conn.close()

# 複数選択可能なselectbox形式
select_list = [False, False, False, False, False, False, False, False, False, False]
for i in range(10):
    select_list[i] = st.checkbox(str(i))

st.write(df_read.head(10))
selected_one = st.radio("選択してください", df_read.head(10).index, horizontal=True)


logitude = df_read.head(10)["緯度"].mean()
latitude = df_read.head(10)["経度"].mean()

center_location = [logitude, latitude]

map = folium.Map(location=center_location, zoom_start=13)   # 全部の検索結果が入るサイズにしたいが、実スケールとの対応が分からない。ディスプレイの解像度などにも依存しそう。。。

for i in range(10):
    logitude = df_read.iloc[i]["緯度"]
    latitude = df_read.iloc[i]["経度"]
    name = df_read.iloc[i]["名前"]
    
    folium.Marker(
        location = [logitude, latitude],
        popup = name,
        icon = folium.Icon(color="blue"),
        ).add_to(map)


# st.data_editorで直接チェックボックスを編集させてもよいかも。。。
# for i in range(len(select_list)):
#     if select_list[i] :
#         logitude = df_read.iloc[i]["緯度"]
#         latitude = df_read.iloc[i]["経度"]
#         name = df_read.iloc[i]["名前"]

#         folium.Marker(
#             location = [logitude, latitude],
#             popup = name,
#             icon = folium.Icon(color="red"),
#             ).add_to(map)
    i = selected_one
    logitude = df_read.iloc[i]["緯度"]
    latitude = df_read.iloc[i]["経度"]
    name = df_read.iloc[i]["名前"]

    folium.Marker(
        location = [logitude, latitude],
        popup = name,
        icon = folium.Icon(color="red"),
        ).add_to(map)


st_folium(map, width=700, height=500)
