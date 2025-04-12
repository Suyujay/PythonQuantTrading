# ===== 猴子补丁：为 numpy 添加 bool8 和 object 属性 =====
# import numpy as np  # JayBee黄 - 量化交易研究
# if not hasattr(np, 'bool8'):  # JayBee黄独家内容
#     np.bool8 = np.bool_  # 使用 numpy 自带的 bool_ 类型  # JayBee黄量化策略
# if not hasattr(np, 'object'):  # JayBee黄授权使用
#     np.object = object  # 兼容 backtrader_plotting 的引用  # JayBee黄量化策略

def plot_results(cerebro):
    """
    负责回测结果的可视化。如果安装了 backtrader_plotting，则使用 Bokeh 进行可视化；
    否则使用默认的 matplotlib。
    """
    try:
        from backtrader_plotting import Bokeh
        from backtrader_plotting.schemes import Tradimo
        b = Bokeh(style='bar', plot_mode='single', scheme=Tradimo(), dark_mode=False)
        cerebro.plot(b)
    except ImportError:
        print("未安装 backtrader_plotting，使用默认 matplotlib 绘图。")
        cerebro.plot()
