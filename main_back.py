import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
from tqdm import tqdm   #for文の進捗を確認
#セットアップ
tqdm.pandas()  

# 地図表示するために緯度、経度情報を取得
import requests
import urllib

# SQLiteを実施
import sqlite3



def scraping_suumo(load_url: str) -> pd.DataFrame:
    """suumoページからスクレイピング

    Args:
        load_url (str): エリア、間取りなどを検索した後で「建物ごとに表示」のurl

    Returns:
        pd.DataFrame:コラム名は "名前", "住所", "最寄り駅１","最寄り駅２","最寄り駅３", "築年数", "建物全体の階数", "階数", "賃料", "管理費", "敷金", "礼金", "間取り", "面積", "URL" 
    """

    res = requests.get(load_url)
    res.encoding = "utf-8"
    soup = BeautifulSoup(res.text, "html.parser")
    
    # ページ数の取得
    pages = soup.find("ol", class_="pagination-parts")
    num_of_pages = int(pages.find_all("li")[-1].text)
    
    
    # データフレーム作成
    rental_property_datas = pd.DataFrame(columns=["名前", "住所", "最寄り駅１","最寄り駅２","最寄り駅３", "築年数", "建物全体の階数", "階数", "賃料", "管理費", "敷金", "礼金", "間取り", "面積", "URL" ])
    
    print("suumo scraping")
    for p in tqdm(range(num_of_pages)):
    # for p in tqdm(range(2)):  # テストの際に使用

        # topのページは"&page=1"を付けても開ける
        page_url = load_url + "&page=" + str(p+1)
        res = requests.get(page_url)
        res.encoding = "utf-8"
        soup = BeautifulSoup(res.text, "html.parser")
        
        # サーバー負荷を避けるため1s遅延
        time.sleep(1)

        # 「建物ごとに表示」ページから物件毎の情報を取得
        cassetitems = soup.find_all("div", class_="cassetteitem")

        for i in range(len(cassetitems)):
            
            # 上の部分（建物情報）
            details = cassetitems[i].find_all("div", class_="cassetteitem-detail")
            
            for ii in range(len(details)):
                name = details[ii].find("div", class_="cassetteitem_content-title").text
                address = details[ii].find("li", class_="cassetteitem_detail-col1").text
                _stations = details[ii].find_all("div", class_="cassetteitem_detail-text")
                station1 = _stations[0].text
                station2 = _stations[1].text
                station3 = _stations[2].text
                _col3 = details[ii].find_all("li", class_="cassetteitem_detail-col3")
                building_age = _col3[0].find_all("div")[0].text
                number_of_floors = _col3[0].find_all("div")[1].text
                
                # 下の部分（部屋の情報）
                items = cassetitems[i].find("div", class_="cassetteitem-item")
                tbodys = items.find_all("tbody")
                for iii in range(len(tbodys)):
                    _tds = tbodys[iii].find_all("td")
                    floor = _tds[2].text.replace('\r','').replace('\n','').replace('\t','')
                    rent = _tds[3].find("span", class_="cassetteitem_other-emphasis ui-text--bold").text
                    maintenance_fee = _tds[3].find("span", class_="cassetteitem_price cassetteitem_price--administration").text
                    deposit = _tds[4].find("span", class_="cassetteitem_price cassetteitem_price--deposit").text
                    gratuity = _tds[4].find("span", class_="cassetteitem_price cassetteitem_price--gratuity").text
                    layout = _tds[5].find("span", class_="cassetteitem_madori").text
                    area = _tds[5].find("span", class_="cassetteitem_menseki").text
                    url = "https://suumo.jp" + _tds[8].find("a").get("href")
                    
                    # DataFrameにまとめた後、rental_property_datasへ追加する
                    _d = pd.DataFrame()
                    _d["名前"] = [name]
                    _d["住所"] = [address]
                    _d["最寄り駅１"] = [station1]
                    _d["最寄り駅２"] = [station2]
                    _d["最寄り駅３"] = [station3]
                    _d["築年数"] = [building_age]
                    _d["建物全体の階数"] = [number_of_floors]
                    _d["階数"] = [floor]
                    _d["賃料"] = [rent]
                    _d["管理費"] = [maintenance_fee]
                    _d["敷金"] = [deposit]
                    _d["礼金"] = [gratuity]
                    _d["間取り"] = [layout]
                    _d["面積"] = [area]
                    _d["URL"] = [url]

                    rental_property_datas = pd.concat([rental_property_datas, _d], ignore_index=True)

    return rental_property_datas
    

