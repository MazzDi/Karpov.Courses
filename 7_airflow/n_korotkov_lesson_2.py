import requests
import pandas as pd
from datetime import timedelta
from datetime import datetime

from airflow import DAG
from airflow.operators.python import PythonOperator

TOP_1M_DOMAINS = 'http://s3.amazonaws.com/alexa-static/top-1m.csv.zip'
TOP_1M_DOMAINS_FILE = 'top-1m.csv'


def get_data():
    top_doms = pd.read_csv(TOP_1M_DOMAINS)
    top_data = top_doms.to_csv(index=False)
    with open(TOP_1M_DOMAINS_FILE, 'w') as f:
        f.write(top_data)


def get_top_domains():
    top_data_df = pd.read_csv(TOP_1M_DOMAINS_FILE, names=['rank', 'domain'])
    top_10_domains = top_data_df.domain.apply(lambda x: x.split('.')[-1])
    top_10_domains = top_10_domains.value_counts().reset_index()['index'].head(10)
    with open('top_10_domains.csv', 'w') as f:
        f.write(top_10_domains.to_csv(index=False, header=False))


def longest():
    top_data_df = pd.read_csv(TOP_1M_DOMAINS_FILE, names=['rank', 'domain'])
    longest_dm = top_data_df.loc[top_data_df.domain.str.len() == top_data_df.domain.str.len().max()].sort_values(by='domain').head(1)
    longest_dm = longest_dm.domain[longest_dm.domain.str.len().idxmax()]
    with open('longest_dm.txt', 'w') as f:
        f.write(longest_dm)
        f.close()
        
def air_place():
    top_data_df = pd.read_csv(TOP_1M_DOMAINS_FILE, names=['rank', 'domain'])
    airflow_pl = top_data_df.query('domain == "airflow.com"')
    airflow_pl = 'no such value in data frame' if airflow_pl.empty else str(airflow_pl['rank'].index[0])
    with open('air_place.txt', 'w') as f:
            f.write(airflow_pl)
            f.close()


def print_data(ds):
    with open('top_10_domains.csv', 'r') as f:
        top_10_domains = f.read()
    with open('longest_dm.txt', 'r') as f:
        longest_dm = f.read()
    with open('air_place.txt', 'r') as f:
        airflow_pl = f.read()
    date = ds

    print(f'Top 10 domians for {date}')
    print(top_10_domains)

    print(f'The longest full domian for {date}')
    print(f'{longest_dm}\n')
    
    print(f'Popularity of "airflow.com" domain for {date} is: {airflow_pl}')

default_args = {
    'owner': 'n-korotkov',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2022, 6, 12),
}
schedule_interval = '0 10 * * *'

dag = DAG('n_korotkov_lesson_2', default_args=default_args, schedule_interval=schedule_interval)

t1 = PythonOperator(task_id='get_data',
                    python_callable=get_data,
                    dag=dag)

t2_1 = PythonOperator(task_id='get_top_domains',
                    python_callable=get_top_domains,
                    dag=dag)

t2_2 = PythonOperator(task_id='longest',
                        python_callable=longest,
                        dag=dag)

t2_3 = PythonOperator(task_id='air_place',
                        python_callable=air_place,
                        dag=dag)

t3 = PythonOperator(task_id='print_data',
                    python_callable=print_data,
                    dag=dag)

t1 >> [t2_1, t2_2, t2_3] >> t3
