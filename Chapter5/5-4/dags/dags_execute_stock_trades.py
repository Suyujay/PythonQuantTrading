from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from stock_bt_trade import get_stock_trade_list
from shioaji_execute_stock_trade import execute_stock_trade
from airflow.operators.bash import BashOperator
import pendulum

local_tz = pendulum.timezone("Asia/Taipei")

default_args = {
    'owner': 'my trade',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=1),
}

# DAG 定義
with DAG(
    '財報選股策略',
    default_args=default_args,
    description='多頭交易策略',
    schedule_interval='0 9 * * 1-5',  # 週一到週五，每天早上 9 點執行
    start_date=datetime.now(local_tz),  # 設定 DAG 開始日期
    catchup=False,
) as dag:
    
    start_dag_task = BashOperator(
        task_id='開始排程處理',
        bash_command='echo "排程開始處理..."'
    )

    # 第一個任務：執行 stock_bt_trade.py
    run_stock_bt_trade = PythonOperator(
        task_id='使用backtrader產生股票交易清單',
        python_callable=get_stock_trade_list
    )

    # 第二個任務：執行 shioaji_execute_stock_trade.py
    run_shioaji_execute_stock_trade = PythonOperator(
        task_id='執行下單',
        python_callable=execute_stock_trade
    )

    end_dag_task = BashOperator(
        task_id='結束排程處理',
        bash_command='echo "排程結束處理..."'
    )

    # 定義相依性：第一個成功後執行第二個
    start_dag_task >> run_stock_bt_trade >> run_shioaji_execute_stock_trade >> end_dag_task
