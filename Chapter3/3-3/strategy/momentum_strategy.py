# filepath: d:\Quant\PythonQuantTrading\Chapter3\3-3\strategy\momentum_strategy.py
from .base_strategy import BaseStrategy # 假設 base_strategy.py 在同一目錄

class MomentumStrategy(BaseStrategy):
    """
    動量順勢策略
    """
    # 如果有特定參數，可以在這裡定義或覆寫
    # params = (('some_momentum_param', value),)

    def __init__(self):
        # 調用父類的 __init__ 來計算共享指標
        super().__init__()
        # 如果有動量策略特定的指標，在這裡計算
        # self.some_momentum_indicator = ...

    def is_uptrend_signal(self):
        """動量策略的多頭進場條件"""
        # 使用繼承來的指標
        return (self.dataclose[0] > self.ma_short[0] and
                self.ma_short[0] > self.ma_medium[0] and
                self.ma_medium[0] > self.ma_long[0] and
                self.atr_ratio[0] > self.params.atr_threshold_high and # 大波動
                self.mosc[0] > 100 and # 正動量
                self.vol_ma_short[0] > self.params.vol_ma_short_threshold) # 大量

    def is_downtrend_signal(self):
        """動量策略的空頭進場條件"""
        return (self.dataclose[0] < self.ma_short[0] and
                self.ma_short[0] < self.ma_medium[0] and
                self.ma_medium[0] < self.ma_long[0] and
                self.atr_ratio[0] > self.params.atr_threshold_high and # 大波動
                self.mosc[0] < 100 and # 負動量
                self.vol_ma_short[0] > self.params.vol_ma_short_threshold) # 大量

    def next(self):
        # 1. 檢查是否有掛單
        if self.order:
            return

        # 2. 檢查是否在交易時段
        if not self.check_trading_time():
            return # 如果不在交易時段且有倉位，check_trading_time 內部會處理平倉

        # 3. 管理現有倉位 (停損/停利)
        if self.manage_position():
             return # 如果觸發了停損停利，則本 K 線不再做其他操作

        # 4. 檢查進場條件 (如果沒有倉位)
        if not self.position:
            if self.is_uptrend_signal():
                self.log('動量多頭信號，創建買單')
                self.order = self.buy()
            elif self.is_downtrend_signal():
                self.log('動量空頭信號，創建賣單')
                self.order = self.sell()
        # else: # 如果有倉位，可以考慮是否加入基於信號反轉的出場邏輯
        #     if self.position.size > 0 and self.is_downtrend_signal():
        #         self.log('動量信號反轉，平多單')
        #         self.close()
        #     elif self.position.size < 0 and self.is_uptrend_signal():
        #         self.log('動量信號反轉，平空單')
        #         self.close()

