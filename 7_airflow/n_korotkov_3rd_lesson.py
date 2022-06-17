import requests
from zipfile import ZipFile
from io import BytesIO
import pandas as pd
import numpy as np
from io import StringIO
import telegram

from datetime import timedelta
from datetime import datetime

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context
from airflow.models import Variable

FILE_ADRESS = 'https://git.lab.karpov.courses/lab/airflow/-/blob/master/dags/n-korotkov/vgsales.csv'
FILE_PATH = 'vgsales.csv'
login = 'n-korotkov'
my_year = 1994 + hash(f'{login}') % 23

default_args = {
    'owner': 'n-korkotkov',
    'depends_on_past': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2021, 6, 14),
    'schedule_interval': '0 9 * * *'
}

CHAT_ID = 641886254
try:
    BOT_TOKEN = Variable.get('telegram_secret')
except:
    BOT_TOKEN = ''

def send_message(context):
    date = context['ds']
    dag_id = context['dag'].dag_id
    message = f'Huge success! Dag {dag_id} completed on {date}'
    if BOT_TOKEN != '':
        bot = telegram.Bot(token=BOT_TOKEN)
        bot.send_message(chat_id=CHAT_ID, text=message)
    else:
        pass

@dag(default_args=default_args, catchup=False)
def n_korkotkov_3rd_lesson():
    @task()
    def get_data():
        games_info_df = pd.read_csv(FILE_PATH)
        return games_info_df

    @task()
    def filt_data(games_info_df):
        login = 'n-korotkov'
        my_year = 1994 + hash(f'{login}') % 23
        games_info_df.columns = games_info_df.columns.str.lower()
        games_info_df = games_info_df[games_info_df['year'].notna()]
        games_info_df.year = games_info_df.year.astype('int')
        final_games_df = games_info_df.query('year == @my_year')
        return final_games_df

    @task()
    def top_game_ww(final_games_df):
        top_game = final_games_df.sort_values(by='global_sales', ascending=False).head(1).name.to_list()[0]
        return {'top_game': top_game}

    @task()
    def top_eu_genre(final_games_df):
        # Преположим, что "самые продаваемые в Европе" - это топ 5 по колонке eu_sales.
        top_list = final_games_df.groupby('genre').eu_sales.sum().sort_values(ascending=False).head(5).index.to_list()
        return {'top_list': top_list}

    @task()
    def top_na_platforms(final_games_df):
        top_platforms = final_games_df.loc[final_games_df.na_sales >= 1] \
                                      .groupby('platform') \
                                      .name.nunique() \
                                      .sort_values(ascending=False)
        top_platforms = top_platforms[top_platforms == top_platforms.max()].index.to_list()
        return {'top_platforms': top_platforms}

    @task()
    def best_publisher(final_games_df):
        best_one_s = final_games_df.groupby('publisher').jp_sales.mean().sort_values(ascending=False)
        best_one_s = best_one_s[best_one_s == best_one_s.max()].index.to_list()
        return {'best_one_s': best_one_s}

    @task()
    def eu_jp_games(final_games_df):
        eu_jp = final_games_df.loc[final_games_df.eu_sales > final_games_df.jp_sales].name.nunique()
        return {'eu_jp': eu_jp}

    @task(on_success_callback=send_message)
    def print_data(top_g, top_l, top_p, best_o, eu_vs_jp, year):
        context = get_current_context()
        date = context['ds']

        tGame = top_g['top_game']
        tList = top_l['top_list']
        tPlatform = top_p['top_platforms']
        bOne = best_o['best_one_s']
        eujp = eu_vs_jp['eu_jp']

        print(f'Top game in {year} year was {tGame}. Message date: {date}')
        print(f'Top 5 genres in EU in {year} year were {tList}. Message date: {date}')
        print(f'Top platform(s) in NA in {year} was(were) {tPlatform}. Message date: {date}')
        print(f'Best publisher(s) in JP in {year} year was(were) {bOne}. Message date: {date}')
        print(f'Number of games with bigger sales EU VS JP in {year} year was {eujp}. Message date: {date}')

    data_frame = get_data()
    f_data = filt_data(data_frame)

    top_game = top_game_ww(f_data)
    top_genre = top_eu_genre(f_data)
    top_platforms = top_na_platforms(f_data)
    best_pub = best_publisher(f_data)
    euVSjp = eu_jp_games(f_data)

    print_data(top_game, top_genre, top_platforms, best_pub, euVSjp, my_year)

n_korkotkov_3rd_lesson = n_korkotkov_3rd_lesson()
