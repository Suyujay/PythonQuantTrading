import numpy as np
import pandas as pd
import vectorbt as vbt
from vectorbt.portfolio.enums import SizeType
import datetime as dt
from typing import Tuple, Optional
from sklearn.model_selection import ParameterGrid
from tqdm import tqdm

class MAVolumeStrategy:
    """
    使用移動平均線、波動率和成交量指標的向量化交易策略
    """
    
    def __init__(
        self,
        ma_short: int = 3,#3,
        ma_medium: int = 15,#15,
        ma_long: int = 90,#90,
        stddev_short: int = 3,
        stddev_long: int = 30,
        vol_ma_short: int = 10,
        vol_ma_short_threshold: float = 1500,
        stop_loss_pct: float = 0.0002,
        take_profit_pct: float = 0.0005,
        trading_start: dt.time = dt.time(9, 20),
        trading_end: dt.time = dt.time(10, 0)
    ):
        """
        初始化策略參數
        """
        self.ma_short = ma_short
        self.ma_medium = ma_medium
        self.ma_long = ma_long
        self.stddev_short = stddev_short
        self.stddev_long = stddev_long
        self.vol_ma_short = vol_ma_short
        self.vol_ma_short_threshold = vol_ma_short_threshold
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.trading_start = trading_start
        self.trading_end = trading_end
    
    def filter_trading_hours(self, df: pd.DataFrame) -> pd.DataFrame:
        """過濾交易時段"""
        # 確保索引是日期時間類型
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # 創建時間過濾遮罩
        time_mask = ((df.index.time >= self.trading_start) & 
                     (df.index.time < self.trading_end))
        
        return df[time_mask].copy()
    
    def generate_signals(self, df: pd.DataFrame) -> Tuple[pd.Series, pd.Series]:
        """
        生成交易信號
        
        參數:
            df: 包含 'open', 'high', 'low', 'close', 'volume' 列的 DataFrame
            
        返回:
            (entries, exits): 包含進場和出場信號的兩個序列
        """
        # 過濾交易時段
        # filtered_df = self.filter_trading_hours(df)
        filtered_df = df
        
        if filtered_df.empty:
            return pd.Series(False, index=df.index), pd.Series(False, index=df.index)
        
        # 取得原始數據的時間遮罩（用於判斷何時屬於交易時段）
        time_mask = ((df.index.time >= self.trading_start) & 
                 (df.index.time < self.trading_end))
        
        # 計算指標 (使用 vectorbt 的 TA 功能)
        ma_short = vbt.MA.run(filtered_df['close'], self.ma_short).ma
        ma_medium = vbt.MA.run(filtered_df['close'], self.ma_medium).ma
        ma_long = vbt.MA.run(filtered_df['close'], self.ma_long).ma
        ma_short.to_csv('ma_short.csv')
        
        # 標準差指標
        stddev_short = filtered_df['close'].rolling(window=self.stddev_short).std()
        stddev_long = filtered_df['close'].rolling(window=self.stddev_long).std()
        
        # 成交量移動平均
        vol_ma_short = vbt.MA.run(filtered_df['volume'], self.vol_ma_short).ma
        
        # 計算進場信號
        long_entries = ((filtered_df['close'] > ma_short) & 
                        (filtered_df['close'] > ma_medium) & 
                        (filtered_df['close'] > ma_long) & 
                        (stddev_short > stddev_long) & 
                        (vol_ma_short > self.vol_ma_short_threshold))
        
        short_entries = ((filtered_df['close'] < ma_short) & 
                         (filtered_df['close'] < ma_medium) & 
                         (filtered_df['close'] < ma_long) & 
                         (stddev_short > stddev_long) & 
                         (vol_ma_short > self.vol_ma_short_threshold))
        
        # 將信號擴展到原始 DataFrame 的索引
        entries_long = pd.Series(False, index=df.index)
        entries_short = pd.Series(False, index=df.index)
        entries_long.loc[long_entries.index] = long_entries
        entries_short.loc[short_entries.index] = short_entries

        # 限制進場信號：僅在交易時段內有效
        entries_long = entries_long & time_mask
        entries_short = entries_short & time_mask

        # 出場信號將在回測過程中動態生成
        exits = pd.Series(False, index=df.index)

        # 如果超過交易時段則強制平倉：非交易時段全部為 exit 信號
        exits = (~time_mask).copy()
        
        return entries_long, exits, entries_short
    
    def backtest(self, df: pd.DataFrame, initial_capital: float = 100000.0) -> vbt.Portfolio:
        """
        執行回測
        
        參數:
            df: 包含 'open', 'high', 'low', 'close', 'volume' 列的 DataFrame
            initial_capital: 初始資金
            
        返回:
            vbt.Portfolio 實例
        """
        # 生成信號
        entries_long, exits, entries_short = self.generate_signals(df)
        
        # 使用 vectorbt 的 Portfolio 進行回測，包括止損和止盈
        portfolio = vbt.Portfolio.from_signals(
            # price=df['close'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            # volume=df['volume'],
            entries=entries_long,
            short_entries=entries_short,
            exits=exits,
            # short_exits=
            size=20,  # 每次交易的頭寸大小
            min_size=20,
            size_type=SizeType.Amount,  # 頭寸大小類型
            init_cash=initial_capital,
            fixed_fees=2.2,  # 手續費, 相當於 0.2%
            sl_stop=self.stop_loss_pct,  # 止損比例
            tp_stop=self.take_profit_pct,  # 止盈比例
            accumulate=False,  # 是否累積頭寸
            freq='1min'  # 時間頻率
        )
        
        return portfolio
    
    def optimize(
        self, 
        df: pd.DataFrame, 
        ma_short_range: list = None,
        ma_medium_range: list = None,
        ma_long_range: list = None,
        stop_loss_range: list = None,
        take_profit_range: list = None,
        stddev_short_range: list = None,
        stddev_long_range: list = None,
        vol_ma_short_range: list = None,
        vol_ma_short_threshold_range: list = None
    ) -> pd.DataFrame:
        """
        參數優化
        """
        # 默認參數範圍
        if ma_short_range is None:
            ma_short_range = [3, 5, 10]
        if ma_medium_range is None:
            ma_medium_range = [15, 20, 30]
        if ma_long_range is None:
            ma_long_range = [60, 90, 120]
        if stop_loss_range is None:
            stop_loss_range = [round(0.0001 + i * 0.0001, 5) for i in range(5)]
        if take_profit_range is None:
            take_profit_range = [round(0.0001 + i * 0.0001, 5) for i in range(5)]
        if stddev_short_range is None:
            stddev_short_range = [2, 3, 4]
        if stddev_long_range is None:
            stddev_long_range = [20, 30, 40]
        if vol_ma_short_range is None:
            vol_ma_short_range = [5, 10, 15]
        if vol_ma_short_threshold_range is None:
            vol_ma_short_threshold_range = [1000, 1500, 2000]
        
        # 創建參數網格
        param_grid = {
            'ma_short': ma_short_range,
            'ma_medium': ma_medium_range,
            'ma_long': ma_long_range,
            'stop_loss_pct': stop_loss_range,
            'take_profit_pct': take_profit_range,
            'stddev_short': stddev_short_range,
            'stddev_long': stddev_long_range,
            'vol_ma_short': vol_ma_short_range,
            # 'vol_ma_short_threshold': vol_ma_short_threshold_range
        }
        
        # 使用 sklearn 的 ParameterGrid
        grid = ParameterGrid(param_grid)
        
        results = []
        for params in tqdm(grid, desc='Parameter grid'):
            strategy = MAVolumeStrategy(
                ma_short=params['ma_short'],
                ma_medium=params['ma_medium'],
                ma_long=params['ma_long'],
                stop_loss_pct=params['stop_loss_pct'],
                take_profit_pct=params['take_profit_pct'],
                stddev_short=params['stddev_short'],
                stddev_long=params['stddev_long'],
                vol_ma_short=params['vol_ma_short'],
                # vol_ma_short_threshold=params['vol_ma_short_threshold'],
                trading_start=self.trading_start,
                trading_end=self.trading_end
            )
            
            portfolio = strategy.backtest(df)
            
            results.append({
                'ma_short': params['ma_short'],
                'ma_medium': params['ma_medium'],
                'ma_long': params['ma_long'],
                'stop_loss_pct': params['stop_loss_pct'],
                'take_profit_pct': params['take_profit_pct'],
                'stddev_short': params['stddev_short'],
                'stddev_long': params['stddev_long'],
                'vol_ma_short': params['vol_ma_short'],
                'vol_ma_short_threshold': self.vol_ma_short_threshold,
                'total_return': portfolio.total_return(),
                'sharpe_ratio': portfolio.sharpe_ratio(),
                'max_drawdown': portfolio.max_drawdown(),
                'win_rate': portfolio.trades.win_rate()
            })
        
        df_results = pd.DataFrame(results)
        df_results = df_results.sort_values(by='total_return', ascending=False)
        df_results.reset_index(drop=True, inplace=True)
        df_results.to_csv('optimization_results.csv', index=False)
        return df_results

# 使用示例
def run_backtest(csv_file, initial_capital=100000.0):
    """
    運行回測示例
    
    參數:
        csv_file: CSV 文件路徑
        initial_capital: 初始資金
    """
    # 讀取數據
    df = pd.read_csv(csv_file)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    
    # 創建策略實例
    strategy = MAVolumeStrategy()
    
    # 執行回測
    portfolio = strategy.backtest(df, initial_capital)
    
    # 顯示結果
    print(f"總收益: {portfolio.total_return():.2%}")
    print(f"夏普比率: {portfolio.sharpe_ratio():.2f}")
    print(f"最大回撤: {portfolio.max_drawdown():.2%}")
    print(f"勝率: {portfolio.trades.win_rate():.2%}")
    
    # 繪製績效圖表
    portfolio.plot()
    
    return portfolio

if __name__ == "__main__":
    # 如果直接運行此文件，則執行示例回測
    run_backtest('../../TXF_30.csv')