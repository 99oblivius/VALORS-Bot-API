FROM geldata/gel

WORKDIR /

COPY dbschema dbschema
COPY queries queries

COPY gel.toml edgedb.toml
COPY tools tools

CMD ["server", "--runstate-dir=/tmp"]
