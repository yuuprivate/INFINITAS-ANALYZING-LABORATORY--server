-- ==========================================
-- 1. 楽曲・譜面マスター系
-- ==========================================

CREATE TABLE IF NOT EXISTS m_songs (
    song_id INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    artist VARCHAR,
    PRIMARY KEY (song_id)
);

CREATE TABLE IF NOT EXISTS m_charts (
    chart_id VARCHAR NOT NULL,
    play_style SMALLINT NOT NULL, -- 0:SP, 1:DP
    song_id INTEGER NOT NULL,
    difficulty_type VARCHAR NOT NULL,
    level INTEGER NOT NULL,
    notes INTEGER NOT NULL,
    PRIMARY KEY (chart_id, play_style),
    FOREIGN KEY (song_id)
        REFERENCES m_songs (song_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS d_charts_clear_irt (
    chart_id VARCHAR NOT NULL,
    play_style SMALLINT NOT NULL,
    irt_discrimination FLOAT DEFAULT 1.0,
    b_easy FLOAT NOT NULL,
    b_normal FLOAT NOT NULL,
    b_hard FLOAT NOT NULL,
    b_ex_hard FLOAT NOT NULL,
    b_fc FLOAT NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (chart_id, play_style),
    FOREIGN KEY (chart_id, play_style)
        REFERENCES m_charts (chart_id, play_style)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS d_charts_score_irt (
    chart_id VARCHAR NOT NULL,
    play_style SMALLINT NOT NULL,
    b_score FLOAT NOT NULL,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (chart_id, play_style),
    FOREIGN KEY (chart_id, play_style)
        REFERENCES m_charts (chart_id, play_style)
        ON DELETE CASCADE
);


-- ==========================================
-- 2. ユーザー系
-- ==========================================

CREATE TABLE IF NOT EXISTS m_users (
    user_id INTEGER NOT NULL,
    dj_name VARCHAR NOT NULL,
    iidx_id_first INTEGER NOT NULL,
    iidx_id_second INTEGER NOT NULL,
    iidx_id_third INTEGER NOT NULL,
    password_hash VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    delete_flag SMALLINT NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id),
    CONSTRAINT uq_dj_name UNIQUE (dj_name),
    CONSTRAINT uq_iidx_id
        UNIQUE (iidx_id_first, iidx_id_second, iidx_id_third)
);

CREATE TABLE IF NOT EXISTS d_users_irt (
    user_id INTEGER NOT NULL,
    ability_clear_sp FLOAT DEFAULT 10.0,
    ability_clear_dp FLOAT DEFAULT 10.0,
    ability_score_sp FLOAT DEFAULT 10.0,
    ability_score_dp FLOAT DEFAULT 10.0,
    PRIMARY KEY (user_id),
    FOREIGN KEY (user_id)
        REFERENCES m_users (user_id)
        ON DELETE CASCADE
);


-- ==========================================
-- 3. スコア系
-- ==========================================

CREATE TABLE IF NOT EXISTS scores (
    score_id BIGINT NOT NULL,
    user_id INTEGER NOT NULL,
    chart_id VARCHAR NOT NULL,
    play_style SMALLINT NOT NULL,
    clear_state INTEGER NOT NULL,
    ex_score INTEGER,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    PRIMARY KEY (score_id),
    FOREIGN KEY (user_id)
        REFERENCES m_users (user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (chart_id, play_style)
        REFERENCES m_charts (chart_id, play_style)
        ON DELETE CASCADE,
    CONSTRAINT uq_user_chart_style
        UNIQUE (user_id, chart_id, play_style)
);

CREATE INDEX IF NOT EXISTS idx_scores_user_id
    ON scores (user_id);

CREATE INDEX IF NOT EXISTS idx_scores_chart_style
    ON scores (chart_id, play_style);

-- ==========================================
-- 4. バージョン系
-- ==========================================

CREATE TABLE IF NOT EXISTS m_version (
    version_id INTEGER not null,
    version_name VARCHAR not null,
    updated_at TIMESTAMP WITHOUT TIME ZONE
)