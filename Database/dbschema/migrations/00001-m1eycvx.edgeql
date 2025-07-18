CREATE MIGRATION m1eycvx6mwilw7buvqhl6xzqke6hfezzqqibft7plhhln4uem4ro2q
    ONTO initial
{
  CREATE SCALAR TYPE default::Snowflake EXTENDING std::int64;
  CREATE TYPE default::Settings {
      CREATE REQUIRED PROPERTY guild_id: default::Snowflake {
          CREATE CONSTRAINT std::exclusive;
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
};
