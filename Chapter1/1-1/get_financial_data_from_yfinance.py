"""
1.如果還沒有安裝 yfinance 套件，先在終端機執行「pip install yfinance」
2.在終端機執行「cd BookCodeV1資料夾位置」切換到「BookCodeV1」資料夾下
3.在終端機中輸入「python Chapter1/1-1/get_financial_data_from_yfinance.py」來執行程式
"""

# 載入需要的套件
import yfinance as yf

# 以取得台積電 2330.TW 的財報資料為例
# 可以把「2330.TW」換成任意想查詢的公司股票代碼
stock = yf.Ticker("2330.TW")

print("取得台積電的季度損益表:")
print(stock.quarterly_financials)

print("取得台積電的季度資產負債表:")
print(stock.quarterly_balance_sheet)

print("取得台積電的季度現金流量表:")
print(stock.quarterly_cashflow)

print("取得台積電的年度損益表:")
print(stock.financials)

print("取得台積電的年度資產負債表:")
print(stock.balance_sheet)

print("取得台積電的年度現金流量表:")
print(stock.cashflow)
