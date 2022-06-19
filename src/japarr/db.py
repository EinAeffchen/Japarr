from pathlib import Path
import sqlite3
import japarr


class JaparrDB:
    SAVE_PATH: Path
    DB_NAME: str

    class ConnectionManager:
        def __init__(self, path):
            self.conn = sqlite3.connect(path)

        def __enter__(self):
            self.cur = self.conn.cursor()
            return self.cur

        def __exit__(self, exc_type, exc_value, exc_traceback):
            self.conn.commit()

    def __init__(self, save_path: str = ""):
        if save_path:
            self.SAVE_PATH = save_path
            self.db_path = self.SAVE_PATH
        else:
            self.SAVE_PATH = Path(japarr.__file__).parent / "config/db"
            self.DB_NAME = "downloads.db"
            self.db_path = self.SAVE_PATH / self.DB_NAME
        self._setup_db()

    def get_drama(self, title: str) -> list:
        with self.ConnectionManager(self.db_path) as cur:
            cur.execute(
                "SELECT * FROM dramas WHERE name=? ORDER BY season, episode",
                (title,),
            )
            return cur.fetchall()

    def get_movie(self, title: str) -> dict:
        with self.ConnectionManager(self.db_path) as cur:
            cur.execute("SELECT * FROM movies WHERE name=?", (title,))
            return cur.fetchone()

    def add_movie(self, title: str, url: str):
        with self.ConnectionManager(self.db_path) as cur:
            cur.execute(
                "INSERT INTO movies(name, url) VALUES(?,?)", (title, url)
            )

    def add_episode(
        self, title: str, url: str, season: int, episode: int, ongoing: int
    ):
        with self.ConnectionManager(self.db_path) as cur:
            cur.execute(
                """INSERT INTO dramas(name, url, season, episode, ongoing)
                            VALUES(?,?,?,?,?)""",
                (title, url, season, episode, ongoing),
            )

    def _setup_db(self):
        with self.ConnectionManager(self.db_path) as c:
            c.execute(
                """
                    CREATE TABLE IF NOT EXISTS dramas
                    ([id] INTEGER PRIMARY KEY, [name] TEXT, [url] TEXT, [season] INTEGER, [episode] INTEGER, [ongoing] INTEGER)
                    """
            )

            c.execute(
                """
                    CREATE TABLE IF NOT EXISTS movies
                    ([id] INTEGER PRIMARY KEY, [name] TEXT, [url] TEXT)
                    """
            )
