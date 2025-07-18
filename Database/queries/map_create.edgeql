with
    guild := select Guild filter Guild.guild_id = <Snowflake>$guild_id,
    name := <str>$name,
    image_url := <str>$image_url,
    new_order := select max((select Map filter Map.guild = guild).order) + 1
select (
    insert Map {
        guild := guild,
        `order` := new_order,
        name := name,
        image_url := image_url
    }
    unless conflict on (.guild, .name)
    else (
        update Map set {
            `order` := new_order,
            image_url := image_url
        }
    )
) { `order` }