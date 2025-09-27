from datetime import timedelta
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago


# Определяем функцию на уровне модуля
def print_hello():
    print('Hello Airflow in Python!')


# Определяем DAG
with DAG(
    "my_test_dag",
    default_args={
        "depends_on_past": False,
        "email": ["airflow@example.com"],
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
    },
    description="My test Dag",
    schedule=None,
    start_date=days_ago(1),
    tags=["test"],
) as dag:

    # Определяем операторы
    bash = BashOperator(
        task_id="bash",
        bash_command="echo Hello Airflow in bash!"
    )

    python = PythonOperator(
        task_id='python',
        python_callable=print_hello
    )

    # Устанавливаем последовательность выполнения операторов
    bash >> python
