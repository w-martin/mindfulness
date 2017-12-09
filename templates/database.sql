--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.10
-- Dumped by pg_dump version 9.5.10

-- Started on 2017-11-30 20:27:41 GMT

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE mindfulness;
--
-- TOC entry 2188 (class 1262 OID 16460)
-- Name: mindfulness; Type: DATABASE; Schema: -; Owner: mindfulness
--

CREATE DATABASE mindfulness WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_GB.UTF-8' LC_CTYPE = 'en_GB.UTF-8';

CREATE USER mindfulness WITH PASSWORD 'mindfulness';

ALTER DATABASE mindfulness OWNER TO mindfulness;

\connect mindfulness

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 1 (class 3079 OID 12393)
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- TOC entry 2191 (class 0 OID 0)
-- Dependencies: 1
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- TOC entry 181 (class 1259 OID 16461)
-- Name: out_of_office; Type: TABLE; Schema: public; Owner: mindfulness
--

CREATE TABLE out_of_office (
    ooo_id integer NOT NULL,
    user_id integer NOT NULL,
    "to" date NOT NULL,
    "from" date NOT NULL
);


ALTER TABLE out_of_office OWNER TO mindfulness;

--
-- TOC entry 182 (class 1259 OID 16464)
-- Name: out_of_office_ooo_id_seq; Type: SEQUENCE; Schema: public; Owner: mindfulness
--

CREATE SEQUENCE out_of_office_ooo_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE out_of_office_ooo_id_seq OWNER TO mindfulness;

--
-- TOC entry 2192 (class 0 OID 0)
-- Dependencies: 182
-- Name: out_of_office_ooo_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mindfulness
--

ALTER SEQUENCE out_of_office_ooo_id_seq OWNED BY out_of_office.ooo_id;


--
-- TOC entry 183 (class 1259 OID 16466)
-- Name: played; Type: TABLE; Schema: public; Owner: mindfulness
--

CREATE TABLE played (
    play_id integer NOT NULL,
    song_id integer,
    date date
);


ALTER TABLE played OWNER TO mindfulness;

--
-- TOC entry 184 (class 1259 OID 16469)
-- Name: played_play_id_seq; Type: SEQUENCE; Schema: public; Owner: mindfulness
--

CREATE SEQUENCE played_play_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE played_play_id_seq OWNER TO mindfulness;

--
-- TOC entry 2193 (class 0 OID 0)
-- Dependencies: 184
-- Name: played_play_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mindfulness
--

ALTER SEQUENCE played_play_id_seq OWNED BY played.play_id;


--
-- TOC entry 185 (class 1259 OID 16471)
-- Name: songs; Type: TABLE; Schema: public; Owner: mindfulness
--

CREATE TABLE songs (
    song_id integer NOT NULL,
    title text,
    url text,
    day integer,
    user_id integer,
    month integer
);


ALTER TABLE songs OWNER TO mindfulness;

--
-- TOC entry 186 (class 1259 OID 16477)
-- Name: songs_song_id_seq; Type: SEQUENCE; Schema: public; Owner: mindfulness
--

CREATE SEQUENCE songs_song_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE songs_song_id_seq OWNER TO mindfulness;

--
-- TOC entry 2194 (class 0 OID 0)
-- Dependencies: 186
-- Name: songs_song_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mindfulness
--

ALTER SEQUENCE songs_song_id_seq OWNED BY songs.song_id;


--
-- TOC entry 187 (class 1259 OID 16479)
-- Name: users; Type: TABLE; Schema: public; Owner: mindfulness
--

CREATE TABLE users (
    name text,
    user_id integer NOT NULL,
    admin boolean DEFAULT false NOT NULL,
    password text
);


ALTER TABLE users OWNER TO mindfulness;

--
-- TOC entry 188 (class 1259 OID 16486)
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: mindfulness
--

CREATE SEQUENCE users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE users_user_id_seq OWNER TO mindfulness;

--
-- TOC entry 2195 (class 0 OID 0)
-- Dependencies: 188
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mindfulness
--

ALTER SEQUENCE users_user_id_seq OWNED BY users.user_id;


--
-- TOC entry 189 (class 1259 OID 16488)
-- Name: votes; Type: TABLE; Schema: public; Owner: mindfulness
--

CREATE TABLE votes (
    vote_id integer NOT NULL,
    song_id integer,
    user_id integer,
    vote bit(1)
);


ALTER TABLE votes OWNER TO mindfulness;

--
-- TOC entry 190 (class 1259 OID 16491)
-- Name: votes_vote_id_seq; Type: SEQUENCE; Schema: public; Owner: mindfulness
--

