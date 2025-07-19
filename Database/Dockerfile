FROM geldata/gel:7.0-alpha.1

WORKDIR /

COPY queries queries

COPY gel.toml gel.toml

EXPOSE 9956

CMD ["server", "--runstate-dir=/tmp"]