import os
import uuid
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from sqlmodel import Field, SQLModel, create_engine, Session, select

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine (SQLite fallback if DATABASE_URL is not set, to prevent crashes!)
if not DATABASE_URL:
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "macaaksara.db")
    DATABASE_URL = f"sqlite:///{db_path}"

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# 1. Dictionary Table Model
class Dictionary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    word: str = Field(index=True, unique=True)
    javanese: str
    meaning: str

# 2. Scan History Table Model
class ScanHistory(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    image_path: str
    latin_output: str
    translation: str
    detected_at: datetime = Field(default_factory=datetime.utcnow)

# 3. Dataset Catalog Table Model
class DatasetCatalog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str = Field(index=True, unique=True)
    base_label: str
    vowel_label: str
    final_label: str
    origin: str

def get_session():
    with Session(engine) as session:
        yield session

def init_db():
    try:
        # Create tables
        SQLModel.metadata.create_all(engine)
        print("[INFO] Database tables initialized successfully.")
        
        # Auto-seed dictionary if empty
        with Session(engine) as session:
            statement = select(Dictionary)
            results = session.exec(statement).first()
            
            if not results:
                print("[INFO] Seeding default vocabulary dictionary into database...")
                DEFAULT_VOCAB = {
                    "maca": "membaca", "aksara": "aksara / huruf", "jawa": "Jawa", "sega": "nasi",
                    "bapa": "bapak / ayah", "ibu": "ibu", "tuku": "membeli", "turu": "tidur",
                    "mangan": "makan", "ngombe": "minum", "kopi": "kopi", "susu": "susu",
                    "adus": "mandi", "dahar": "makan (halus/krama)", "tindak": "pergi (halus/krama)",
                    "rawuh": "datang (halus/krama)", "sare": "tidur (halus/krama)", "luwe": "lapar",
                    "kencot": "lapar (ngoko)", "desa": "desa", "negara": "negara", "kanca": "teman",
                    "dalan": "jalan", "omah": "rumah", "banyu": "air", "geni": "api", "angin": "angin",
                    "lemah": "tanah", "langit": "langit", "lintang": "bintang", "rembulan": "bulan",
                    "srengenge": "matahari", "sabar": "sabar", "seneng": "senang / suka", "sedih": "sedih",
                    "sinahu": "belajar", "apik": "bagus / baik", "elek": "jelek", "anyar": "baru",
                    "ngiris": "mengiris", "sawo": "sawo"
                }
                
                db_entries = []
                for lat_word, ind_meaning in DEFAULT_VOCAB.items():
                    entry = Dictionary(word=lat_word, javanese="", meaning=ind_meaning)
                    db_entries.append(entry)
                
                session.add_all(db_entries)
                session.commit()
                print(f"[INFO] Successfully seeded {len(db_entries)} entries into 'dictionary' table.")
    except Exception as e:
        print(f"[WARNING] Database connection failed or could not initialize. Falling back to local files: {e}")
