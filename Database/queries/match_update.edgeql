update `Match`
filter .num = <int64>$num
set {
    map := <optional Map>$map ?? .map,
    teamA_score := <optional int64>$teamA_score ?? .teamA_score,
    teamB_score := <optional int64>$teamB_score ?? .teamB_score,
    ended_ts := <optional datetime>$ended_ts ?? .ended_ts
}