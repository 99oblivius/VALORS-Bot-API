CREATE MIGRATION m1lhgvoz7kcjbowjchurr6u4fd2t2sgnouehdmbzzxr6vo7azdegmq
    ONTO initial
{
  CREATE SCALAR TYPE default::MatchId EXTENDING std::sequence;
  CREATE SCALAR TYPE default::Snowflake EXTENDING std::int64;
  CREATE ABSTRACT TYPE default::Timestamped {
      CREATE PROPERTY created_at: std::datetime {
          CREATE REWRITE
              INSERT 
              USING (std::datetime_of_statement());
      };
      CREATE PROPERTY updated_at: std::datetime {
          CREATE REWRITE
              INSERT 
              USING (std::datetime_of_statement());
          CREATE REWRITE
              UPDATE 
              USING (std::datetime_of_statement());
      };
  };
  CREATE TYPE default::Guild EXTENDING default::Timestamped {
      CREATE PROPERTY guild_id: default::Snowflake {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY queue_channel_id: default::Snowflake;
      CREATE PROPERTY scores_channel_id: default::Snowflake;
      CREATE PROPERTY staff_role_id: default::Snowflake;
  };
  CREATE TYPE default::Map EXTENDING default::Timestamped {
      CREATE LINK guild: default::Guild;
      CREATE REQUIRED PROPERTY name: std::str;
      CREATE CONSTRAINT std::exclusive ON ((.guild, .name));
      CREATE REQUIRED PROPERTY enabled: std::bool {
          SET default := true;
      };
      CREATE REQUIRED PROPERTY image_url: std::str;
      CREATE PROPERTY order: std::int64;
  };
  ALTER TYPE default::Guild {
      CREATE LINK maps := (.<guild[IS default::Map]);
  };
  CREATE TYPE default::Player EXTENDING default::Timestamped {
      CREATE PROPERTY captain_volunteer: std::bool {
          SET default := false;
      };
      CREATE REQUIRED PROPERTY discord_id: default::Snowflake {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY games_played: std::int64 {
          SET default := 0;
      };
      CREATE PROPERTY games_won: std::int64 {
          SET default := 0;
      };
      CREATE PROPERTY mmr: std::float64 {
          SET default := 0;
      };
      CREATE PROPERTY rounds_won: std::int64 {
          SET default := 0;
      };
  };
  CREATE TYPE default::`Match` EXTENDING default::Timestamped {
      CREATE REQUIRED LINK guild: default::Guild;
      CREATE LINK map: default::Map;
      CREATE LINK teamA_captain: default::Player;
      CREATE MULTI LINK teamA_players: default::Player;
      CREATE LINK teamB_captain: default::Player;
      CREATE MULTI LINK teamB_players: default::Player;
      CREATE PROPERTY ended_ts: std::datetime;
      CREATE PROPERTY num: default::MatchId {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY teamA_score: std::int16;
      CREATE PROPERTY teamB_score: std::int16;
  };
  CREATE TYPE default::MapVote EXTENDING default::Timestamped {
      CREATE REQUIRED LINK map: default::Map;
      CREATE REQUIRED LINK `match`: default::`Match`;
      CREATE REQUIRED LINK player: default::Player;
      CREATE CONSTRAINT std::exclusive ON ((.`match`, .player));
  };
};
