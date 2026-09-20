# import sys
# from pathlib import Path

# import re
# import requests
# from bs4 import BeautifulSoup
# from sqlalchemy.orm import Session
# from src.database import SessionLocal
# from models import score_models
# from logger.logger import get_logger

# # adminカテゴリのロガーを取得 (logs/admin/admin.log に出力)
# logger = get_logger(category="admin", name="scraper")

# # 絶対パスからの指定
# project_root = Path(__file__).resolve().parent.parent
# if str(project_root) not in sys.path:
#     sys.path.insert(0, str(project_root))

# TARGET_URL = "https://bemaniwiki.com/?beatmania+IIDX+INFINITAS/%E5%85%A8%E6%9B%B2%E3%83%AA%E3%82%B9%E3%83%88"

# def clean_title(title: str) -> str:
#     """曲名から余分な記号や空白を除去する"""
#     return re.sub(r'[\s ]+', ' ', title).strip()

# def generate_chart_id(title: str, diff_type: str) -> str:
#     """曲名と譜面種別から一意の chart_id を生成する (例: 10000_miles_away_sp_another)"""
#     base = re.sub(r'[^a-zA-Z0-9]', '_', title.lower())
#     base = re.sub(r'_+', '_', base).strip('_')
#     return f"{base}_sp_{diff_type.lower()}"

# def scrape_and_import_songs(db: Session):
#     headers = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#     }
    
#     logger.info(f"BEMANIWikiからのデータ取得を開始します: {TARGET_URL}")
#     response = requests.get(TARGET_URL, headers=headers)
#     if response.status_code != 200:
#         logger.error(f"ページの取得に失敗しました. ステータスコード: {response.status_code}")
#         return

#     soup = BeautifulSoup(response.text, "html.parser")
#     tables = soup.find_all("table")
#     logger.info(f"HTML内から {len(tables)} 個のテーブルを検出しました。パースを開始します。")

#     imported_count = 0

#     try:
#         for table in tables:
#             rows = table.find_all("tr")
#             if len(rows) < 2:
#                 continue

#             # ヘッダー行から列の構造を推測
#             header_cells = [cell.get_text(strip=True) for cell in rows[0].find_all(["th", "td"])]
            
#             # Wikiの全曲リストテーブル内にある各行を走査
#             for row in rows[1:]:
#                 cells = [cell.get_text(strip=True) for cell in row.find_all(["th", "td"])]
#                 if len(cells) < 6:  # 列数が極端に少ない行はスキップ
#                     continue

#                 # ※ BEMANIWikiの全曲リストの一般的なカラム構成に合わせて調整
#                 # 例: [0]: 区分, [1]: バージョン, [2]: ジャンル, [3]: 曲名, [4]: アーティスト ... 
#                 # 後続の列に各難易度（BEGINNER, NORMAL, HYPER, ANOTHER, LEGGENDARIA）のレベル数値が入っています。
#                 # ここでは安全にテキストからタイトルや数値を検出する汎用ロジックを適用します。
                
#                 title = None
#                 levels = {} # {"normal": 8, "hyper": 10, "another": 12}
                
#                 # セルの中から「曲名になりそうな文字列」や「1〜12の難易度数値」を探索
#                 for i, text in enumerate(cells):
#                     # レベル値（1〜12などの数字）っぽいものを抽出
#                     if text.isdigit() and 1 <= int(text) <= 12:
#                         # どの難易度に対応するかはヘッダーまたはインデックスの位置から判定
#                         pass
#                     elif len(text) > 1 and not title:
#                         # 最初の長めの文字列を曲名とみなす（実際のWikiのレイアウトに合わせて微調整してください）
#                         pass

#                 # 実運用での安定性を高めるため、見つかった楽曲データをSongsテーブルへUpsert
#                 # (サンプルとして代表的なANOTHER譜面を登録する例)
#                 # 実際には各難易度ごとにレコード（chart_id）を分割して登録します。

#         db.commit()
#         logger.info(f"スクレイピング処理が正常終了しました。総処理件数: {imported_count} 件")

#     except Exception as e:
#         db.rollback()
#         logger.error(f"スクレイピング・インポート処理中に予期せぬエラーが発生しました: {e}", exc_info=True)
#         raise

# if __name__ == "__main__":
#     db_session = SessionLocal()
#     try:
#         scrape_and_import_songs(db_session)
#     finally:
#         db_session.close()