CREATE SEQUENCE votes_vote_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE votes_vote_id_seq OWNER TO mindfulness;

--
-- TOC entry 2196 (class 0 OID 0)
-- Dependencies: 190
-- Name: votes_vote_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: mindfulness
--

ALTER SEQUENCE votes_vote_id_seq OWNED BY votes.vote_id;


--
-- TOC entry 2043 (class 2604 OID 16493)
-- Name: ooo_id; Type: DEFAULT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY out_of_office ALTER COLUMN ooo_id SET DEFAULT nextval('out_of_office_ooo_id_seq'::regclass);


--
-- TOC entry 2044 (class 2604 OID 16494)
-- Name: play_id; Type: DEFAULT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY played ALTER COLUMN play_id SET DEFAULT nextval('played_play_id_seq'::regclass);


--
-- TOC entry 2045 (class 2604 OID 16495)
-- Name: song_id; Type: DEFAULT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY songs ALTER COLUMN song_id SET DEFAULT nextval('songs_song_id_seq'::regclass);


--
-- TOC entry 2047 (class 2604 OID 16496)
-- Name: user_id; Type: DEFAULT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY users ALTER COLUMN user_id SET DEFAULT nextval('users_user_id_seq'::regclass);


--
-- TOC entry 2048 (class 2604 OID 16497)
-- Name: vote_id; Type: DEFAULT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY votes ALTER COLUMN vote_id SET DEFAULT nextval('votes_vote_id_seq'::regclass);


--
-- TOC entry 2050 (class 2606 OID 16499)
-- Name: played_pkey; Type: CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY played
    ADD CONSTRAINT played_pkey PRIMARY KEY (play_id);


--
-- TOC entry 2052 (class 2606 OID 16501)
-- Name: played_song_id_key; Type: CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY played
    ADD CONSTRAINT played_song_id_key UNIQUE (song_id);


--
-- TOC entry 2055 (class 2606 OID 16503)
-- Name: song_id; Type: CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY songs
    ADD CONSTRAINT song_id PRIMARY KEY (song_id);


--
-- TOC entry 2057 (class 2606 OID 16505)
-- Name: songs_url_key; Type: CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY songs
    ADD CONSTRAINT songs_url_key UNIQUE (url);


--
-- TOC entry 2059 (class 2606 OID 16507)
-- Name: user_id; Type: CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY users
    ADD CONSTRAINT user_id PRIMARY KEY (user_id);


--
-- TOC entry 2061 (class 2606 OID 16509)
-- Name: users_name_key; Type: CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_name_key UNIQUE (name);


--
-- TOC entry 2065 (class 2606 OID 16511)
-- Name: vote_id; Type: CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY votes
    ADD CONSTRAINT vote_id PRIMARY KEY (vote_id);


--
-- TOC entry 2062 (class 1259 OID 16512)
-- Name: fki_song_id; Type: INDEX; Schema: public; Owner: mindfulness
--

CREATE INDEX fki_song_id ON votes USING btree (song_id);


--
-- TOC entry 2053 (class 1259 OID 16513)
-- Name: fki_user_id; Type: INDEX; Schema: public; Owner: mindfulness
--

CREATE INDEX fki_user_id ON songs USING btree (user_id);


--
-- TOC entry 2063 (class 1259 OID 16514)
-- Name: fki_user_id2; Type: INDEX; Schema: public; Owner: mindfulness
--

CREATE INDEX fki_user_id2 ON votes USING btree (user_id);


--
-- TOC entry 2066 (class 2606 OID 16515)
-- Name: played_song_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY played
    ADD CONSTRAINT played_song_id_fkey FOREIGN KEY (song_id) REFERENCES songs(song_id);


--
-- TOC entry 2068 (class 2606 OID 16520)
-- Name: song_id; Type: FK CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY votes
    ADD CONSTRAINT song_id FOREIGN KEY (song_id) REFERENCES songs(song_id);


--
-- TOC entry 2067 (class 2606 OID 16525)
-- Name: user_id; Type: FK CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY songs
    ADD CONSTRAINT user_id FOREIGN KEY (user_id) REFERENCES users(user_id);


--
-- TOC entry 2069 (class 2606 OID 16530)
-- Name: user_id; Type: FK CONSTRAINT; Schema: public; Owner: mindfulness
--

ALTER TABLE ONLY votes
    ADD CONSTRAINT user_id FOREIGN KEY (user_id) REFERENCES users(user_id);


--
-- TOC entry 2190 (class 0 OID 0)
-- Dependencies: 7
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2017-11-30 20:27:41 GMT

--
-- PostgreSQL database dump complete
--

