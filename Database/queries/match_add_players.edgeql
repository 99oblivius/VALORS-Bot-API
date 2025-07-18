update `Match`
filter .num = <int64>$num
set {
    teamA_players += (
        select Player
        filter contains(<array<Snowflake>>$teamA_ids, Player.discord_id)
    ),
    teamB_players += (
        select Player
        filter contains(<array<Snowflake>>$teamB_ids, Player.discord_id)
    )
}