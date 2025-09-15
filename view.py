import os
import dotenv
import csv
from pathlib import Path

import sqlite3

from datetime import datetime
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

from kovaaks import Kovaaks

dotenv.load_dotenv()

SCRIPT_LOCATION = Path(__file__).resolve().parent
KOVAAKS_USERNAME = os.getenv("KOVAAKS_USERNAME")
KOVAAKS_DATABASE = os.getenv("KOVAAKS_DATABASE")

# get all scores from one scenario
# can pull from local db or online db

class View:
    def __init__(self, database: str=KOVAAKS_DATABASE, username: str=KOVAAKS_USERNAME):
        self._database = database
        self._username = username
        self._userid = self._get_userid()



    def _get_userid(self) -> int:
        con = sqlite3.connect(self._database)
        cur = con.cursor()

        # Check if username exists
        res = cur.execute("SELECT COUNT(1) FROM users WHERE username='%s'" % self._username)
        # Create new user if not exist
        user_does_not_exist = res.fetchone()[0] == 0
        if user_does_not_exist:
           cur.execute("INSERT INTO users (userid, username) VALUES (NULL, '%s')" % self._username)
        # Get ID from 
        res = cur.execute("SELECT userid FROM users WHERE username='%s'" % self._username)
        userid = res.fetchone()[0]

        con.commit()
        con.close()

        return userid 

    def get_scenario(self, scenario_name:str) -> dict[list[int]]:
        con = sqlite3.connect(self._database)
        cur = con.cursor()

        # Check if score is in DB
        res = cur.execute("SELECT score, timestamp, cm FROM scores_local WHERE\
                           userid=%d AND\
                          scenario='%s';"\
                           % (self._userid, scenario_name))
        datum = res.fetchall()

        con.close()

        score_by_cm = defaultdict(list)
        for data in datum:
            cm = data[2]
            score = data[0]
            score_by_cm[cm].append(score)
        
        return score_by_cm
    
    def get_scenario_pb(self, scenario_name:str) -> tuple[tuple[int]]:
        con = sqlite3.connect(self._database)
        cur = con.cursor()

        # Get highest score by sensitivity (360/cm)
        res = cur.execute("SELECT cm, MAX(score) OVER (PARTITION BY cm) FROM scores\
                           WHERE userid=%d AND scenario='%s'\
                           GROUP BY cm \
                           ORDER BY cm ASC;"\
                           % (self._userid, scenario_name))
        datum = res.fetchall()

        con.close()
        
        return datum

    def plot_scenario_pb(self, scenario_name:str) -> None:
        score_by_cm = self.get_scenario_pb(scenario_name)

        x, y = map(list, zip(*score_by_cm))

        print(x)
        print(y)
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111)

        ax.plot(x, y)

        ax.set_xlabel('cm/360')
        ax.set_ylabel('Score')
        ax.set_xticks(x)
        ax.set_title(scenario_name)
        ax.legend()

        plt.show()

    def plot_scenario(self, scenario_name:str) -> None:
        score_by_cm = self.get_scenario(scenario_name)




def get_benchmark(file_name:str, difficulty: str):
    with open(file_name, mode='r') as file:
            csv_dict_reader = csv.DictReader(file)
            for row in csv_dict_reader:
                scenario_name = row[difficulty]

def plot_3d():
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    ax.set_xlabel('Date')
    ax.set_ylabel('cm/360')
    ax.set_zlabel('Score')
    ax.set_yticks(list(store_ids.values()))
    ax.set_yticklabels(list(store_ids.keys()))
    ax.set_title('Monthly Sales Trends for USA Retail Stores')
    ax.legend()

    plt.show()


def sample_plot():
    # Sample data: Months (1 to 12)
    months = np.arange(1, 13)

    # Sales data for three stores (randomly generated for example)
    store_sales = {
        'Store A': np.random.randint(2000, 5000, size=12),
        'Store B': np.random.randint(1500, 4500, size=12),
        'Store C': np.random.randint(3000, 6000, size=12)
    }

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')

    # Assign a unique y-value for each store for separation
    store_ids = {'Store A': 1, 'Store B': 2, 'Store C': 3}

    for store, sales in store_sales.items():
        y = np.full_like(months, store_ids[store])  # constant y for each store
        ax.plot(months, y, sales, label=store)

    ax.set_xlabel('Month')
    ax.set_ylabel('Store ID')
    ax.set_zlabel('Sales ($)')
    ax.set_yticks(list(store_ids.values()))
    ax.set_yticklabels(list(store_ids.keys()))
    ax.set_title('Monthly Sales Trends for USA Retail Stores')
    ax.legend()
    plt.show()

if __name__ == "__main__":
    view = View()
    view.plot_scenario_pb("FreightTrack")