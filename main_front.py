import streamlit as st
import pandas as pd

# SQLiteを実施
import sqlite3

# 地図の表示に使用
import folium
from streamlit_folium import st_folium

import os

set_madori_list = {
    "2K" : "2K",
    "2DK" : "2DK",
    "2LDK" : "2LDK",
}

set_erea_list = {
    "世田谷区" : "setagaya",
    "目黒区" : "meguro",
    "品川" : "shinagawa",
    "港区" : "minato",
}

set_display_number_list = {
    "10件" : 10,
    "20件" : 20,
    "30件" : 30
}

# 保存したdbの読み込んで確認
dbname = "Chintai.db"


def read_db(dbname: str, erea_list: list) -> pd.DataFrame:
    """選択したエリアについてDBから読み込む

    Args:
        dbname (str): 現状は"Chintai.db"で固定
        set_erea_list (str): st.multiselectの戻り値をそのままいれればよい

    Returns:
        pd.DataFrame: 読み込んだDataFrameをすべて結合したもの
    """

    # 現在のファイルのディレクトリを取得
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # データベースファイルへのパスを構築
    db_path = os.path.join(current_dir, dbname)
    
    # データベースに接続
    conn = sqlite3.connect(db_path)  # 渡した名前でデータベースを作成（すでに存在していれば、それに接続する）
    df_read = pd.DataFrame()

    # エリアごとにtable分けているので順番に読み込む
    for i in range(len(erea_list)):
        tablename = set_erea_list[erea_list[i]] + "_2K2DK2LDK"
        # SQLクエリを使用してデータの読み込んで、DataFrameへ変換
        query = "SELECT * FROM " + tablename
        _df = pd.read_sql_query(query, conn)
        
        df_read = pd.concat([df_read, _df], ignore_index=True)

    # 接続を閉じる（必須）
    conn.close()
    
    return df_read

def filter_df(df: pd.DataFrame, set_madori_value: list, rent_lower_and_upper_limits: list) -> pd.DataFrame:
    """指定した条件を満たすものを抽出する

    Args:
        df_read (pd.DataFrame): 読み込んだ全データ
        set_madori (list): 選択された"間取り"のvalueのリスト
        value (list): "賃料"が[下限, 上限]に入るものを抽出する

    Returns:
        pd.DataFrame: 抽出結果のdf（インデックスを振りなおしたもの）
    """

    df = df[df["間取り"].isin(set_madori_value)]
    df = df[df["賃料"].between(rent_lower_and_upper_limits[0], rent_lower_and_upper_limits[1])]
    
    # 抽出したデータをソートして、indexが０から始まるように付け直す
    # この際に元のdfを変更したくないのでcopy()を作成する
    df = df.sort_values("賃料", ascending=True)
    df_copy = df.copy().reset_index(drop=True)

    return df_copy

# 表示する項目、数などの指定
def display_df(filtered_df: pd.DataFrame, display_number: int, display_page: int) -> pd.DataFrame:
    """条件で抽出した後のデータから、更に、表示するデータのみを抽出する

    Args:
        filtered_df (pd.DataFrame): 条件抽出後のデータでindex_resetしたものを想定
        display_number (int): 一度に表示する物件の数
        display_page (int): 表示するページ

    Returns:
        pd.DataFrame: 指定した１ページ分に相当するデータ
    """
   
    # 一度に表示する件数、表示するページをもとに、対応する番号のデータを抽出
    df = filtered_df[(display_page-1) * display_number : display_page * display_number]
    
    return df

def display_map(filtered_df: pd.DataFrame, displayed_df: pd.DataFrame, selected_one: int) -> None:
    """foliumを使って地図を表示する

    Args:
        filtered_df (pd.DataFrame): 条件で抽出済みdf(インデックスを振りなおしたもの)
        displayed_df (pd.DataFrame): 一覧として表示するdf
        selected_one (int): 強調したいデータのindex(filtered_dfに対するindex)
    
    Notes:
        一覧として表示した物件すべて地図上にプロットする。
        その上で選択した物件についてはマーカーの色を変える。
    """

    # 地図の中心は、表示する物件の中央付近にしたい
    logitude = displayed_df["緯度"].mean()
    latitude = displayed_df["経度"].mean()
    
    center_location = [logitude, latitude]

    # 全部の検索結果が入るサイズにしたいが、実スケールとの対応が分からない。ディスプレイの解像度などにも依存しそう。。
    # 自分の環境でちょうど良さそうなzoom_start=12としておく
    map = folium.Map(location=center_location, zoom_start=12)

    # 一覧表示の物件をすべて地図上にプロットする
    for i in displayed_df.index:
        # 参照するindexはfilterd_dfに対応している
        logitude = filtered_df.iloc[i]["緯度"]  
        latitude = filtered_df.iloc[i]["経度"]
        name = filtered_df.iloc[i]["名前"]
        
        folium.Marker(
            location = [logitude, latitude],
            popup = name,
            icon = folium.Icon(color="blue"),
            ).add_to(map)

    # 選択した物件のみマーカーを変える
    i = selected_one
    logitude = filtered_df.iloc[i]["緯度"]
    latitude = filtered_df.iloc[i]["経度"]
    name = filtered_df.iloc[i]["名前"]

    folium.Marker(
        location = [logitude, latitude],
        popup = name,
        icon = folium.Icon(color="red"),
        ).add_to(map)
    
    # 地図の表示
    st_folium(map, width=700, height=500)    
    
    return

