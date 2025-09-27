import requests
import json
import pandas as pd
from datetime import timedelta
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow import DAG
from airflow.models import Variable
from airflow.utils.dates import days_ago
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator


def get_crypto_price_to_json():
    def get_bitcoin_price(url):
        params = {
            'ids': 'bitcoin',
            'vs_currencies': 'RUB'
        }
        headers = {'api-key': Variable.get("crypto_key")}
        response = requests.get(url, headers=headers, params=params)
        return response.json()

    def get_ethereum_price(url):
        params = {
            'ids': 'ethereum',
            'vs_currencies': 'RUB'
        }
        headers = {'api-key': Variable.get("crypto_key")}
        response = requests.get(url, headers=headers, params=params)
        return response.json()

    url = 'https://api.coingecko.com/api/v3/simple/price'
    bit_jsn = get_bitcoin_price(url)
    eth_jsn = get_ethereum_price(url)
    res_jsn = {**bit_jsn, **eth_jsn}

    with open('crypto_price.json', 'w') as outfile:
        json.dump(res_jsn, outfile, ensure_ascii=False, indent=4)


def crypto_delete_errors():
    # Функция удаляет ошибки работы API
    with open('crypto_price.json', 'r', encoding="utf-8") as infile:
        data = json.load(infile)

    if 'status' in data.keys():
        del data['status']
    data_list = []
    for currency, prices in data.items():
        for price_currency, price in prices.items():
            data_list.append({
                'Криптовалюта': currency,
                'Цена': price,
                'Валюта цены': price_currency
            })

    # Преобразуем в DataFrame
    df = pd.DataFrame(data_list)

    df.to_csv('crypto_price.csv', index=False)


def crypto_from_csv_to_parquet():
    processed_df = pd.read_csv("crypto_price.csv")
    processed_df.to_parquet("crypto_price.parquet")


def crypto_export_to_postgres():
    """
    Функция сохранения данных в Postgres БД
    """
    # Чтение данных из csv-файла
    df = pd.read_csv("crypto_price.csv")

    # Подключение к PostgreSQL
    hook = PostgresHook(postgres_conn_id="crypto")
    conn = hook.get_conn()
    cursor = conn.cursor()
    # Экспорт данных в PostgreSQL
    for index, row in df.iterrows():
        cursor.execute(
            f"""
            INSERT INTO crypto_data
            (currency, price, price_currency)
            VALUES (
            '{row["Криптовалюта"]}',
            {row["Цена"]},
            '{row["Валюта цены"]}'
            );
            """
        )
    # Commit транзакций к БД
    conn.commit()
    cursor.close()
    conn.close()


default_args = {
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
    "start_date": days_ago(1),
}

with DAG(
    "crypto_pipeline_dag",
    default_args=default_args,
    description="A crypto pipeline from bit and eth",
    schedule_interval=timedelta(minutes=5),
    catchup=False,
    tags=["crypto"],
) as dag:

    get_crypto_price = PythonOperator(
        task_id="get_crypto",
        python_callable=get_crypto_price_to_json
    )

    delete_errors = PythonOperator(
        task_id="process_data_and_delete_errors",
        python_callable=crypto_delete_errors
    )

    from_scv_to_parquet = PythonOperator(
        task_id="from_csv_to_parquet",
        python_callable=crypto_from_csv_to_parquet
    )

    create_crypto_table = PostgresOperator(
        task_id="create_crypto_table",
        postgres_conn_id="crypto",
        sql="""
        CREATE TABLE IF NOT EXISTS crypto_data (
        currency VARCHAR(50),
        price INT,
        price_currency VARCHAR(255)
        );
        """,
    )

    export_crypto_to_db = PythonOperator(
        task_id="export_crypto_to_db",
        python_callable=crypto_export_to_postgres
    )

[get_crypto_price, create_crypto_table] >> delete_errors >> from_scv_to_parquet >> export_crypto_to_db
