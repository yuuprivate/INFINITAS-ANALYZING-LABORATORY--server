import csv
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database import SessionLocal
from src.models import chart_models, song_models

def import_csv_to_m_chart(file_path: str):
    db: Session = SessionLocal()

    try:
        max_id_result = db.query(func.max(chart_models.MChart.chart_id)).scalar()
        current_chart_id = max_id_result if max_id_result is not None else 0

        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            
            notes_mapping = {
                "SP BEGINNER": (0, 0),
                "SP NORMAL": (0, 1),
                "SP HYPER": (0, 2),
                "SP ANOTHER": (0, 3),
                "SP LEGGENDARIA": (0, 4),
                "DP NORMAL": (1, 1),
                "DP HYPER": (1, 2),
                "DP ANOTHER": (1, 3),
                "DP LEGGENDARIA": (1, 4),
            }

            level_mapping = {
                "SPB": (0, 0),
                "SPN": (0, 1),
                "SPH": (0, 2),
                "SPA": (0, 3),
                "SPL": (0, 4),
                "DPN": (1, 1),
                "DPH": (1, 2),
                "DPA": (1, 3),
                "DPL": (1, 4),
            }

            for line_no, row in enumerate(reader, start=2):
                song_id_raw = row.get("SONG_ID")
                if not song_id_raw or not song_id_raw.strip():
                    continue
                
                song_id = int(song_id_raw)
                
                song = db.query(song_models.MSong).filter(song_models.MSong.song_id == song_id).first()
                if not song:
                    print(f"[行 {line_no}] 警告: SONG_ID {song_id} ({row.get('TITLE')}) が m_song に存在しないためスキップします。")
                    continue
                
                song_version = song.version

                for diff_name, (play_style, diff_type) in notes_mapping.items():
                    note_col = diff_name
                    level_col = [k for k, v in level_mapping.items() if v == (play_style, diff_type)][0]

                    note_val = row.get(note_col)
                    level_val = row.get(level_col)

                    if (not note_val or note_val.strip().upper() == "NULL") and \
                       (not level_val or level_val.strip().upper() == "NULL"):
                        continue

                    parsed_notes = int(note_val.strip()) if note_val and note_val.strip().upper() != "NULL" else None
                    parsed_level = int(level_val.strip()) if level_val and level_val.strip().upper() != "NULL" else None

                    # データベースの level が NOT NULL のため、レベルが取得できない場合は登録を見送る
                    if parsed_level is None:
                        continue
                    if parsed_notes is None:
                        continue

                    existing = db.query(chart_models.MChart).filter(
                        chart_models.MChart.song_id == song_id,
                        chart_models.MChart.play_style == play_style,
                        chart_models.MChart.difficulty_type == diff_type
                    ).first()

                    if existing:
                        existing.version = song_version
                        existing.notes = parsed_notes
                        existing.level = parsed_level
                    else:
                        current_chart_id += 1
                        new_chart = chart_models.MChart(
                            chart_id=current_chart_id,
                            play_style=play_style,
                            song_id=song_id,
                            difficulty_type=diff_type,
                            level=parsed_level,
                            notes=parsed_notes,
                            version=song_version
                        )
                        db.add(new_chart)
                    count += 1
            
            db.commit()
            print(f"成功: 譜面データ（計 {count} 件）のインポート処理が完了しました！")
            
    except Exception as e:
        db.rollback()
        print(f"\n[エラー発生] CSVファイルの読み込み中（または直前の処理）にエラーが発生しました。")
        if 'line_no' in locals():
            print(f"エラー発生行: 約 {line_no} 行目 (SONG_ID: {row.get('SONG_ID', '不明')}, TITLE: {row.get('TITLE', '不明')})")
        print(f"エラー詳細: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_to_m_chart("data/m_chart.csv")