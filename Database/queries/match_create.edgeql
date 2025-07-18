select (
    insert `Match` {
        guild := <Guild>$guild
    }
) { num }