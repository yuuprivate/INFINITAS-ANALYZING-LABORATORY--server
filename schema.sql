--
-- PostgreSQL database dump
--

\restrict eu5tUTb6ZWJhP4PrRGoIeMNHOydTPqfxBuZJRdaf1PUIEjfu8koTSRx5V75htuM

-- Dumped from database version 15.19
-- Dumped by pg_dump version 18.6 (Ubuntu 18.6-0ubuntu0.26.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: d_charts_clear_irt; Type: TABLE; Schema: public; Owner: iidx_user
--

CREATE TABLE public.d_charts_clear_irt (
    chart_id integer NOT NULL,
    play_style smallint NOT NULL,
    irt_discrimination double precision DEFAULT 1.0,
    b_easy double precision NOT NULL,
    b_normal double precision NOT NULL,
    b_hard double precision NOT NULL,
    b_ex_hard double precision NOT NULL,
    b_fc double precision NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.d_charts_clear_irt OWNER TO iidx_user;

--
-- Name: d_charts_score_irt; Type: TABLE; Schema: public; Owner: iidx_user
--

CREATE TABLE public.d_charts_score_irt (
    chart_id integer NOT NULL,
    play_style smallint NOT NULL,
    b_score double precision NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.d_charts_score_irt OWNER TO iidx_user;

--
-- Name: d_users_irt; Type: TABLE; Schema: public; Owner: iidx_user
--

CREATE TABLE public.d_users_irt (
    user_id integer NOT NULL,
    ability_clear_sp double precision DEFAULT 10.0,
    ability_clear_dp double precision DEFAULT 10.0,
    ability_score_sp double precision DEFAULT 10.0,
    ability_score_dp double precision DEFAULT 10.0
);


ALTER TABLE public.d_users_irt OWNER TO iidx_user;

--
-- Name: m_charts; Type: TABLE; Schema: public; Owner: iidx_user
--

CREATE TABLE public.m_charts (
    chart_id integer NOT NULL,
    play_style smallint NOT NULL,
    song_id integer NOT NULL,
    difficulty_type integer NOT NULL,
    level integer NOT NULL,
    notes integer NOT NULL,
    version integer
);


ALTER TABLE public.m_charts OWNER TO iidx_user;

--
-- Name: m_difficulty; Type: TABLE; Schema: public; Owner: iidx_user
--

CREATE TABLE public.m_difficulty (
    difficulty_id integer NOT NULL,
    difficulty_name character varying
);


ALTER TABLE public.m_difficulty OWNER TO iidx_user;

--
-- Name: m_songs; Type: TABLE; Schema: public; Owner: iidx_user
--

CREATE TABLE public.m_songs (
    song_id integer NOT NULL,
    title character varying NOT NULL,
    version integer
);


ALTER TABLE public.m_songs OWNER TO iidx_user;

--
-- Name: m_users; Type: TABLE; Schema: public; Owner: iidx_user
--

CREATE TABLE public.m_users (
    user_id integer NOT NULL,
    dj_name character varying NOT NULL,
    iidx_id_first integer NOT NULL,
    iidx_id_second integer NOT NULL,
    iidx_id_third integer NOT NULL,
    password_hash character varying NOT NULL,
    created_at timestamp without time zone,
    delete_flag smallint DEFAULT 0 NOT NULL
);


ALTER TABLE public.m_users OWNER TO iidx_user;

--
-- Name: m_version; Type: TABLE; Schema: public; Owner: iidx_user
--

CREATE TABLE public.m_version (
    version_id integer NOT NULL,
    version_name character varying NOT NULL,
    updated_at timestamp without time zone
);


ALTER TABLE public.m_version OWNER TO iidx_user;

--
-- Name: scores; Type: TABLE; Schema: public; Owner: iidx_user
--

CREATE TABLE public.scores (
    score_id bigint NOT NULL,
    user_id integer NOT NULL,
    chart_id integer NOT NULL,
    play_style smallint NOT NULL,
    clear_state integer NOT NULL,
    ex_score integer,
    updated_at timestamp without time zone
);


ALTER TABLE public.scores OWNER TO iidx_user;

--
-- Name: d_charts_clear_irt d_charts_clear_irt_pkey; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.d_charts_clear_irt
    ADD CONSTRAINT d_charts_clear_irt_pkey PRIMARY KEY (chart_id, play_style);


--
-- Name: d_charts_score_irt d_charts_score_irt_pkey; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.d_charts_score_irt
    ADD CONSTRAINT d_charts_score_irt_pkey PRIMARY KEY (chart_id, play_style);


--
-- Name: d_users_irt d_users_irt_pkey; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.d_users_irt
    ADD CONSTRAINT d_users_irt_pkey PRIMARY KEY (user_id);


--
-- Name: m_charts m_charts_pkey; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.m_charts
    ADD CONSTRAINT m_charts_pkey PRIMARY KEY (chart_id, play_style);


--
-- Name: m_difficulty m_difficulty_pkey; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.m_difficulty
    ADD CONSTRAINT m_difficulty_pkey PRIMARY KEY (difficulty_id);


--
-- Name: m_songs m_songs_pkey; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.m_songs
    ADD CONSTRAINT m_songs_pkey PRIMARY KEY (song_id);


--
-- Name: m_users m_users_pkey; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.m_users
    ADD CONSTRAINT m_users_pkey PRIMARY KEY (user_id);


--
-- Name: scores scores_pkey; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_pkey PRIMARY KEY (score_id);


--
-- Name: m_users uq_dj_name; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.m_users
    ADD CONSTRAINT uq_dj_name UNIQUE (dj_name);


--
-- Name: m_users uq_iidx_id; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.m_users
    ADD CONSTRAINT uq_iidx_id UNIQUE (iidx_id_first, iidx_id_second, iidx_id_third);


--
-- Name: scores uq_user_chart_style; Type: CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT uq_user_chart_style UNIQUE (user_id, chart_id, play_style);


--
-- Name: idx_scores_chart_style; Type: INDEX; Schema: public; Owner: iidx_user
--

CREATE INDEX idx_scores_chart_style ON public.scores USING btree (chart_id, play_style);


--
-- Name: idx_scores_user_id; Type: INDEX; Schema: public; Owner: iidx_user
--

CREATE INDEX idx_scores_user_id ON public.scores USING btree (user_id);


--
-- Name: d_charts_clear_irt d_charts_clear_irt_chart_id_play_style_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.d_charts_clear_irt
    ADD CONSTRAINT d_charts_clear_irt_chart_id_play_style_fkey FOREIGN KEY (chart_id, play_style) REFERENCES public.m_charts(chart_id, play_style);


--
-- Name: d_charts_score_irt d_charts_score_irt_chart_id_play_style_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.d_charts_score_irt
    ADD CONSTRAINT d_charts_score_irt_chart_id_play_style_fkey FOREIGN KEY (chart_id, play_style) REFERENCES public.m_charts(chart_id, play_style);


--
-- Name: d_users_irt d_users_irt_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.d_users_irt
    ADD CONSTRAINT d_users_irt_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.m_users(user_id) ON DELETE CASCADE;


--
-- Name: m_charts m_charts_song_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.m_charts
    ADD CONSTRAINT m_charts_song_id_fkey FOREIGN KEY (song_id) REFERENCES public.m_songs(song_id) ON DELETE CASCADE;


--
-- Name: scores scores_chart_id_play_style_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_chart_id_play_style_fkey FOREIGN KEY (chart_id, play_style) REFERENCES public.m_charts(chart_id, play_style);


--
-- Name: scores scores_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: iidx_user
--

ALTER TABLE ONLY public.scores
    ADD CONSTRAINT scores_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.m_users(user_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict eu5tUTb6ZWJhP4PrRGoIeMNHOydTPqfxBuZJRdaf1PUIEjfu8koTSRx5V75htuM

