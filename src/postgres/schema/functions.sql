CREATE OR REPLACE FUNCTION create_artist(
    "name" TEXT,
    external_urls JSONB,
    followers JSONB,
    genres TEXT[],
    href TEXT,
    images JSONB,
    popularity INT,
    type TEXT,
    uri TEXT
) RETURNS BIGINT AS
$$
DECLARE
    result BIGINT;
BEGIN
    INSERT INTO artists (name, external_urls, followers,
                         genres, href,
                         images, popularity,
                         type, uri)
    VALUES (create_artist.name, create_artist.external_urls, create_artist.followers,
            create_artist.genres, create_artist.href,
            create_artist.images, create_artist.popularity,
            create_artist.type, create_artist.uri)
    RETURNING id INTO result;
    RETURN result;
END;
$$ LANGUAGE plpgsql;