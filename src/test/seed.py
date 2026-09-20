#########################################################
## 投入先テーブル:m_songs, m_charts, d_charts_clear_irt ##
#########################################################
import sys
from pathlib import Path

import random
import re
import requests
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import chart_models, score_models, song_models, user_models
from logger.logger import get_logger

logger = get_logger(category="admin", name="seed")

# 絶対パスからの指定
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

TARGET_URL = "https://bemaniwiki.com/?beatmania+IIDX+INFINITAS/%E5%85%A8%E6%9B%B2%E3%83%AA%E3%82%B9%E3%83%88"
DIFFICULTY_ORDER = ["BEGINNER", "NORMAL", "HYPER", "ANOTHER", "LEGGENDARIA"]

def calculate_initial_irt(level: int) -> dict:
    base = float(level)
    return {
        "b_easy": base - 0.5,
        "b_normal": base,
        "b_hard": base + 0.3,
        "b_ex_hard": base + 0.8,
        "b_fc": base + 1.5
    }

def parse_level(text: str) -> int | None:
    if not text:
        return None
    text = text.strip()
    if text in ["-", "―", ""]:
        return None
    match = re.search(r'\b(1[0-2]|[1-9])\b', text)
    return int(match.group(1)) if match else None

def table_to_2d_grid(table) -> list[list[str]]:
    """rowspan / colspan を展開して均一な2次元配列(grid)に変換する"""
    rows = table.find_all("tr")
    grid = []

    for r_idx, tr in enumerate(rows):
        cols = tr.find_all(["td", "th"])
        c_idx = 0

        while len(grid) <= r_idx:
            grid.append([])

        for td in cols:
            while c_idx < len(grid[r_idx]) and grid[r_idx][c_idx] is not None:
                c_idx += 1

            try:
                rowspan = int(td.get("rowspan", 1))
            except ValueError:
                rowspan = 1
            try:
                colspan = int(td.get("colspan", 1))
            except ValueError:
                colspan = 1

            text = td.get_text(strip=True)

            for r in range(r_idx, r_idx + rowspan):
                while len(grid) <= r:
                    grid.append([])
                for c in range(c_idx, c_idx + colspan):
                    while len(grid[r]) <= c:
                        grid[r].append(None)
                    grid[r][c] = text

            c_idx += colspan

    return grid

def seed_database():
    logger.info("=== BEMANIWiki 全曲リストのスクレイピング・データインポートを開始します ===")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (Chrome/120.0.0.0)"
    }

    try:
        response = requests.get(TARGET_URL, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
    except Exception as e:
        logger.error(f"Wikiページの取得に失敗しました: {e}")
        return

    db: Session = SessionLocal()

    song_id_counter = 1
    sp_chart_counter = 1
    dp_chart_counter = 1

    total_songs = 0
    total_charts = 0

    try:
        tables = soup.find_all("table")
        for table in tables:
            grid = table_to_2d_grid(table)
            if not grid or len(grid) < 2:
                continue

            # ヘッダー行から列インデックスを特定
            title_col = None
            artist_col = None

            for r in range(min(5, len(grid))):
                for c_idx, cell in enumerate(grid[r]):
                    if cell in ["曲名", "タイトル", "Title"]:
                        title_col = c_idx
                    elif cell in ["アーティスト", "Artist"]:
                        artist_col = c_idx

            # 見つからない場合のデフォルト列想定 [Ver, Title, Artist, ...]
            if title_col is None:
                title_col = 1
            if artist_col is None:
                artist_col = 2

            last_title = None

            for row in grid:
                if len(row) <= title_col:
                    continue

                title = row[title_col]
                artist = row[artist_col] if len(row) > artist_col and artist_col is not None else ""

                # ヘッダー・見出し行・空行のスキップ
                if not title or title in ["曲名", "タイトル", "Title"] or "▼" in title or "▲" in title:
                    continue

                # 同一曲の複数行（CN表記行など）対策: Titleが変わった時のみ song_id を発行
                current_song_id = song_id_counter
                if title != last_title:
                    song_obj = song_models.MSong(
                        song_id=current_song_id,
                        title=title,
                        artist=artist
                    )
                    db.add(song_obj)
                    total_songs += 1
                    song_id_counter += 1
                    last_title = title
                else:
                    current_song_id = song_id_counter - 1

                # 難易度レベル解析（SP: 3~7列目, DP: 8~11列目付近を探索）
                # 通常構成: [Ver, Title, Artist, BPM, SP-B, SP-N, SP-H, SP-A, SP-L, DP-N, DP-H, DP-A, DP-L]
                sp_cols = row[4:9] if len(row) >= 9 else []
                dp_cols = row[9:13] if len(row) >= 13 else []

                levels_sp = {}
                levels_dp = {}

                for idx, diff_type in enumerate(DIFFICULTY_ORDER):
                    if idx < len(sp_cols):
                        lvl = parse_level(sp_cols[idx])
                        if lvl:
                            levels_sp[diff_type] = lvl

                for idx, diff_type in enumerate(DIFFICULTY_ORDER[1:]):
                    if idx < len(dp_cols):
                        lvl = parse_level(dp_cols[idx])
                        if lvl:
                            levels_dp[diff_type] = lvl

                # SP 譜面登録
                for diff_type in DIFFICULTY_ORDER:
                    if diff_type in levels_sp:
                        chart_id_str = f"{sp_chart_counter:04d}"
                        lvl = levels_sp[diff_type]

                        db.add(chart_models.MChart(
                            chart_id=chart_id_str,
                            play_style=0,
                            song_id=current_song_id,
                            difficulty_type=diff_type,
                            level=lvl,
                            notes=random.randint(100, 2500)
                        ))

                        db.add(chart_models.DChartClearIrt(
                            chart_id=chart_id_str,
                            play_style=0,
                            irt_discrimination=1.0,
                            **calculate_initial_irt(lvl)
                        ))

                        sp_chart_counter += 1
                        total_charts += 1

                # DP 譜面登録
                for diff_type in DIFFICULTY_ORDER[1:]:
                    if diff_type in levels_dp:
                        chart_id_str = f"{dp_chart_counter:04d}"
                        lvl = levels_dp[diff_type]

                        db.add(chart_models.MChart(
                            chart_id=chart_id_str,
                            play_style=1,
                            song_id=current_song_id,
                            difficulty_type=diff_type,
                            level=lvl,
                            notes=random.randint(100, 2500)
                        ))

                        db.add(chart_models.DChartClearIrt(
                            chart_id=chart_id_str,
                            play_style=1,
                            irt_discrimination=1.0,
                            **calculate_initial_irt(lvl)
                        ))

                        dp_chart_counter += 1
                        total_charts += 1

        db.commit()
        logger.info(f"インポート完了: 楽曲 {total_songs} 件 | 譜面 {total_charts} 件")

    except Exception as e:
        db.rollback()
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()