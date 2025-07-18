with
    guild := select Guild filter Guild.guild_id = <Snowflake>$guild_id,
    name := <str>$name
update Map
filter .guild = guild and .name = name
set {
    enabled := false
}