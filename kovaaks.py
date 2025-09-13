import requests, json
import itertools
from base64 import b64encode
from urllib.parse import quote

import os
import dotenv

from models import *
from endpoints import *

AUTH_SESSION = False

class Kovaaks:
    def __init__(self):
        self._username: None | str = None
        self._password: None | str = None
        self._auth = {}
        self.session = requests.Session()
    
    @staticmethod
    def from_login(username: str=None, password: str=None):
        kovaaks = Kovaaks()
        kovaaks._username = username
        kovaaks._password = password
        return kovaaks

    def login(self):
        if self._username is None or self._password is None:
            raise NoCredentials("You did not pass your username and/or password to the constructor.")
        # yes this is how they do their authentication
        encoded_pair = b64encode(f"{self._username}:{self._password}".encode()).decode()
        resp = self.session.post("https://kovaaks.com/auth/webapp/login", headers={"authorization": "Basic %s" % encoded_pair})
        resp.raise_for_status()
        self._auth = resp.json()
        self.session.headers.update({"authorization": "Bearer " + self._auth["auth"]["jwt"]})

    def _verify_token(self):
        resp = self.session.get(VERIFY_TOKEN)
        resp.raise_for_status()
        return resp.json()["success"]

    def _endpoint_for(self, f: LeaderboardFilter):
        return {
            LeaderboardFilter.GLOBAL: SCENARIO_GLOBAL_LEADERBOARD,
            LeaderboardFilter.FRIENDS: SCENARIO_FRIENDS_LEADERBOARD,
            LeaderboardFilter.VIP: SCENARIO_VIP_LEADERBOARD,
            LeaderboardFilter.MY_POSITION: SCENARIO_ADJ_LEADERBOARD
        }.get(f)

    def scenario_leaderboard(self, id: int, start_page=0, per_page=10, max_page=-1, by_page=True, filter_: LeaderboardFilter=LeaderboardFilter.GLOBAL) -> list[Score]:
        # todo: add username filtering
        endpoint = self._endpoint_for(filter_)
        for offset in (itertools.count() if max_page == -1 else range(max_page)):
            resp = self.session.get(endpoint % (id, start_page + offset, per_page))
            resp.raise_for_status()
            print(json.dumps(resp.json(), indent=2))
            result = [Score(
                entry.get("steamId"),
                entry.get("score"),
                entry.get("rank"),
                entry.get("steamAccountName"),
                entry.get("kovaaksPlusActive"),
                entry.get("attributes", {}).get("fov"),
                entry.get("attributes", {}).get("hash"),
                entry.get("attributes", {}).get("cm360"),
                entry.get("attributes", {}).get("epoch"),
                entry.get("attributes", {}).get("kills"),
                entry.get("attributes", {}).get("avgFps"),
                entry.get("attributes", {}).get("avgTtk"),
                entry.get("attributes", {}).get("fovScale"),
                entry.get("attributes", {}).get("vertSens"),
                entry.get("attributes", {}).get("horizSens"),
                entry.get("attributes", {}).get("resolution"),
                entry.get("attributes", {}).get("sensScale"),
                entry.get("attributes", {}).get("accuracyDamage"),
                entry.get("attributes", {}).get("challengeStart"),
                entry.get("attributes", {}).get("scenarioVersion"),
                entry.get("attributes", {}).get("clientBuildVersion"),
                entry.get("webappUsername"),
            ) for entry in resp.json()["data"]]

            if by_page: yield result
            else:
                for x in result: yield x
    
    def scenario_count(self) -> int:
        resp = self.session.get(POPULAR_SCENARIOS % (0, 0))
        resp.raise_for_status()
        return resp.json()["total"]
    
    def scenario_search(self, query: str=None, start_page=0, per_page=10, max_page=-1, by_page=True) -> list[Scenario]:
        for offset in (itertools.count() if max_page == -1 else range(max_page)):
            if query is None:
                resp = self.session.get(POPULAR_SCENARIOS % (start_page + offset, per_page))
            else:
                resp = self.session.get(POPULAR_SCENARIOS_SEARCH % (start_page + offset, per_page, query))
            resp.raise_for_status()
            
            result = [Scenario(
                entry.get("rank"),
                entry.get("leaderboardId"),
                entry.get("scenarioName"),
                entry.get("scenario", {}).get("aimType"),
                entry.get("scenario", {}).get("authors"),
                entry.get("scenario", {}).get("description"),
                entry.get("counts", {}).get("plays"),
                entry.get("counts", {}).get("entries"),
            ) for entry in resp.json()["data"]]

            if by_page: yield result
            else:
                for x in result: yield x

    def popular_playlists(self, start_page=0, per_page=10, max_page=-1, by_page=True) -> list[Playlist]:
        for offset in (itertools.count() if max_page == -1 else range(max_page)):
            resp = self.session.get(POPULAR_PLAYLISTS % (start_page + offset, per_page))
            resp.raise_for_status()
            result = [
                Playlist(
                entry.get("playlistName"),
                entry.get("playlistCode"),
                entry.get("playlistId"),
                entry.get("playlistJson", {}).get("authorName"),
                entry.get("playlistJson", {}).get("description"),
                [
                    PlaylistScenario(
                        scen.get("scenarioName"),
                        scen.get("playCount")
                    ) for scen in entry.get("playlistJson", {}).get("scenarioList", [])
                ],
                entry.get("playlistJson", {}).get("authorSteamId"),
                entry.get("subscribers"),
                entry.get("webappUsername"),
                entry.get("steamAccountName"),
            ) for entry in resp.json()["data"]]
            if by_page: yield result
            else:
                for x in result: yield x

    def player_search(self, query: str) -> list[PlayerSearchResult]:
        if len(query) < 3: raise ValueError("You can only search for usernames which are 3 characters or more in length.")
        resp = self.session.get(PLAYER_SEARCH % quote(query))
        resp.raise_for_status()
        return [PlayerSearchResult(*x.values()) for x in resp.json()]
    
    def scenario_by_user(self, scenario_name: str) -> json:
        scenario_by_user = f"https://kovaaks.com/webapp-backend/user/scenario/last-scores/by-name?username={self._username}&scenarioName={scenario_name}"
        response = self.session.get(scenario_by_user)
        response.raise_for_status()
        return response.json()

if __name__ == "__main__":
    beanTSId=2648

    if AUTH_SESSION:
        dotenv.load_dotenv()
        username = os.getenv("KOVAAKS_USERNAME")
        password = os.getenv("KOVAAKS_PASSWORD")
        kvk = Kovaaks.from_login(
            username=username,
            password=password)
        kvk.login()
        if not kvk._verify_token():
            raise LoginError("Invalid credentials.")
        print(f"Login successful: {username}")
    else:
        kvk = Kovaaks()

    # gets user data only
    # response = kvk.session.get("https://kovaaks.com/webapp-backend/user/search?username=lawbstuh")

    # response = kvk.session.get(f"https://kovaaks.com/webapp-backend/leaderboard/scores/global?leaderboardId={2}&page={0}&max={5}")
    scenario_by_user = f"https://kovaaks.com/webapp-backend/user/scenario/last-scores/by-name?username=lawbstuh&scenarioName=beanTS"
    response = kvk.session.get(scenario_by_user)
    response.raise_for_status()
    res = response.json()
    print(len(res))
    print(json.dumps(res, indent=2))

    # good for leaderboard stuff
    # need to use local for more in depth analysis
    # can only pull 9 last played
    # website receives 10 last played but api call receives only 9