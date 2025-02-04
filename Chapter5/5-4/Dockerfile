# 使用官方 Airflow 映像
FROM apache/airflow:2.9.2
# 複製必要文件到容器
COPY ./requirements.txt /requirements.txt
ENV TZ=Asia/Taipei
# 安裝 Python 依賴
RUN pip install --no-cache-dir -r /requirements.txt
