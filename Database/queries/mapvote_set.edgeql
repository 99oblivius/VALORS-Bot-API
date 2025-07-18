with
    `match` := <`Match`>$match,
    player := <Player>$player,
    map := <Map>$map
insert MapVote {
    `match` := `match`,
    player := player,
    map := map
}
unless conflict on (.`match`, .player)
else (
    update MapVote set {
        map := map
    }
)