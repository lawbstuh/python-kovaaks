KOVAAKS_BACKEND = "https://kovaaks.com/webapp-backend/"
POPULAR_SCENARIOS = KOVAAKS_BACKEND+"scenario/popular?page=%d&max=%d" # (start_page, per_page)
POPULAR_SCENARIOS_SEARCH = KOVAAKS_BACKEND+"scenario/popular?page=%d&max=%d&scenarioNameSearch=%s"
POPULAR_PLAYLISTS = KOVAAKS_BACKEND+"playlist/popular?page=%d&max=%d" # (start_page, per_page)
SCENARIO_GLOBAL_LEADERBOARD = KOVAAKS_BACKEND+"leaderboard/scores/global?leaderboardId=%d&page=%d&max=%d" # (id, start_page, per_page)
SCENARIO_FRIENDS_LEADERBOARD = KOVAAKS_BACKEND+"leaderboard/scores/friends?leaderboardId=%d&page=%d&max=%d" # (id, start_page, per_page)
SCENARIO_VIP_LEADERBOARD = KOVAAKS_BACKEND+"leaderboard/scores/vip?leaderboardId=%d&page=%d&max=%d" # (id, start_page, per_page)
SCENARIO_ADJ_LEADERBOARD = KOVAAKS_BACKEND+"leaderboard/scores/adjacent?leaderboardId=%d&page=%d&max=%d" # (id, start_page, per_page)
PLAYER_SEARCH = KOVAAKS_BACKEND+"user/search?username=%s" # (username,)

PROFILE = "https://kovaaks.com/kovaaks/profile?username=%s" # (username,)
VERIFY_TOKEN = "https://kovaaks.com/auth/webapp/verify-token"