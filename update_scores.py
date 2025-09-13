import os
import dotenv
from pathlib import Path
import csv
import json
import sqlite3
from datetime import date, datetime

from kovaaks import Kovaaks

dotenv.load_dotenv()

SCRIPT_LOCATION = Path(__file__).resolve().parent
KOVAAKS_USERNAME = os.getenv("KOVAAKS_USERNAME")
KOVAAKS_DATABASE = os.getenv("KOVAAKS_DATABASE")
DATE_FORMAT = "%Y%m%d"

# stats = Path("C:\\Program Files\\Steam\\steamapps\\common\\FPSAimTrainer\\FPSAimTrainer\\stats")

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

# main = [
#     "score",
#     "attributes"
# ]
# attribute_keys = [
#     "epoch",
#     "cm360",
#     "avgTtk",
#     "accuracyDamage"
# ]



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
        

    def _create_tables(self):
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

    def get_scenario_data(self, scenario_name: str) -> json:
        return self._kovaaks_service.scenario_by_user(scenario_name)
        
    def write_scenario_data(self, scenario_name: str, scenario_data: json) -> int:
        # Parse data
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
        # print(scoreid)

        # results = f"score: {score}\ntime: {time.strftime(DATE_FORMAT)}\nsens: {cm}\nttk: {ttk}\nacc: {acc}%"
        # print(results)

        # SCOREID   INT  PRIMARY NOT NULL
        # USERID    INT          NOT NULL
        # SCENARIO  TEXT         NOT NULL
        # TIME      INT          NOT NULL
        # SCORE     INT          NOT NULL
        # CM        REAL         NOT NULL
        # TTK       REAL         NOT NULL
        # ACC       INT          NOT NULL


        con = sqlite3.connect(self._database)
        cur = con.cursor()

        # "INSERT INTO movie VALUES(?, ?, ?)", data
        # Check if score is in DB
        res = cur.execute("SELECT COUNT(1) FROM scores WHERE scoreid=%d;" % scoreid)
        exists = res.fetchone()
        if (exists[0] != 0):
            print('\tScore already recorded: %d' % scoreid)
            con.commit()
            con.close()
            return 1
        insert_scores = "INSERT INTO scores \
(scoreid, userid, scenario, timestamp, score, cm, ttk, acc) \
VALUES (%d, %d, '%s', %d, %d, %f, %f, %d)" % (
                scoreid,
                self._userid,
                scenario_name,
                timestamp,
                score,
                cm,
                ttk,
                acc,
            )
        print(insert_scores)
        cur.execute(insert_scores)

        con.commit()
        con.close()
        return 0 

    def get_avasive_s1(self, difficulty: str):
        with open('avasive_s1.csv', mode='r') as file:
            csv_dict_reader = csv.DictReader(file)
            for row in csv_dict_reader:
                scenario_name = row[difficulty]
                scenario_data = self.get_scenario_data(scenario_name)
                
                print(scenario_name)
                if len(scenario_data) < 1:
                    print("\tNo recorded runs")
                    continue

                for data in scenario_data:
                    self.write_scenario_data(scenario_name, data)

if __name__ == "__main__":
    # get_score(KOVAAKS_USERNAME, 'beanTS')
    scribe = Scribe()
    scribe.get_avasive_s1("med")