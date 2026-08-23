DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'obrasgov_chat') THEN
        CREATE ROLE obrasgov_chat
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOREPLICATION
            NOBYPASSRLS;
    ELSE
        ALTER ROLE obrasgov_chat
            LOGIN
            NOSUPERUSER
            NOCREATEDB
            NOCREATEROLE
            NOINHERIT
            NOREPLICATION
            NOBYPASSRLS;
    END IF;
END
$$;
