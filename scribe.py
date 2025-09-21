import os
import dotenv
from pathlib import Path
import csv
import json
import sqlite3

import re
from datetime import datetime
from collections import defaultdict
from dataclasses import astuple, dataclass
from typing import Iterable

import numpy as np

from kovaaks import Kovaaks

dotenv.load_dotenv()

SCRIPT_LOCATION = Path(__file__).resolve().parent
KOVAAKS_USERNAME = os.getenv("KOVAAKS_USERNAME")
KOVAAKS_DATABASE = os.getenv("KOVAAKS_DATABASE")
KOVAAKS_STATS = os.getenv("KOVAAKS_STATS")

# ***IMPLEMENT LATER***
# benchmarks table

# CREATE TABLE IF NOT EXISTS users (
#     userid INTEGER PRIMARY KEY AUTOINCREMENT,
#     username TEXT NOT NULL UNIQUE
# )

# CREATE TABLE IF NOT EXISTS scores (
#     scoreid   INT  PRIMARY KEY,
#     userid    INT  NOT NULL,
#     scenario  TEXT NOT NULL,
#     timestamp INT  NOT NULL,
#     score     REAL NOT NULL,
#     cm        REAL NOT NULL,
#     ttk       REAL NOT NULL,
#     acc       INT  NOT NULL
# )


@dataclass(frozen=True)
class ScenarioData:
    '''
    External class with scenario scores and data
    '''
    scenario_name:str
    timestamp:int
    score:float
    cm:float
    ttk:float
    acc:int

    @property
    def ymd(self) -> int:
        date = datetime.fromtimestamp(self.timestamp / 1000)
        return int('%04d%02d%02d' % (date.year, date.month, date.day))

@dataclass(frozen=True)
class _ScenarioData(ScenarioData):
    '''
    Internal dataclass for inserting data into database.
    '''
    scoreid:int
    userid:int

class MultipleInitException(Exception):
    pass

class ScenarioDatum:
    def __init__(self, datum:Iterable[ScenarioData]):
        self._datum:tuple[ScenarioData] = tuple(datum)
        self._datum_len = len(self._datum)
        self._cm:list[float] # = [i for i in range(20, 90, 10)]
        self._date:list[float]

        self._scores:list[float]

        self._bin_by_day()
    
        # Create a n*m array
        # n = len(cm)
        # m = len(date)
        # cm = unique sensitivities
        # date = unique dates
        # TODO: extrapolate missing dates / fill with zeros

    def __len__(self):
        return self._datum_len

    @property
    def datum(self):
        return self._datum
    
    @property
    def cm(self):
        return self._cm

    @property
    def date(self):
        return self._date
    
    @property
    def scores(self):
        return self._scores

    # day, cm, score
    # every date there is, we need the range of scores

    def _bin_by_day(self):
        # if (self._cm and self._datum_index_by_day):
        #     raise MultipleInitException("ScenarioDatum initialized more than once")

        cm = set()
        date = set()
        # date_and_index = defaultdict(list)

        for i in range(self._datum_len):
            data = self._datum[i]

            cm.add(data.cm)
            date.add(data.ymd)

            # data_date = data.ymd
            # date_and_index[data_date].append(i)

        self._cm = sorted(list(cm))
        self._date = sorted(list(date))

        len_cm = len(cm)
        len_date = len(date)
        scores = [0] * (len_cm * len_date)

        for data_index in range(self._datum_len):
            data = self._datum[data_index]

            i = self._cm.index(data.cm)
            j = self._date.index(data.ymd)
            score_index = j * i + j
            scores[score_index] = max(scores[score_index], data.score)

        self._scores = scores
            


    def get_sens(self) -> list[int]:
        if not self._cm:
            self._cm = set(map(lambda data: data.cm), self._datum)
        return self._cm


