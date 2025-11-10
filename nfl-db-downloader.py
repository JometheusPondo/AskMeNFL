#!/usr/bin/env python3
"""
NFL Complete Data Downloader - nflreadpy version
"""

import nflreadpy as nfl
import sqlite3
import time
import logging
from datetime import datetime
import os
from typing import List
import sys

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nfl_download.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NFLDataDownloader:
    def __init__(self, db_path: str = "/app/data/nfl_complete_database.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.download_stats = {}

    def log_progress(self, dataset_name: str, years: List[int], start_time: float):
        elapsed = time.time() - start_time
        self.download_stats[dataset_name] = {
            'years': years,
            'elapsed_time': elapsed,
            'timestamp': datetime.now()
        }
        logger.info(f"Completed {dataset_name} in {elapsed:.1f}s")

    def download_pbp_data(self, years: List[int]):
        """Download play-by-play in batches"""
        logger.info("Downloading play-by-play data...")
        batch_size = 5

        for i in range(0, len(years), batch_size):
            batch = years[i:i + batch_size]
            start_time = time.time()
            try:
                logger.info(f"  Years: {batch[0]}-{batch[-1]}")
                pbp = nfl.load_pbp(seasons=batch).to_pandas()

                if_exists = 'replace' if i == 0 else 'append'
                pbp.to_sql('plays', self.conn, if_exists=if_exists, index=False)

                logger.info(f"  Done in {time.time() - start_time:.1f}s")
                del pbp

            except Exception as e:
                logger.error(f"  Failed: {e}")

    def download_player_stats(self, years: List[int]):
        """Download player stats"""
        logger.info("Downloading player stats...")
        start_time = time.time()
        try:
            stats = nfl.load_player_stats(seasons=years).to_pandas()
            stats.to_sql('player_stats', self.conn, if_exists='replace', index=False)
            self.log_progress('player_stats', years, start_time)
        except Exception as e:
            logger.error(f"Failed: {e}")

    def download_rosters(self, years: List[int]):
        """Download rosters"""
        logger.info("Downloading rosters...")
        start_time = time.time()
        try:
            rosters = nfl.load_rosters(seasons=years).to_pandas()
            rosters.to_sql('rosters', self.conn, if_exists='replace', index=False)
            self.log_progress('rosters', years, start_time)
        except Exception as e:
            logger.error(f"Failed: {e}")

    def download_schedules(self, years: List[int]):
        """Download schedules"""
        logger.info("Downloading schedules...")
        start_time = time.time()
        try:
            schedules = nfl.load_schedules(seasons=years).to_pandas()
            schedules.to_sql('schedules', self.conn, if_exists='replace', index=False)
            self.log_progress('schedules', years, start_time)
        except Exception as e:
            logger.error(f"Failed: {e}")

    def download_players(self):
        """Download player info"""
        logger.info("Downloading player info...")
        start_time = time.time()
        try:
            players = nfl.load_players().to_pandas()
            players.to_sql('players', self.conn, if_exists='replace', index=False)
            self.log_progress('players', ['all'], start_time)
        except Exception as e:
            logger.error(f"Failed: {e}")

    def create_indexes(self):
        """Create indexes"""
        logger.info("Creating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_plays_passer ON plays(passer_player_name)",
            "CREATE INDEX IF NOT EXISTS idx_plays_season ON plays(season)",
            "CREATE INDEX IF NOT EXISTS idx_plays_week ON plays(week)",
            "CREATE INDEX IF NOT EXISTS idx_plays_team ON plays(posteam)",
        ]

        for idx in indexes:
            try:
                self.conn.execute(idx)
            except:
                pass
        self.conn.commit()

    def download_everything(self):
        """Download all data"""
        total_start = time.time()
        logger.info("Starting NFL data download...")

        years = list(range(1999, 2026))  # 1999-2025

        try:
            self.download_pbp_data(years)
            self.download_player_stats(years)
            self.download_rosters(years)
            self.download_schedules(years)
            self.download_players()
            self.create_indexes()

            logger.info(f"\nDone! Time: {(time.time() - total_start) / 60:.1f} min")

            # Print summary
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            for table in cursor.fetchall():
                cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                logger.info(f"  {table[0]}: {cursor.fetchone()[0]:,} rows")

        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise
        finally:
            self.conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "/app/data/nfl_complete_database.db"

    print("NFL Data Downloader (nflreadpy)")
    print("Downloading 1999-2025 seasons")
    print("Time: ~30-60 minutes")

    confirm = input("\nProceed? (yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        downloader = NFLDataDownloader(db_path)
        downloader.download_everything()
    else:
        print("Cancelled")