CREATE MIGRATION m1kke5uyowo44cpam4ygvsjjxbgtfqpxedeeri6vzjlg4abtuyxbia
    ONTO m1eycvx6mwilw7buvqhl6xzqke6hfezzqqibft7plhhln4uem4ro2q
{
  CREATE SCALAR TYPE default::MapId EXTENDING std::sequence;
  CREATE SCALAR TYPE default::MatchId EXTENDING std::sequence;
  ALTER TYPE default::Settings {
      DROP PROPERTY guild_id;
  };
  ALTER TYPE default::Settings RENAME TO default::Guild;
  ALTER TYPE default::Guild {
      CREATE PROPERTY guild_id: default::Snowflake {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY queue_channel_id: default::Snowflake;
      CREATE PROPERTY scores_channel_id: default::Snowflake;
      CREATE PROPERTY staff_role_id: default::Snowflake;
  };
  CREATE TYPE default::Map {
      CREATE REQUIRED LINK guild: default::Guild;
      CREATE PROPERTY created_at: std::datetime {
          CREATE REWRITE
              INSERT 
              USING (std::datetime_of_statement());
      };
      CREATE REQUIRED PROPERTY enabled: std::bool {
          SET default := true;
      };
      CREATE REQUIRED PROPERTY image_url: std::str;
      CREATE REQUIRED PROPERTY name: std::str;
      CREATE PROPERTY num: default::MapId;
      CREATE PROPERTY updated_at: std::datetime {
          CREATE REWRITE
              INSERT 
              USING (std::datetime_of_statement());
          CREATE REWRITE
              UPDATE 
              USING (std::datetime_of_statement());
      };
  };
  CREATE TYPE default::Player {
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
      CREATE PROPERTY updated_at: std::datetime {
          CREATE REWRITE
              INSERT 
              USING (std::datetime_of_statement());
          CREATE REWRITE
              UPDATE 
              USING (std::datetime_of_statement());
      };
  };
  CREATE TYPE default::`Match` {
      CREATE REQUIRED LINK guild: default::Guild;
      CREATE MULTI LINK teamA_players: default::Player;
      CREATE MULTI LINK teamB_players: default::Player;
      CREATE PROPERTY _id: default::MatchId {
          CREATE CONSTRAINT std::exclusive;
      };
      CREATE PROPERTY created_at: std::datetime {
          CREATE REWRITE
              INSERT 
              USING (std::datetime_of_statement());
      };
      CREATE PROPERTY ended_ts: std::datetime;
      CREATE PROPERTY map_id: default::MapId;
      CREATE PROPERTY teamA_score: std::int64;
      CREATE PROPERTY teamB_score: std::int64;
  };
  CREATE TYPE default::MapVote {
      CREATE REQUIRED LINK map: default::Map;
      CREATE REQUIRED LINK `match`: default::`Match`;
      CREATE REQUIRED LINK player: default::Player;
      CREATE CONSTRAINT std::exclusive ON ((.`match`, .player));
      CREATE PROPERTY updated_at: std::datetime {
          CREATE REWRITE
              INSERT 
              USING (std::datetime_of_statement());
          CREATE REWRITE
              UPDATE 
              USING (std::datetime_of_statement());
      };
  };
};