class Scribe:
    def __init__(
            self,
            database: str=KOVAAKS_DATABASE,
            username: str=KOVAAKS_USERNAME
        ):
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
        # user_table = """
        #     CREATE TABLE IF NOT EXISTS users (
        #     userid INTEGER PRIMARY KEY AUTOINCREMENT,
        #     username TEXT NOT NULL UNIQUE
        # );"""
        # cur.execute(user_table)
        # res = cur.execute("SELECT name FROM sqlite_master WHERE name='scores'")
        # print(res.fetchone())

        # Create scores table
        # scores_table = """
        # CREATE TABLE IF NOT EXISTS scores (
        #     scoreid   INT  PRIMARY KEY,
        #     userid    INT  NOT NULL,
        #     scenario  TEXT NOT NULL,
        #     timestamp INT  NOT NULL,
        #     score     REAL NOT NULL,
        #     cm        REAL NOT NULL,
        #     ttk       REAL NOT NULL,
        #     acc       INT  NOT NULL);"""
        # res = cur.execute(scores_table)
        # print(res.fetchone())

        # Create offline scores
        # scores_table = """CREATE TABLE IF NOT EXISTS scores_local (
        #     scoreid   INT  PRIMARY KEY,
        #     userid    INT  NOT NULL,
        #     scenario  TEXT NOT NULL,
        #     timestamp INT  NOT NULL,
        #     score     REAL NOT NULL,
        #     cm        REAL NOT NULL,
        #     ttk       REAL NOT NULL,
        #     acc       INT  NOT NULL);"""
        # cur.execute(scores_table)
        # res = cur.execute("SELECT name FROM sqlite_master WHERE name='scores_local'")
        # print(res.fetchone())

        con.commit()
        con.close()

    def get_scenario(self, scenario_name:str, local=True) -> ScenarioDatum:
        con = sqlite3.connect(self._database)
        cur = con.cursor()

        if local:
        # Check if score is in DB
            res = cur.execute("SELECT timestamp, score, cm, ttk, acc\
                            FROM scores_local\
                            WHERE userid=%d AND scenario='%s'\
                            ORDER BY cm ASC, timestamp ASC;"\
                            % (self._userid, scenario_name))
        else:
            res = cur.execute("SELECT timestamp, score, cm, ttk, acc\
                            FROM scores\
                            WHERE userid=%d AND scenario='%s'\
                            ORDER BY cm ASC, timestamp ASC;"\
                            % (self._userid, scenario_name))
        datum = res.fetchall()

        con.close()
        
        data_map = map(lambda data:ScenarioData(scenario_name, *data), datum)
        return ScenarioDatum(data_map)
    
    def get_scenario_pb(self, scenario_name:str, local=True) -> tuple[tuple[int]]:
        con = sqlite3.connect(self._database)
        cur = con.cursor()

        # Get highest score by sensitivity (360/cm)
        if local:
            res = cur.execute("SELECT cm, MAX(score)\
                            OVER (PARTITION BY cm)\
                            FROM scores_local\
                            WHERE userid=%d AND scenario='%s'\
                            GROUP BY cm \
                            ORDER BY cm ASC;"\
                            % (self._userid, scenario_name))
        else:
            res = cur.execute("SELECT cm, MAX(score)\
                            OVER (PARTITION BY cm)\
                            FROM scores\
                            WHERE userid=%d AND scenario='%s'\
                            GROUP BY cm \
                            ORDER BY cm ASC;"\
                            % (self._userid, scenario_name))
        datum = res.fetchall()

        con.close()
        
        return datum

    def get_scenario_data_from_api(self, scenario_name: str, verbose=False) -> list[_ScenarioData]:
        if verbose: print("Updating: %s" % scenario_data)

        scenario_data_json = self._kovaaks_service.scenario_by_user(scenario_name)
        len_data = len(scenario_data_json)
        if len_data == 0:
            return []
        scenario_datum = [None] * len_data
        for i in range(len_data):
            scenario_data = scenario_data_json[i]
            score       = float(scenario_data["score"])
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
            
            scenario_datum[i] = _ScenarioData(
                scoreid=scoreid,
                userid=self._userid,
                scenario_name=scenario_name,
                timestamp=timestamp,
                score=score,
                cm=cm,
                ttk=ttk,
                acc=acc,
            )
        if verbose: print(astuple(scenario_datum[0]))
        return scenario_datum
            
    def get_scenario_data_from_local(self, scenario_name: str, verbose=False) -> list[_ScenarioData]:
        stats_path = Path(KOVAAKS_STATS)
        if verbose: print(stats_path)
        stats = stats_path.glob('*%s - Challenge - *.csv' % scenario_name)
        scenario_datum = []
        for stat in stats:
            if verbose: print(stat.stem)
            # convert date in title to time stamp
            # only take files that have a later timestamp than last update
            # match = re.split(r' - Challenge - | Stats', stat.stem)
            match = re.findall(r'(\d{4})\.(\d{2})\.(\d{2})-(\d{2})\.(\d{2})\.(\d{2})', stat.stem)

            date_match = match[0]
            scoreid = int(''.join(date_match) + str(self._userid))
            date = datetime(
                year=int(date_match[0]),
                month=int(date_match[1]),
                day=int(date_match[2]),
                hour=int(date_match[3]),
                minute=int(date_match[4]),
                second=int(date_match[5])
            )
            timestamp = int(date.timestamp() * 1000)
            
            with open(stat, 'r') as file:
                csv_reader = csv.reader(file)
                csv_list = list(csv_reader)
                score       = float(csv_list[-26][1])
                cm          = float(csv_list[-12][1])
                ttk         = float(csv_list[-39][1])
                hit         = int(csv_list[-35][1])
                miss        = int(csv_list[-34][1])
                acc = hit / (hit + miss)
            
            
            scenario_data = _ScenarioData(
                scoreid=scoreid,
                userid=self._userid,
                scenario_name=scenario_name,
                timestamp=timestamp,
                score=score,
                cm=cm,
                ttk=ttk,
                acc=acc,
            )

            if verbose:
                print("scoreid:", scoreid)
                print("timestamp:", timestamp)
                print(date, date_match)
                print(round(acc * 10e4))
                print(astuple(scenario_data))
            scenario_datum.append(scenario_data)

        return scenario_datum

    def write_scenario_data_from_api(self, scenario_data: _ScenarioData, verbose=False) -> int:
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
        
        # Insert scores from api
        insert_scores = "INSERT INTO scores \
(scoreid, userid, scenario, timestamp, score, cm, ttk, acc) \
VALUES (%d, %d, '%s', %d, %d, %f, %f, %d)" % astuple(scenario_data)
        print(insert_scores)
        cur.execute(insert_scores)

        con.commit()
        con.close()
        return 0 
    
    def write_scenario_data_from_local(self, scenario_data: _ScenarioData, verbose=False) -> int:
        con = sqlite3.connect(self._database)
        cur = con.cursor()

        # Check if score is in DB
        res = cur.execute("SELECT COUNT(1) FROM scores_local WHERE scoreid=%d;" % scenario_data.scoreid)
        exists = res.fetchone()
        if (exists[0] != 0):
            print('\tScore already recorded: %d' % scenario_data.scoreid)
            con.commit()
            con.close()
            return 1
        
        # Insert scores local
        insert_scores = "INSERT INTO scores_local \
(scoreid, userid, scenario, timestamp, score, cm, ttk, acc) \
VALUES (%d, %d, '%s', %d, %d, %f, %f, %d)" % astuple(scenario_data)
        if verbose: print(insert_scores)
        cur.execute(insert_scores)

        con.commit()
        con.close()
        return 0 

    def record_benchmark(self, file_name:str, difficulty: str, local=True) -> None:
        print('Recording scores from %s' % 'Kovaaks API' if local else 'local files')
        
        with open(file_name, mode='r') as file:
            csv_dict_reader = csv.DictReader(file)
            for row in csv_dict_reader:
                scenario_name = row[difficulty]
                print(scenario_name)

                if local: # Get scenario data from local
                    scenario_datum = self.get_scenario_data_from_local(scenario_name)

                    if len(scenario_datum) < 1:
                        print("\tNo recorded runs")
                        continue

                    for scenario_data in scenario_datum:
                        exit_code = self.write_scenario_data_from_local(scenario_data)
                        # Exit once a score is already inserted
                        if exit_code == 1:
                            break
                else:
                    try:
                        scenario_datum = self.get_scenario_data_from_api(scenario_name)
                    except(Exception) as excpt:
                        print("\tGet failed:\n\n\t%s" % str(excpt))
                        return

                    
                    if len(scenario_datum) < 1:
                        print("\tNo recorded runs")
                        continue

                    for scenario_data in scenario_datum:
                        exit_code = self.write_scenario_data_from_api(scenario_data, True)
                        # Exit once a score is already inserted
                        if exit_code == 1:
                            break


    def _test_db(self):
        con = sqlite3.connect(self._database)
        cur = con.cursor()

        # Check if score is in DB
        res = cur.execute("SELECT * FROM scores_local;")
        for r in res.fetchall():
            print(r)
        
        con.close()


if __name__ == "__main__":
    # get_score(KOVAAKS_USERNAME, 'beanTS')
    scribe = Scribe()
    # scribe.record_benchmark("avasive_s1.csv","med",local=False)
    # scribe.record_benchmark("avasive_s1.csv","hard",local=False)
    # scribe.record_benchmark("voltaic_s5.csv","easy",local=False)
    # scribe.record_benchmark("voltaic_s5.csv","med",local=False)
    # scribe.record_benchmark("voltaic_s5.csv","hard",local=False)
    # scribe.get_scenario_data_from_api("FreightTrack")
    # scribe.get_scenario_data_from_local("VT ControlTS Intermediate S5", True)
    scribe.record_benchmark("voltaic_s5.csv", "hard")
    scribe.record_benchmark("avasive_s1.csv","med")
