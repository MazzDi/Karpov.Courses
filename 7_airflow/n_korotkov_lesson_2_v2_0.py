import requests
from zipfile import ZipFile
from io import BytesIO
from io import StringIO
import telegram

import pandas as pd
import numpy as np

from datetime import timedelta
from datetime import datetime

from airflow.models import Variable
from airflow.operators.python import get_current_context
from airflow.decorators import dag, task

TOP_1M_DOMAINS = 'http://s3.amazonaws.com/alexa-static/top-1m.csv.zip'
TOP_1M_DOMAINS_FILE = 'top-1m.csv'

default_args = {
    'owner': 'n-korotkov',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2022, 6, 12),
    'schedule_interval': '0 12 * * *'
}

@dag(default_args=default_args, catchup=False)
def n_kor_version_2_lesson_2():
    
    @task()
    def get_data():
        top_doms = requests.get(TOP_1M_DOMAINS, stream=True)
        zipfile = ZipFile(BytesIO(top_doms.content))
        top_data = zipfile.read(TOP_1M_DOMAINS_FILE).decode('utf-8')
        return top_data

    @task()
    def get_top_domains(top_data):
        top_data_df = pd.read_csv(StringIO(top_data), names=['rank', 'domain'])
        top_10_domains = top_data_df.domain.apply(lambda x: x.split('.')[-1])
        top_10_domains = top_10_domains.value_counts().reset_index()['index'].head(10).to_list()
        return {'top_10_domains': top_10_domains}

    @task()
    def longest(top_data):
        top_data_df = pd.read_csv(StringIO(top_data), names=['rank', 'domain'])
        longest_dm = top_data_df.loc[top_data_df.domain.str.len() == 
                                     top_data_df.domain.str.len().max()].sort_values(by='domain').head(1)
        longest_dm = longest_dm.domain[longest_dm.domain.str.len().idxmax()]
        return {'longest_dm': longest_dm}

    @task()
    def air_place(top_data):
        top_data_df = pd.read_csv(StringIO(top_data), names=['rank', 'domain'])
        airflow_pl = top_data_df.query('domain == "airflow.com"')
        airflow_pl = 'no such value in data frame' if airflow_pl.empty else str(airflow_pl['rank'].index[0])
        return {'airflow_pl': airflow_pl}

    @task()
    def print_data(top_domains, longest_one, air_p):
        context = get_current_context()
        date = context['ds']

        top_10 = top_domains['top_10_domains']
        longe = longest_one['longest_dm']
        air_pl = air_p['airflow_pl']

        print(f'Top 10 domians for {date}: {top_10}')

        print(f'The longest full domian for {date} is {longe}')

        print(f'Popularity of "airflow.com" domain for {date} is: {air_pl}')

    top_data = get_data()
    top_domains = get_top_domains(top_data)
    longest_domian = longest(top_data)
    airflow_place = air_place(top_data)
    print_data(top_domains, longest_domian, airflow_place)

n_kor_version_2_lesson_2 = n_kor_version_2_lesson_2()