#<条件設定> キーワード・ソースのデフォルト値を設定
if 'set_madori' not in st.session_state:
    st.session_state.set_madori = "2LDK"
    st.session_state.set_erea = "目黒区"
    st.session_state.rent_lower_and_upper_limits = (20.0, 30.0)
    st.session_state.display_number = "10件"
    st.session_state.filtered_df = pd.DataFrame()
    st.session_state.search_button_is_not_pushed = True  # 検索ボタンを一度でも押せばFalseになる

st.title("賃貸検索アプリ")
st.session_state.set_madori = st.sidebar.multiselect("間取りを選択", set_madori_list.keys(), st.session_state.set_madori)
st.session_state.set_erea = st.sidebar.multiselect("エリアを選択", set_erea_list.keys(), st.session_state.set_erea)
st.session_state.rent_lower_and_upper_limits = st.sidebar.slider("価格範囲を指定してください[万円]", 0.0, 50.0, st.session_state.rent_lower_and_upper_limits)

# keyのリストをvalueのリストに変換する
set_madori_value = []
for i in range(len(st.session_state.set_madori)):
    set_madori_value.append(set_madori_list[st.session_state.set_madori[i]])


# DBの読み込み
df_read = read_db(dbname, st.session_state.set_erea)

# 検索ボタンを押したときのみ
if st.sidebar.button("検索", type="primary"):
    # 指定した条件のデータを抽出する
    st.session_state.filtered_df = filter_df(df_read, set_madori_value, st.session_state.rent_lower_and_upper_limits)
    
    st.session_state.search_button_is_not_pushed = False


# 検索ボタンが押されるまではこちらの処理 
if st.session_state.search_button_is_not_pushed :
    st.write("条件を指定した上で検索ボタンを押してください")
    
# 検索ボタンが押された時のみ（filterd_dfにデータが入っている時のみ）実行する   
else :
    # 検索結果の表示
    st.sidebar.write("条件に合う物件は" + str(len(st.session_state.filtered_df)) + "件です")
    
    # 検索結果が０件の時の例外処理
    if len(st.session_state.filtered_df) == 0 :
        st.write("条件を変えて再度検索をしてください")
    
    # 検索結果が１件以上ある時の通常処理
    else :
        # 表示する条件を指定する
        # 一度に表示する物件の数を指定
        st.session_state.display_number_key = st.sidebar.radio("一度に表示する件数",set_display_number_list.keys())
        st.session_state.display_number = set_display_number_list[st.session_state.display_number_key]

        # 表示するページ番号の指定
        max_page = len(st.session_state.filtered_df) // st.session_state.display_number + 1

        # st.sliderでは最小値＜最大値でないとエラーがでるため、max_page==1の時はsliderを使わない
        if max_page == 1 :
            st.sidebar.write("全" + str(len(st.session_state.filtered_df)) + "件を表示します")

        else :
            st.session_state.display_page = st.sidebar.slider("表示するページ", 1, max_page, 1)
            
        # 一度に表示する分のデータを抽出
        displayed_df = display_df(st.session_state.filtered_df, st.session_state.display_number ,st.session_state.display_page )

        # 一覧表示
        st.write(displayed_df)

        # 指定した物件について詳細な情報を表示する
        selected_one = st.radio("詳しく知りたい物件の番号を選択してください", displayed_df.index, horizontal=True)

        # 直接リンクを作成
        st.write(st.session_state.filtered_df.iloc[selected_one]["URL"])

        # foliumを使って地図を表示
        display_map(st.session_state.filtered_df, displayed_df, selected_one)



