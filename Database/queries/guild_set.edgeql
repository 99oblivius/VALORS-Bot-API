with
    guild_id := <Snowflake>$guild_id,
    scores_channel_id := <optional Snowflake>$scores_channel_id ?? <Snowflake>{},
    queue_channel_id := <optional Snowflake>$queue_channel_id ?? <Snowflake>{},
    staff_role_id := <optional Snowflake>$staff_role_id ?? <Snowflake>{}
insert Guild {
    guild_id := guild_id,
    scores_channel_id := scores_channel_id,
    queue_channel_id := queue_channel_id,
    staff_role_id := staff_role_id
}
unless conflict on .guild_id
else (
    update Guild set {
        scores_channel_id := scores_channel_id ?? .scores_channel_id,
        queue_channel_id := queue_channel_id ?? .queue_channel_id,
        staff_role_id := staff_role_id ?? .staff_role_id
    }
)