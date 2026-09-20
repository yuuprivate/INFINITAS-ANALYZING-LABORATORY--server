import csv
from sqlalchemy.orm import Session
from src.database import SessionLocal
from src.models import song_models

def import_csv_to_m_song(file_path: str):
    db: Session = SessionLocal()
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                song_id = int(row["SONG_ID"])
                
                # 重複チェック
                existing = db.query(song_models.MSong).filter(song_models.MSong.song_id == song_id).first()
                if existing:
                    continue

                new_song = song_models.MSong(
                    song_id=song_id,
                    title=row["TITLE"],
                    version=row["VERSION"]
                )
                db.add(new_song)
                count += 1
            
            db.commit()
            print(f"成功: {count} 件の楽曲データをインポートしました！")
    except Exception as e:
        db.rollback()
        print(f"エラーが発生しました: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_csv_to_m_song("data/m_song.csv")