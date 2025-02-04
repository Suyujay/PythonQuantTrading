"""
1.如果還沒有安裝 typing_extensions 套件，先在終端機執行「pip install typing_extensions」
2.在終端機執行「cd BookCodeV1資料夾位置」切換到「BookCodeV1」資料夾下
3.在終端機中輸入「python Chapter1/1-2/annotated_example.py」來執行程式
"""

# 載入需要的套件
from typing import Tuple

from typing_extensions import Annotated


def annotated_example(
    n1: Annotated[int, "這個數字將會被加1"], n2: Annotated[int, "這個數字將會被加2"]
) -> Tuple[Annotated[str, "轉成文字的 n1+1"], Annotated[str, "轉成文字的 n2+2"]]:
    """
    接受兩個整數作為輸入，n1 會加 1，n2 會加 2，然後將加總結果轉換為字串形式回傳。
    """
    return str(n1 + 1), str(n2 + 2)


print(f"輸出結果：{annotated_example(3, 4)}")  # 輸出結果：('4', '6')
