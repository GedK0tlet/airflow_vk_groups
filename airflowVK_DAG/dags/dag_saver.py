from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models import Variable

from scripts.fetch_data_vk import fetch_data


token = Variable.get('token_vk_api')
link = Variable.get('link_vk_group')

default_args = {
    'owner': 'Evgeniy',
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    dag_id='dag_saver_v01',
    default_args=default_args,
    start_date=datetime(2024, 9, 21),
    tags=['VK_DAG'],
    schedule_interval='0 * * * *',
) as dag:
    task_create_table = PostgresOperator(
        task_id='create_table_vk',
        postgres_conn_id='postgres_default',
        sql = """
            create table if not exists vk_group_posts (
                id serial PRIMARY KEY,
                vk_group_link VARCHAR,
                vk_post_id INTEGER,
                vk_post_text VARCHAR,
                vk_post_comments VARCHAR,
                time_created timestamp default now()
            )
        """
    )

    task_fetch_vk_data = PythonOperator(
        task_id='fetch_vk_data',
        provide_context=True,
        python_callable=fetch_data,
        op_kwargs = {'token': token, 'link': link}
    )


    task_insert_data = PostgresOperator(
        task_id='insert_data',
        postgres_conn_id='postgres_default',
        sql = '''
            insert into vk_group_posts (vk_group_link, vk_post_id, vk_post_text, vk_post_comments) 
            select '{{ti.xcom_pull(task_ids="fetch_vk_data", key="linck_group")}}',
                    '{{ti.xcom_pull(task_ids="fetch_vk_data", key="vk_post_id")}}',
                    '{{ti.xcom_pull(task_ids="fetch_vk_data", key="text_post")}}',
                    '{{ti.xcom_pull(task_ids="fetch_vk_data", key="comments_post")}}'
            where not exists(
                select vk_post_id from vk_group_posts where vk_post_id = '{{ti.xcom_pull(task_ids="fetch_vk_data", key="vk_post_id")}}'
            )
               ''',
        autocommit=True
    )

    task_create_table >> task_fetch_vk_data >> task_insert_data