# クレンジングに使用した処理を関数化
def replace_B_to_minus(floor: str) -> int:
    """地下を示すBを"-"に置き換える（"階数"で使用）

    Args:
        floor (str): X階数の"X"だけを渡す_

    Returns:
        int: 特に、BX -> -X で返す
    """
    if "B" in floor :
        floor = int(floor.replace("B","-"))
    else :
        floor = int(floor)

    return floor

def replace_man_yen_to_int(money: str) -> float:
    """X.X万円をfloatに変換する

    Args:
        money (str): X.X万円

    Returns:
        float: X.X (万円)
    """
    if "-" in money :
        money = float(0.0)
    else:
        money = float(money.replace("万円", ""))

    return money

def replace_yen_to_int(money: str) -> float:
    """X000円を0.X万円に変換する

    Args:
        money (str): X000円

    Returns:
        float: 0.X (万円)
    """
    if "-" in money :
        money = float(0)
    else :
        money = float(money.replace("円", "")) * 0.0001

    return money

def cleansing_suumo(rental_property_datas: pd.DataFrame) -> pd.DataFrame:
    """suumoからスクレイピング後のデータをクレンジングと重複削除

    Args:
        rental_property_datas (pd.DataFrame): スクレイピング後のDataFrameを直接渡せばよい

    Returns:
        pd.DataFrame: 
    """
    
    # if文で作成してたものをラムダ式に整理

    rental_property_datas["築年数"] = rental_property_datas["築年数"].apply(lambda x : int(0) if x=="新築" else int(x.replace("築","").replace("年","")))

    # "建物全体の階数を"最小と最大のコラムに直す
    rental_property_datas["建物階数_最小"] = rental_property_datas["建物全体の階数"].apply(lambda x : int(x.split("地上")[0].replace("地下","-")) if "地下" in x else int(0))
    rental_property_datas["建物階数_最大"] = rental_property_datas["建物全体の階数"].apply(lambda x : int(x.split("地上")[1].replace("階建","")) if "地下" in x else int(x.replace("階建","")))

    # "階数"を"最小と最大のコラムに直す
    rental_property_datas["階数_最小"] = rental_property_datas["階数"].apply(lambda x : replace_B_to_minus(x.split("-")[0]) if "-" in x else replace_B_to_minus(x.replace("階", "")))
    rental_property_datas["階数_最大"] = rental_property_datas["階数"].apply(lambda x : replace_B_to_minus(x.split("-")[1].replace("階", "")) if "-" in x else replace_B_to_minus(x.replace("階", "")))

    rental_property_datas["賃料"] = rental_property_datas["賃料"].apply(lambda x: replace_man_yen_to_int(x))
    rental_property_datas["敷金"] = rental_property_datas["敷金"].apply(lambda x : replace_man_yen_to_int(x))
    rental_property_datas["礼金"] = rental_property_datas["礼金"].apply(lambda x : replace_man_yen_to_int(x))

    rental_property_datas["管理費"] = rental_property_datas["管理費"].apply(lambda x : replace_yen_to_int(x))

    rental_property_datas["面積"] = rental_property_datas["面積"].apply(lambda x : float(x.replace("m2","")))
    # rental_property_datas["間取り"] = rental_property_datas["間取り"]  # そのままでよい
    
    
    # 重複判定の実施
    df = rental_property_datas
    df_cleansing= df[df[["住所","賃料","管理費","間取り","建物階数_最小","建物階数_最大","階数_最小","階数_最大","面積","敷金","礼金"]].duplicated()]
    
    return df_cleansing


def get_logitude_and_latitude(address:str)  :
    """住所から緯度、経度を取得

    Args:
        address (str): _description_
        float (_type_): _description_
    """
    makeUrl = "https://msearch.gsi.go.jp/address-search/AddressSearch?q="
    s_quote = urllib.parse.quote(address)
    response = requests.get(makeUrl + s_quote)
    logitude = response.json()[0]["geometry"]["coordinates"][1]  # 緯度 ※順番注意！
    latitude = response.json()[0]["geometry"]["coordinates"][0]  # 経度
    
    # サーバー負荷を避けるため0.2s遅延
    time.sleep(0.2)
    
    return (logitude, latitude)

