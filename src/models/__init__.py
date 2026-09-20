# src/models/__init__.py
from src.database import Base

# 依存関係の順に読み込む
from src.models.user_models import MUser
from src.models.chart_models import MChart
from src.models.song_models import MSong
from src.models.score_models import Score