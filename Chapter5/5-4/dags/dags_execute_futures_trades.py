# dags/execute_futures_trades.py

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
from futures_bt_trade import get_futures_trade_list
from shioaji_execute_futures_trade import execute_futures_trade
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

#
# 第一個 DAG：每週一到五的 8:45, 9:45, 10:45, 11:45, 12:45
#
with DAG(
    dag_id='多頭趨勢期貨交易策略_0845_1245',
    default_args=default_args,
    description='多頭交易策略 (8:45~12:45，每小時的第 45 分)',
    schedule_interval='45 8-12 * * 1-5',  # cron
    start_date=datetime.now(local_tz),
    catchup=False,
) as dag_1:

    start_dag_task = BashOperator(
        task_id='開始排程處理_第一段',
        bash_command='echo "排程開始處理...(8:45~12:45，每小時的 45 分)"'
    )

    run_futures_bt_trade = PythonOperator(
        task_id='使用backtrader產生期貨交易清單_第一段',
        python_callable=get_futures_trade_list
    )

    run_shioaji_execute_futures_trade = PythonOperator(
        task_id='期貨執行下單_第一段',
        python_callable=execute_futures_trade
    )

    end_dag_task = BashOperator(
        task_id='結束排程處理_第一段',
        bash_command='echo "排程結束處理...(8:45~12:45，每小時的 45 分)"'
    )

    start_dag_task >> run_futures_bt_trade >> run_shioaji_execute_futures_trade >> end_dag_task


#
# 第二個 DAG：每週一到五的 9:15, 10:15, 11:15, 12:15, 13:15
#
with DAG(
    dag_id='多頭趨勢期貨交易策略_0915_1315',
    default_args=default_args,
    description='多頭交易策略 (9:15~13:15，每小時的第 15 分)',
    schedule_interval='15 9-13 * * 1-5',  # cron
    start_date=datetime.now(local_tz),
    catchup=False,
) as dag_2:

    start_dag_task = BashOperator(
        task_id='開始排程處理_第二段',
        bash_command='echo "排程開始處理...(9:15~13:15，每小時的 15 分)"'
    )

    run_futures_bt_trade = PythonOperator(
        task_id='使用backtrader產生期貨交易清單_第二段',
        python_callable=get_futures_trade_list
    )

    run_shioaji_execute_futures_trade = PythonOperator(
        task_id='期貨執行下單_第二段',
        python_callable=execute_futures_trade
    )

    end_dag_task = BashOperator(
        task_id='結束排程處理_第二段',
        bash_command='echo "排程結束處理...(9:15~13:15，每小時的 15 分)"'
    )

    start_dag_task >> run_futures_bt_trade >> run_shioaji_execute_futures_trade >> end_dag_task
