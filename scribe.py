import os
import dotenv
from pathlib import Path
import csv
import json
import sqlite3
from datetime import datetime
from dataclasses import astuple, dataclass

from kovaaks import Kovaaks

dotenv.load_dotenv()

SCRIPT_LOCATION = Path(__file__).resolve().parent
KOVAAKS_USERNAME = os.getenv("KOVAAKS_USERNAME")
KOVAAKS_DATABASE = os.getenv("KOVAAKS_DATABASE")
KOVAAKS_STATS = os.getenv("KOVAAKS_STATS")

# update modes: all, by difficulty, by specific?
# store each score by date
# store 2 tables, scenario and benchmarks
# updating scores oupdates scenario

# user table
# schema USERS
# USERID   INT  PRIMARY NOT NULL
# USERNAME TEXT         NOT NULL

# scenario table
# scenario name, date (Ymd), score, accuracy, kps, cm360
# schema SCENARIO
# SCOREID   INT  PRIMARY NOT NULL
# USERID    INT          NOT NULL
# SCENARIO  TEXT         NOT NULL
# TIME      INT          NOT NULL
# SCORE     INT          NOT NULL
# CM        INT          NOT NULL
# TTK       INT          NOT NULL
# ACC       INT          NOT NULL

# ***IMPLEMENT LATER***
# benchmarks table

@dataclass
class ScenarioData:
    scoreid:int
    userid:int
    scenario_name:str
    timestamp:int
    score:int
    cm:float
    ttk:float
    acc:int

class Scribe:
    def __init__(self, database: str=KOVAAKS_DATABASE, username: str=KOVAAKS_USERNAME):
        self._database = database
        self._username = username
        self._kovaaks_service = Kovaaks.from_login(username)
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

    def _create_tables(self) -> None:
        con = sqlite3.connect(self._database)
        cur = con.cursor()

        # Create users table
        user_table = """
            CREATE TABLE IF NOT EXISTS users (
            userid INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE
        );"""
        cur.execute(user_table)
        res = cur.execute("SELECT name FROM sqlite_master WHERE name='scores'")
        print(res.fetchone())

        # Create scores table
        scores_table = """
        CREATE TABLE IF NOT EXISTS scores (
            scoreid   INT  PRIMARY KEY,
            userid    INT  NOT NULL,
            scenario  TEXT NOT NULL,
            timestamp INT  NOT NULL,
            score     INT  NOT NULL,
            cm        REAL NOT NULL,
            ttk       REAL NOT NULL,
            acc       INT  NOT NULL
        );"""
        cur.execute(scores_table)
        res = cur.execute("SELECT name FROM sqlite_master WHERE name='users'")
        print(res.fetchone())

        con.commit()
        con.close()

    def get_scenario_data_from_api(self, scenario_name: str, verbose=False) -> list[ScenarioData]:
        if verbose: print("Updating: %s" % scenario_data)

        scenario_data_json = self._kovaaks_service.scenario_by_user(scenario_name)
        len_data = len(scenario_data_json)
        if len_data == 0:
            return []
        scenario_datum = [None] * len_data
        for i in range(len_data):
            scenario_data = scenario_data_json[i]
            score       = int(scenario_data["score"])
            attributes  = scenario_data["attributes"]
            timestamp   = int(attributes["epoch"])
            time        = datetime.fromtimestamp(timestamp / 1000)
            cm          = float(attributes["cm360"])
            ttk         = float(attributes["avgTtk"])
            acc         = int(attributes["accuracyDamage"]) / 1000
            scoreid     = int("%04d%02d%02d%02d%02d%02d%d" % (
                    time.year,
                    time.month,
                    time.day,
                    time.hour,
                    time.minute,
                    time.second,
                    self._userid,
                ))
            
            scenario_datum[i] = ScenarioData(
                scoreid,
                self._userid,
                scenario_name,
                timestamp,
                score,
                cm,
                ttk,
                acc,
            )
        return scenario_datum
            
    def get_scenario_data_from_local(self, scenario_name: str) -> list[ScenarioData]:
        stats_path = Path(KOVAAKS_STATS)
        print(stats_path)
        stats = stats_path.glob('*%s - *.csv' % scenario_name)
        for stat in stats:
            print(stat.stem)
            # convert date in title to time stamp
            # only take files that have a later timestamp than last update
            with open(stat, 'r') as file:
                csv_dict_reader = csv.DictReader(file)
                for row in csv_dict_reader:
                    print(row)
                return []


    

    def write_scenario_data(self, scenario_data: ScenarioData, verbose=False) -> int:
        con = sqlite3.connect(self._database)
        cur = con.cursor()

        # Check if score is in DB
        res = cur.execute("SELECT COUNT(1) FROM scores WHERE scoreid=%d;" % scenario_data.scoreid)
        exists = res.fetchone()
        if (exists[0] != 0):
            print('\tScore already recorded: %d' % scenario_data.scoreid)
            con.commit()
            con.close()
            return 1
        insert_scores = "INSERT INTO scores \
(scoreid, userid, scenario, timestamp, score, cm, ttk, acc) \
VALUES (%d, %d, '%s', %d, %d, %f, %f, %d)" % astuple(scenario_data)
        print(insert_scores)
        cur.execute(insert_scores)

        con.commit()
        con.close()
        return 0 

    def record_online_benchmark(self, file_name:str, difficulty: str):
        with open(file_name, mode='r') as file:
            csv_dict_reader = csv.DictReader(file)
            for row in csv_dict_reader:
                scenario_name = row[difficulty]
                scenario_datum = self.get_scenario_data_from_api(scenario_name)
                
                print(scenario_name)
                if len(scenario_datum) < 1:
                    print("\tNo recorded runs")
                    continue

                for scenario_data in scenario_datum:
                    exit_code = self.write_scenario_data(scenario_data)
                    # Exit once a score is already inserted
                    if exit_code == 1:
                        break

if __name__ == "__main__":
    # get_score(KOVAAKS_USERNAME, 'beanTS')
    scribe = Scribe()
    scribe.record_online_benchmark("avasive_s1.csv","med")
    # scribe.record_online_benchmark("avasive_s1.csv","hard")
    # scribe.record_online_benchmark("voltaic_s5.csv","hard")
    # scribe.get_scenario_data_from_api("FreightTrack")
    # scribe.get_scenario_data_from_local("VT Controlsphere Intermediate S5")
