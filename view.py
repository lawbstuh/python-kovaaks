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
from scribe import Scribe

dotenv.load_dotenv()

SCRIPT_LOCATION = Path(__file__).resolve().parent

# get all scores from one scenario
# can pull from local db or online db

class View:
    def __init__(self):
        self._scribe = Scribe()

    def plot_scenario_pb(self, scenario_name:str) -> None:
        score_by_cm = self._scribe.get_scenario_pb(scenario_name)
        print(score_by_cm)

        x, y = map(list, zip(*score_by_cm))

        print(x)
        print(y)
        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111)

        ax.bar(x, y)

        ax.set_xlabel('cm/360')
        ax.set_ylabel('Score')
        ax.set_xticks(x)
        ax.set_title(scenario_name)
        # ax.legend()

        plt.show()

    def plot_scenario(self, scenario_name:str) -> None:
        score_by_cm = self._scribe.get_scenario(scenario_name)

    def plot_3d(self, scenario_name:str) -> None:
        scenario_datum = self._scribe.get_scenario(scenario_name)

        fig = plt.figure(figsize=(10, 7))
        ax = fig.add_subplot(111, projection='3d')

        len_x = len(scenario_datum.date)
        len_y = len(scenario_datum.cm)
        _x = np.arange(len_x)
        _y = np.arange(len_y)
        _xx, _yy = np.meshgrid(_x, _y)
        x, y = _xx.ravel(), _yy.ravel()

        bottom = np.array([0] * (len_x * len_y))
        width = 1
        depth = 1
        top = np.array(scenario_datum.scores)

        ax.bar3d(x, y, bottom, width, depth, top, edgecolor='black', shade=True)

        ax.set_xlabel('Date')
        ax.set_ylabel('cm/360')
        ax.set_zlabel('Score')
        # ax.set_yticks(range(len_x))
        ax.set_yticklabels(scenario_datum.date)
        # ax.set_yticks(range(len_y))
        ax.set_yticklabels(scenario_datum.cm)
        ax.set_title(scenario_name)

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
    # view.plot_3d("VT Controlsphere Intermediate S5")
    view.plot_3d("VT ww5t Intermediate S5")
    # view.plot_scenario_pb("FreightTrack")