def add_logitude_and_latitude(df_cleansing: pd.DataFrame) -> pd.DataFrame :
    """クレンジング後のDataFrameに緯度、経度のコラムを追加

    Args:
        df_cleansing (pd.DataFrame): _description_

    Returns:
        pd.DataFrame: _description_
    """

    # DBへ格納するためにはlistはダメ
    # apply()の引数として、result_type="expand"が使えなかったので、apply(pd.Series)で分割     
    print("add loagitude and latitude")
    _df = df_cleansing["住所"].progress_apply(lambda x : get_logitude_and_latitude(x)).apply(pd.Series) 
    _df.columns = ["緯度", "経度"]
    df_cleansing.loc[:, ["緯度", "経度"]] = _df

    # SettingWithCopyWarning（ビューへ操作なのか、コピーへの操作なのか不明瞭）と言われるのでやめた
    # df_cleansing[["緯度", "経度"]] = df_cleansing["住所"].progress_apply(lambda x : get_logitude_and_latitude(x)).apply(pd.Series) 
    
    return df_cleansing
    
def save_to_db(dbname: str, tablename:str, df_cleansing: pd.DataFrame) -> None :
    """dfをDBへ保存する

    Args:
        dbname (str): _description_
        tablename (str): _description_
        df_cleansing (pd.DataFrame): _description_
    """

    # データベースに接続
    conn = sqlite3.connect(dbname)  # 渡した名前でデータベースを作成（すでに存在していれば、それに接続する）

    # DataFrameはsqliteに保存するメソッドが存在している
    df_cleansing.to_sql(tablename, conn, if_exists='replace',  index=False)

    # 接続を閉じる（必須）
    conn.close()

    return 

def add_DB_list(df_DB_list: pd.DataFrame, load_url: str, dbname: str, tablename: str) -> pd.DataFrame :
    """スクレイピング先と作成するDBをdf_DB_listへ追加する

    Args:
        df_DB_list (pd.DataFrame): _description_
        load_url (str): _description_
        dbname (str): _description_
        tablename (str): _description_

    Returns:
        pd.DataFrame: _description_
    """
    _df = pd.DataFrame()
    _df["load_url"] = [load_url]
    _df["dbname"] = [dbname]
    _df["tablename"] = [tablename]
    
    df_DB_list = pd.concat([df_DB_list, _df], ignore_index=True)
    
    return df_DB_list


def main():
    
    # スクレイピング先と作成するDBの一覧
    df_DB_list = pd.DataFrame()
    
    # 目黒区、2K, 2DK, 2LDK （建物種別　マンション、アパート）
    df_DB_list = add_DB_list(
        df_DB_list,
        load_url ="https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13110&cb=0.0&ct=9999999&et=9999999&md=05&md=06&md=07&ts=1&ts=2&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=",
        dbname ="Chintai.db",
        tablename="meguro_2K2DK2LDK",
    )
    
    # 世田谷区、2K, 2DK, 2LDK （建物種別　マンション、アパート）
    df_DB_list = add_DB_list(
        df_DB_list,
        load_url ="https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13112&cb=0.0&ct=9999999&et=9999999&md=05&md=06&md=07&ts=1&ts=2&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1",
        dbname ="Chintai.db",
        tablename="setagaya_2K2DK2LDK",
    )
    
    # 品川区、2K, 2DK, 2LDK （建物種別　マンション、アパート）
    df_DB_list = add_DB_list(
        df_DB_list,
        load_url ="https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13109&cb=0.0&ct=9999999&et=9999999&md=05&md=06&md=07&ts=1&ts=2&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1",
        dbname ="Chintai.db",
        tablename="shinagawa_2K2DK2LDK",
    )
    
    # 港区、2K, 2DK, 2LDK （建物種別　マンション、アパート）
    df_DB_list = add_DB_list(
        df_DB_list,
        load_url ="https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=13&sc=13103&cb=0.0&ct=9999999&et=9999999&md=05&md=06&md=07&ts=1&ts=2&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&srch_navi=1",
        dbname ="Chintai.db",
        tablename="minato_2K2DK2LDK",
    )
    
    for i in range(len(df_DB_list)):

        df_scraping = scraping_suumo(df_DB_list["load_url"][i])  # スクレイピング
        df_cleansing = cleansing_suumo(df_scraping)  # クレンジング
        df_cleansing = add_logitude_and_latitude(df_cleansing)  # 緯度・経度の追加
        save_to_db(df_DB_list["dbname"][i], df_DB_list["tablename"][i], df_cleansing)
    


if __name__ == '__main__':
    main()