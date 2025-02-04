# 載入需要的套件
import os
from datetime import datetime
from typing import List, Tuple

import finlab
import pandas as pd
import yfinance as yf
from dotenv import load_dotenv
from finlab import data
from pandas.core.indexes.datetimes import DatetimeIndex
from typing_extensions import Annotated


def finlab_login() -> None:
    """
    函式說明: 使用 FinLab API token 登入 FinLab。
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 載入 .env檔案中定義的變數
    load_dotenv(f"{current_dir}/.env")
    # 取得儲存在 .env檔案中 FINLAB API Token
    api_token = os.getenv("FINLABTOKEN")
    # 使用 API Token 登入 FinLab 量化平台
    finlab.login(api_token=api_token)


# finlab_login()


def get_top_stocks_by_market_value(
    excluded_industry: Annotated[List[str], "需要排除的特定產業類別列表"] = [],
    pre_list_date: Annotated[str, "上市日期須早於此指定日期"] = None,
    top_n: Annotated[int, "市值前 N 大的公司"] = None,
) -> Annotated[List[str], "符合條件的公司代碼列表"]:
    """
    函式說明:
    篩選市值前 N 大的上市公司股票代碼，並以列表形式回傳。篩選過程包括以下條件：
    1. 排除特定產業的公司(excluded_industry)。
    2. 僅篩選上市日期早於指定日期(pre_list_date)的公司。
    3. 選擇市值前 N 大的公司(top_n)。
    """
    # 從 FinLab 取得公司基本資訊表，內容包括公司股票代碼、公司名稱、上市日期和產業類別
    company_info = data.get("company_basic_info")[
        ["stock_id", "公司名稱", "上市日期", "產業類別", "市場別"]
    ]
    # 如果有指定要排除的產業類別，則過濾掉這些產業的公司
    if excluded_industry:
        company_info = company_info[~company_info["產業類別"].isin(excluded_industry)]
    # 如果有設定上市日期條件，則過濾掉上市日期晚於指定日期的公司
    if pre_list_date:
        company_info = company_info[company_info["市場別"] == "sii"]
        company_info = company_info[company_info["上市日期"] < pre_list_date]
    # 如果有設定top_n條件，則選取市值前 N 大的公司股票代碼
    if top_n:
        # 從 FinLab 取得最新的個股市值數據表，並重設索引名稱為 market_value
        market_value = pd.DataFrame(data.get("etl:market_value"))
        market_value = market_value[market_value.index == pre_list_date]
        market_value = market_value.reset_index().melt(
            id_vars="date", var_name="stock_id", value_name="market_value"
        )
        # 將市值數據表與公司資訊表根據股票代碼欄位(stock_id)進行合併，
        # 並根據市值欄位(market_value)將公司由大到小排序
        company_info = pd.merge(market_value, company_info, on="stock_id").sort_values(
            by="market_value", ascending=False
        )
        return company_info.head(top_n)["stock_id"].tolist()
    else:
        return company_info["stock_id"].tolist()


# print(
#     get_top_stocks_by_market_value(
#         excluded_industry=["建材營造"],
#         pre_list_date="2017-01-03",
#         market_cap_date="2017-01-03",
#         top_n=100,
#     )
# )


def get_daily_close_prices_data(
    stock_symbols: Annotated[List[str], "股票代碼列表"],
    start_date: Annotated[str, "起始日期", "YYYY-MM-DD"],
    end_date: Annotated[str, "結束日期", "YYYY-MM-DD"],
    is_tw_stock: Annotated[bool, "stock_symbols 是否是台灣股票"] = True,
) -> Annotated[
    pd.DataFrame,
    "每日股票收盤價資料表",
    "索引是日期(DatetimeIndex格式)",
    "欄位名稱包含股票代碼",
]:
    """
    函式說明:
    獲取指定股票清單(stock_symbols)在給定日期範圍內(start_date~end_date)每日收盤價資料。
    """
    # 如果是台灣股票，則在每個股票代碼後加上 ".TW"
    if is_tw_stock:
        stock_symbols = [
            f"{symbol}.TW" if ".TW" not in symbol else symbol
            for symbol in stock_symbols
        ]
    # 從 YFinance 下載指定股票在給定日期範圍內的數據，並取出收盤價欄位(Close)的資料
    stock_data = yf.download(stock_symbols, start=start_date, end=end_date)["Close"]
    # 如果只取一支股票，將其轉換為 DataFrame 並設定欄位名稱為該股票代碼
    if len(stock_symbols) == 1:
        stock_data = pd.DataFrame(stock_data)
        stock_data.columns = stock_symbols
    # 使用向前填補方法處理資料中的遺失值
    stock_data = stock_data.ffill()
    # 將欄位名稱中的 ".TW" 移除，只保留股票代碼
    stock_data.columns = stock_data.columns.str.replace(".TW", "", regex=False)
    return stock_data


# print(
#     get_daily_close_prices_data(
#         stock_symbols=["2330", "1101"],
#         start_date="2022-01-01",
#         end_date="2022-01-08",
#         is_tw_stock=True,
#     )
# )
# print(
#     get_daily_close_prices_data(
#         stock_symbols=["2330"],
#         start_date="2022-01-01",
#         end_date="2022-01-08",
#         is_tw_stock=True,
#     )
# )


def get_factor_data(
    stock_symbols: Annotated[List[str], "股票代碼列表"],
    factor_name: Annotated[str, "因子名稱"],
    trading_days: Annotated[
        List[DatetimeIndex], "如果有指定日期，就會將資料的頻率從季頻擴充成此交易日頻率"
    ] = None,
) -> Annotated[
    pd.DataFrame,
    "有指定trading_days，回傳多索引資料表,索引是datetime和asset,欄位包含value(因子值)。",
    "未指定trading_days，回傳原始FinLab因子資料表,索引是datetime,欄位包含股票代碼。",
]:
    """
    函式說明:
    從 FinLab 獲取指定股票清單(stock_symbols)的單個因子(factor_name)資料，
    並根據需求擴展至交易日頻率資料或是回傳原始季頻因子資料。
    如果沒有指定交易日(trading_days)，則回傳原始季頻因子資料。
    """
    # 從 FinLab 獲取指定因子資料表，並藉由加上 .deadline() 將索引格式轉為財報截止日
    factor_data = data.get(f"fundamental_features:{factor_name}").deadline()
    # 如果指定了股票代碼列表，則篩選出特定股票的因子資料
    if stock_symbols:
        factor_data = factor_data[stock_symbols]
    # 如果指定了交易日，則將「季度頻率」的因子資料擴展至「交易日頻率」的資料，
    # 否則回傳原始資料
    if trading_days is not None:
        factor_data = factor_data.reset_index()
        factor_data = extend_factor_data(
            factor_data=factor_data, trading_days=trading_days
        )
        # 使用 melt 轉換資料格式
        factor_data = factor_data.melt(
            id_vars="index", var_name="asset", value_name="value"
        )
        # 重命名欄位名稱，且根據日期、股票代碼進行排序，最後設定多重索引 datetime 和 asset
        factor_data = (
            factor_data.rename(columns={"index": "datetime"})
            .sort_values(by=["datetime", "asset"])
            .set_index(["datetime", "asset"])
        )
    return factor_data


def extend_factor_data(
    factor_data: Annotated[
        pd.DataFrame,
        "未擴充前的因子資料表",
        "欄位名稱包含index(日期欄位名稱)和股票代碼",
    ],
    trading_days: Annotated[List[DatetimeIndex], "交易日的列表"],
) -> Annotated[
    pd.DataFrame,
    "填補後的因子資料表",
    "欄位名稱包含index(日期欄位名稱)和股票代碼",
]:
    """
    函式說明:
    將因子資料(factor_data)擴展至交易日頻率(trading_days)資料，使用向前填補的方式補值。
    """
    # 將交易日列表轉換為 DataFrame 格式，索引為指定的交易日的列表
    trading_days_df = pd.DataFrame(trading_days, columns=["index"])
    # 將交易日資料與因子資料進行合併，以交易日資料有的日期為主
    extended_data = pd.merge(trading_days_df, factor_data, on="index", how="outer")
    extended_data = extended_data.ffill()
    # 最後只回傳在和 trading_days_df 時間重疊的資料
    extended_data = extended_data[
        (extended_data["index"] >= min(trading_days_df["index"]))
        & (extended_data["index"] <= max(trading_days_df["index"]))
    ]
    return extended_data


# trading_days = pd.date_range(start="2020-01-01", end="2020-12-01", freq="D")
# print(
#     get_factor_data(
#         stock_symbols=[
#             "2330",
#             "1101",
#         ],
#         factor_name="營業利益",
#         trading_days=trading_days,
#     )
# )
# print(
#     get_factor_data(
#         stock_symbols=[
#             "2330",
#             "1101",
#         ],
#         factor_name="營業利益",
#         trading_days=None,
#     )
# )


def convert_quarter_to_dates(
    quarter: Annotated[str, "年-季度字串，例如：2013-Q1"],
) -> Annotated[Tuple[str, str], "季度對應的起始和結束日期字串"]:
    """
    函式說明:
    將季度字串(quarter)轉換為起始和結束日期字串。
    ex: 2013-Q1 -> 2013-05-16, 2013-08-14。
    """
    year, qtr = quarter.split("-")
    if qtr == "Q1":
        return f"{year}-05-16", f"{year}-08-14"
    if qtr == "Q2":
        return f"{year}-08-15", f"{year}-11-14"
    if qtr == "Q3":
        return f"{year}-11-15", f"{int(year) + 1}-03-31"
    if qtr == "Q4":
        return f"{int(year) + 1}-04-01", f"{int(year) + 1}-05-15"


# print(convert_quarter_to_dates(quarter="2013-Q1"))
# print(convert_quarter_to_dates(quarter="2013-Q2"))
# print(convert_quarter_to_dates(quarter="2013-Q3"))
# print(convert_quarter_to_dates(quarter="2013-Q4"))


def convert_date_to_quarter(
    date: Annotated[str, "日期字串，格式為 YYYY-MM-DD"],
) -> Annotated[str, "對應的季度字串"]:
    """
    函式說明:
    將日期字串(date)轉換為季度字串。
    ex: 2013-05-16 -> 2013-Q1
    yyyy-mm-dd -> yyyy-q。
    """
    # 將字串轉換為日期格式
    date_obj = datetime.strptime(date, "%Y-%m-%d").date()
    year, month, day = (
        date_obj.year,
        date_obj.month,
        date_obj.day,
    )  # 獲取年份、月份和日期
    # 根據日期判斷所屬的季度並回傳相應的季度字串
    if month == 5 and day >= 16 or month in [6, 7] or (month == 8 and day <= 14):
        return f"{year}-Q1"
    elif month == 8 and day >= 15 or month in [9, 10] or (month == 11 and day <= 14):
        return f"{year}-Q2"
    elif month == 11 and day >= 15 or month in [12]:
        return f"{year}-Q3"
    elif (month == 1) or (month == 2) or (month == 3 and day <= 31):
        return f"{year-1}-Q3"
    elif month == 4 or (month == 5 and day <= 15):
        return f"{year-1}-Q4"


# print(convert_date_to_quarter(date="2013-05-16"))
# print(convert_date_to_quarter(date="2013-08-14"))
# print(convert_date_to_quarter(date="2013-08-15"))
# print(convert_date_to_quarter(date="2013-11-14"))
# print(convert_date_to_quarter(date="2013-11-15"))
# print(convert_date_to_quarter(date="2014-03-31"))
# print(convert_date_to_quarter(date="2014-04-01"))
# print(convert_date_to_quarter(date="2014-05-15"))


def rank_stocks_by_factor(
    factor_df: Annotated[
        pd.DataFrame,
        "因子資料表",
        "欄位名稱含asset(股票代碼欄位)、datetime(日期欄位)、value(因子值欄位)",
    ],
    positive_corr: Annotated[bool, "因子與收益的相關性, 正相關為 True, 負相關為 False"],
    rank_column: Annotated[str, "用於排序的欄位名稱"],
    rank_result_column: Annotated[str, "保存排序結果的欄位名稱"] = "rank",
) -> Annotated[
    pd.DataFrame,
    "包含排序結果的資料表",
    "欄位名稱含asset(股票代碼)、datetime(日期)、value(因子值欄位)、rank(排序結果欄位)",
]:
    """
    函式說明:
    根據某個指定因子的值(rank_column)對股票進行排序，
    遞增或遞減排序方式取決於因子與未來收益的相關性(positive_corr)。
    如果相關性為正，則將股票按因子值由小到大排序；如果為負，則按因子值由大到小排序。
    最後，將排序結果新增至原始因子資料表中，且指定排序結果欄位名稱為 rank_result_column。
    """
    # 複製因子資料表，以避免對原資料進行修改
    ranked_df = factor_df.copy()
    # 將 datetime 欄位設置為索引
    ranked_df = ranked_df.set_index("datetime")
    # 針對每一天的資料，根據指定的因子欄位進行排名
    # 如果因子與收益正相關，則根據因子值由小到大排名
    # 如果因子與收益負相關，則根據因子值由大到小排名
    ranked_df[rank_result_column] = ranked_df.groupby(level="datetime")[
        rank_column
    ].rank(ascending=positive_corr)
    ranked_df = ranked_df.fillna(0)
    ranked_df.reset_index(inplace=True)
    return ranked_df


# trading_days = pd.date_range(start="2020-01-01", end="2020-01-03", freq="D")
# test_factor_df = get_factor_data(
#     stock_symbols=["1101", "1102", "2330", "2912"],
#     factor_name="營業利益",
#     trading_days=trading_days,
# )
# test_factor_df = test_factor_df.reset_index()
# rank_stocks_by_factor(
#     factor_df=test_factor_df,
#     positive_corr=True,
#     rank_column="value",
#     rank_result_column="rank",
# )
# rank_stocks_by_factor(
#     factor_df=test_factor_df,
#     positive_corr=False,
#     rank_column="value",
#     rank_result_column="rank",
# )


def calculate_weighted_rank(
    ranked_dfs: Annotated[
        List[pd.DataFrame],
        "多個包含因子排名資料表的列表",
        "欄位名稱含asset(股票代碼)、datetime(日期)、value(因子值欄位)、rank(排序結果欄位)",
    ],
    weights: Annotated[List[float], "對應於各因子權重的列表"],
    positive_corr: Annotated[
        bool, "因子與收益相關性的列表, 正相關為 True, 負相關為 False"
    ],
    rank_column: Annotated[str, "用於排序的欄位名稱"],
) -> Annotated[
    pd.DataFrame,
    "包含加權排序結果的資料表",
    "欄位名稱含asset(股票代碼)、datetime(日期)和加權排名結果(weighted_rank)",
]:
    """
    函式說明:
    根據多個因子的加權排名計算最終的股票排名。
    len(ranked_dfs) 會等於 len(weights)
    """
    # 檢查 ranked_dfs 和 weights 的長度是否相同，否則拋出錯誤
    # 也就是有 n 個因子資料就需要有 n 個權重值
    if len(ranked_dfs) != len(weights):
        raise ValueError("ranked_dfs 和 weights 的長度必須相同。")
    # 初始化 combined_ranks 為空的 DataFrame，用來儲存加權後的排名結果
    combined_ranks = pd.DataFrame()
    # 遍歷每個因子排名資料表及其對應的權重
    for i, df in enumerate(ranked_dfs):
        # 將每個因子的排名乘以對應的權重，並存入新的欄位 rank_i
        df[f"rank_{i}"] = df[rank_column] * weights[i]
        if combined_ranks.empty:
            combined_ranks = df[["datetime", "asset", f"rank_{i}"]]
        else:
            # 根據 datetime 和 asset 這兩個欄位將資料進行合併
            combined_ranks = pd.merge(
                combined_ranks,
                df[["datetime", "asset", f"rank_{i}"]],
                on=["datetime", "asset"],
                how="outer",
            )
    # 將合併後的資料中遺失值刪除
    combined_ranks = combined_ranks.dropna()
    # 最後，將所有乘上權重的排名進行每個股票每日的加總，得到最終的加權排名
    combined_ranks["weighted"] = combined_ranks.filter(like="rank_").sum(axis=1)
    # 根據加權總分計算最終的股票排名
    # 使用 rank_stocks_by_factor 函數對加權排名結果進行排序
    ranked_df = rank_stocks_by_factor(
        factor_df=combined_ranks,
        positive_corr=positive_corr,
        rank_column="weighted",
        rank_result_column="weighted_rank",
    )
    return ranked_df[["datetime", "asset", "weighted_rank"]]


# trading_days = pd.date_range(start="2020-01-01", end="2020-01-02", freq="D")
# test_factor_data = get_factor_data(
#     stock_symbols=["1101", "1102", "2330", "2912"],
#     factor_name="營業利益",
#     trading_days=trading_days,
# )
# test_factor_data = test_factor_data.reset_index()
# test_2factors_data_list = [
#     rank_stocks_by_factor(
#         factor_df=test_factor_data,
#         positive_corr=True,
#         rank_column="value",
#         rank_result_column="rank",
#     ),
#     rank_stocks_by_factor(
#         factor_df=test_factor_data,
#         positive_corr=True,
#         rank_column="value",
#         rank_result_column="rank",
#     ),
# ]
# calculate_weighted_rank(
#     ranked_dfs=test_2factors_data_list,
#     weights=[1 / 2, 1 / 2],
#     positive_corr=True,
#     rank_column="rank",
# )


def get_daily_OHLCV_data(
    stock_symbols: Annotated[List[str], "股票代碼列表"],
    start_date: Annotated[str, "起始日期", "YYYY-MM-DD"],
    end_date: Annotated[str, "結束日期", "YYYY-MM-DD"],
    is_tw_stock: Annotated[bool, "stock_symbols 是否是台灣股票"] = True,
) -> Annotated[pd.DataFrame, "價量的資料集", "欄位名稱包含股票代碼、日期、開高低收量"]:
    """
    函式說明:
    取得指定股票(stock_symbols)在給定日期範圍內(start_date~end_date)的每日價量資料。
    """
    # 如果是台灣股票，則在股票代碼後加上 ".TW"
    if is_tw_stock:
        stock_symbols = [
            f"{symbol}.TW" if ".TW" not in symbol else symbol
            for symbol in stock_symbols
        ]
    # 使用 pd.concat 合併多隻股票的數據
    all_stock_data = pd.concat(
        [
            # 從 YFinance 下載每隻股票在指定日期範圍內的數據
            pd.DataFrame(yf.download(symbol, start=start_date, end=end_date)).droplevel(
                "Ticker", axis=1
            )
            # 新增一個 "asset" 的欄位，用來儲存股票代碼
            .assign(asset=symbol.split(".")[0])
            # 重設索引並將日期欄位名稱從 Date 改為 datetime
            .reset_index().rename(columns={"Date": "datetime"})
            # 使用向前填補的方法處理資料中的遺失值
            .ffill()
            for symbol in stock_symbols
        ]
    )
    all_stock_data.columns.name = None
    all_stock_data = all_stock_data[
        ["Open", "High", "Low", "Close", "Volume", "datetime", "asset"]
    ]
    return all_stock_data.reset_index(drop=True)


# print(
#     get_daily_OHLCV_data(
#         stock_symbols=["2330", "1101"],
#         start_date="2022-01-01",
#         end_date="2022-01-08",
#         is_tw_stock=True,
#     )
# )
# print(
#     get_daily_OHLCV_data(
#         stock_symbols=["2330"],
#         start_date="2022-01-01",
#         end_date="2022-01-08",
#         is_tw_stock=True,
#     )
# )


def list_factors_by_type(
    data_type: Annotated[str, "資料型態，例如：fundamental_features"],
) -> Annotated[List[str], "該資料型態下的所有項目列表"]:
    """
    函式說明:
    根據資料型態列出所有相關的因子名稱。
    """
    return list(
        data.search(keyword=data_type, display_info=["name", "description", "items"])[
            0
        ]["items"]
    )


# print(list_factors_by_type(data_type="fundamental_features"))
