# filepath: d:\Quant\PythonQuantTrading\Chapter3\3-3\strategy\mean_reversion_strategy.py
from .base_strategy import BaseStrategy # 假設 base_strategy.py 在同一目錄
import backtrader as bt

class MeanReversionStrategy(BaseStrategy):
    """
    均值回歸逆勢策略
    """
    # params = (('rsi_oversold', 30), ('rsi_overbought', 70),)

    def __init__(self):
        super().__init__()
        # 可以訪問繼承來的指標，如 self.bbands, self.rsi
        # 如果有逆勢策略特定的指標，在這裡計算

    def is_buy_reversal_signal(self):
        """均值回歸的買入進場條件"""
        # 範例：價格觸及布林帶下軌 + RSI 超賣 + 小波動 + 小量
        return (self.dataclose[0] <= self.bbands.lines.bot[0] and
                # self.rsi[0] < self.params.rsi_oversold and
                self.atr_ratio[0] < self.params.atr_threshold_low and # 小波動
                self.vol_ma_short[0] < self.params.vol_threshold_low) # 小量

    def is_sell_reversal_signal(self):
        """均值回歸的賣出進場條件"""
        # 範例：價格觸及布林帶上軌 + RSI 超買 + 小波動 + 小量
        return (self.dataclose[0] >= self.bbands.lines.top[0] and
                # self.rsi[0] > self.params.rsi_overbought and
                self.atr_ratio[0] < self.params.atr_threshold_low and # 小波動
                self.vol_ma_short[0] < self.params.vol_threshold_low) # 小量

    def next(self):
        if self.order:
            return

        if not self.check_trading_time():
            return

        if self.manage_position():
             return

        if not self.position:
            if self.is_buy_reversal_signal():
                self.log('均值回歸買入信號，創建買單')
                self.order = self.buy()
            elif self.is_sell_reversal_signal():
                self.log('均值回歸賣出信號，創建賣單')
                self.order = self.sell()
        # else: # 均值回歸的出場通常是回到中軌或固定停利
        #     if self.position.size > 0 and self.dataclose[0] >= self.bbands.lines.mid[0]:
        #         self.log('均值回歸平多單 (回到中軌)')
        #         self.close()
        #     elif self.position.size < 0 and self.dataclose[0] <= self.bbands.lines.mid[0]:
        #         self.log('均值回歸平空單 (回到中軌)')
        #         self.close()