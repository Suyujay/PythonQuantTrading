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
