from game.charts import PlayerTrendChart, PlayersAndMembersDataset

CHARTS = {
    "weekly_players": PlayerTrendChart(
        PlayersAndMembersDataset, slug='commonology', name="weekly_players", since_game=38),
    "weekly_players_4wma": PlayerTrendChart(
        PlayersAndMembersDataset, slug='commonology', name="weekly_player_4wma", since_game=38, agg_period=4)
}
