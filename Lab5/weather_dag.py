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


def write_as_json() -> None:
    response = requests.get(
        'http://api.openweathermap.org/data/2.5/weather',
        params={
            'q': 'Guryevsk, Kemerovo, RU',  # Город, регион (область), страна
            'appid': Variable.get('weather_key'),
            'lang': 'ru',                   # Язык ответа
            'units': 'metric'              # Единицы измерения: градусы Цельсия
        }
    )
    if response.status_code != 200:
        raise requests.exceptions.RequestException

    with open('weather_data.json', 'w', encoding="utf-8") as outfile:
        js_response = response.json()
        js_response['units'] = 'metric'
        json.dump(js_response, outfile, ensure_ascii=False, indent=4)
    print("Файл успешно записан в формате JSON")


def from_json_to_csv_celsius():
    with open('weather_data.json', 'r', encoding="utf-8") as infile:
        data = json.load(infile)
    df_main = pd.json_normalize(data)
    df_weather = pd.json_normalize(
        data, record_path=["weather"], record_prefix="weather."
    )
    # Объединение нормализованных данных
    df = pd.concat([df_main, df_weather], axis=1).drop(columns="weather")

    if df.loc[0, 'units'] == 'metric':
        pass
    else:
        for col in ["main.temp", "main.feels_like", "main.temp_min", "main.temp_max"]:
            if col in df.columns:
                df[col] = (df[col] - 273.15).round(1)

    df.to_csv("weather_data.csv", index=False)
    print("Файл успешно переведён из JSON в CSV с температурой в цельсиях")


def from_csv_to_parquet():
    processed_df = pd.read_csv("weather_data.csv")
    processed_df.to_parquet("weather_data.parquet")
    print("Файл успешно переведён в формат Parquet")


def export_to_postgres():
    """
    Функция сохранения данных в Postgres БД
    """
    # Чтение данных из csv-файла
    df = pd.read_csv("weather_data.csv")

    # Подключение к PostgreSQL
    hook = PostgresHook(postgres_conn_id="postgres_weather")
    conn = hook.get_conn()
    cursor = conn.cursor()
    # Экспорт данных в PostgreSQL
    for index, row in df.iterrows():
        cursor.execute(
            f"""
            INSERT INTO weather_data
            (base, visibility, dt, timezone, id, name, cod, coord_lon, coord_lat, main_temp,
            main_feels_like, main_temp_min, main_temp_max, main_pressure, main_humidity,
            main_sea_level, main_grnd_level, wind_speed, wind_deg, clouds_all,
            sys_country, sys_sunrise, sys_sunset, weather_id, weather_main, weather_description,
            weather_icon)
            VALUES (
            '{row["base"]}',
            {row["visibility"]},
            {row["dt"]},
            {row["timezone"]},
            {row["id"]},
            '{row["name"]}',
            {row["cod"]},
            {row["coord.lon"]},
            {row["coord.lat"]},
            {row["main.temp"]},
            {row["main.feels_like"]},
            {row["main.temp_min"]},
            {row["main.temp_max"]},
            {row["main.pressure"]},
            {row["main.humidity"]},
            {row["main.sea_level"]},
            {row["main.grnd_level"]},
            {row["wind.speed"]},
            {row["wind.deg"]},
            {row["clouds.all"]},
            '{row["sys.country"]}',
            {row["sys.sunrise"]},
            {row["sys.sunset"]},
            {row["weather.id"]},
            '{row["weather.main"]}',
            '{row["weather.description"]}',
            '{row["weather.icon"]}'
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
    "weather_data_pipeline_dag",
    default_args=default_args,
    description="A weather data pipeline from openweathermap",
    schedule_interval="0 21 * * *",  # Запуск в полночь по MSK (UTC+3)
    catchup=False,
    tags=["weather"],
) as dag:

    download_data_task = PythonOperator(
        task_id="download_data",
        python_callable=write_as_json
    )

    process_data_task = PythonOperator(
        task_id="process_data",
        python_callable=from_json_to_csv_celsius
    )

    save_data_task = PythonOperator(
        task_id="save_data",
        python_callable=from_csv_to_parquet
    )

    create_weather_table = PostgresOperator(
        task_id="create_weather_table",
        postgres_conn_id="postgres_weather",
        sql="""
        CREATE TABLE IF NOT EXISTS weather_data (
        base VARCHAR(255),
        visibility INT,
        dt INT,
        timezone INT,
        id INT,
        name VARCHAR(255),
        cod INT,
        coord_lon DECIMAL(10,8),
        coord_lat DECIMAL(10,8),
        main_temp DECIMAL(10,2),
        main_feels_like DECIMAL(10,2),
        main_temp_min DECIMAL(10,2),
        main_temp_max DECIMAL(10,2),
        main_pressure INT,
        main_humidity INT,
        main_sea_level INT,
        main_grnd_level INT,
        wind_speed DECIMAL(10,2),
        wind_deg INT,
        clouds_all INT,
        sys_type VARCHAR(255),
        sys_country VARCHAR(255),
        sys_sunrise INT,
        sys_sunset INT,
        weather_id INT,
        weather_main VARCHAR(255),
        weather_description VARCHAR(255),
        weather_icon VARCHAR(255)
        );
        """,
    )

    export_to_db = PythonOperator(
        task_id="export_to_db",
        python_callable=export_to_postgres
    )

[download_data_task, create_weather_table] >> process_data_task >> save_data_task >> export_to_db