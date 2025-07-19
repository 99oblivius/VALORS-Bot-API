select (
    insert `Match` {
        guild := select Guild filter Guild.guild_id = <Snowflake>$guild_id
    }
) { num }