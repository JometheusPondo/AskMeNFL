#!/usr/bin/env python3
"""
NFL Complete Data Downloader
Downloads ALL available NFL data from nfl_data_py and organizes it into SQLite database
"""

import nfl_data_py as nfl
import sqlite3
import pandas as pd
import time
import logging
from datetime import datetime
import os
from typing import List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nfl_download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NFLDataDownloader:
    def __init__(self, db_path: str = "nfl_complete.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.download_stats = {}

    def log_progress(self, dataset_name: str, years: List[int], start_time: float):
        """Log download progress and statistics"""
        elapsed = time.time() - start_time
        self.download_stats[dataset_name] = {
            'years': years,
            'elapsed_time': elapsed,
            'timestamp': datetime.now()
        }
        logger.info(f"✅ {dataset_name} completed in {elapsed:.1f}s for years {min(years)}-{max(years)}")

    def download_core_data(self, years: List[int] = None):
        """Download the core datasets - play-by-play, weekly, and seasonal data"""
        if years is None:
            years = list(range(1999, 2025))  # 1999-2024

        logger.info(f"🏈 Starting core data download for {len(years)} years...")

        # 1. Play-by-Play Data (The crown jewel!)
        logger.info("📊 Downloading play-by-play data...")
        start_time = time.time()
        try:
            pbp_data = nfl.import_pbp_data(years, downcast=True)
            pbp_data.to_sql('plays', self.conn, if_exists='replace', index=False)
            self.log_progress('play_by_play', years, start_time)
        except Exception as e:
            logger.error(f"❌ Play-by-play download failed: {e}")

        # 2. Weekly Player Stats
        logger.info("📈 Downloading weekly player stats...")
        start_time = time.time()
        try:
            weekly_data = nfl.import_weekly_data(years, downcast=True)
            weekly_data.to_sql('weekly_stats', self.conn, if_exists='replace', index=False)
            self.log_progress('weekly_stats', years, start_time)
        except Exception as e:
            logger.error(f"❌ Weekly data download failed: {e}")

        # 3. Seasonal Aggregated Stats
        logger.info("🎯 Downloading seasonal stats...")
        start_time = time.time()
        try:
            seasonal_data = nfl.import_seasonal_data(years)
            seasonal_data.to_sql('seasonal_stats', self.conn, if_exists='replace', index=False)
            self.log_progress('seasonal_stats', years, start_time)
        except Exception as e:
            logger.error(f"❌ Seasonal data download failed: {e}")

    def download_roster_data(self, years: List[int] = None):
        """Download roster and player information"""
        if years is None:
            years = list(range(1999, 2025))

        logger.info(f"👥 Starting roster data download...")

        # Seasonal Rosters
        logger.info("🏟️ Downloading seasonal rosters...")
        start_time = time.time()
        try:
            seasonal_rosters = nfl.import_seasonal_rosters(years)
            seasonal_rosters.to_sql('seasonal_rosters', self.conn, if_exists='replace', index=False)
            self.log_progress('seasonal_rosters', years, start_time)
        except Exception as e:
            logger.error(f"❌ Seasonal rosters download failed: {e}")

        # Weekly Rosters (more detailed)
        logger.info("📅 Downloading weekly rosters...")
        start_time = time.time()
        try:
            weekly_rosters = nfl.import_weekly_rosters(years)
            weekly_rosters.to_sql('weekly_rosters', self.conn, if_exists='replace', index=False)
            self.log_progress('weekly_rosters', years, start_time)
        except Exception as e:
            logger.error(f"❌ Weekly rosters download failed: {e}")

    def download_advanced_analytics(self, years: List[int] = None):
        """Download Next Gen Stats and advanced analytics"""
        if years is None:
            years = list(range(2016, 2025))  # NGS data availability

        logger.info(f"🚀 Starting advanced analytics download...")

        # Next Gen Stats - Passing
        logger.info("🎯 Downloading NGS passing data...")
        start_time = time.time()
        try:
            ngs_passing = nfl.import_ngs_data('passing', years)
            ngs_passing.to_sql('ngs_passing', self.conn, if_exists='replace', index=False)
            self.log_progress('ngs_passing', years, start_time)
        except Exception as e:
            logger.error(f"❌ NGS passing download failed: {e}")

        # Next Gen Stats - Rushing
        logger.info("🏃 Downloading NGS rushing data...")
        start_time = time.time()
        try:
            ngs_rushing = nfl.import_ngs_data('rushing', years)
            ngs_rushing.to_sql('ngs_rushing', self.conn, if_exists='replace', index=False)
            self.log_progress('ngs_rushing', years, start_time)
        except Exception as e:
            logger.error(f"❌ NGS rushing download failed: {e}")

        # Next Gen Stats - Receiving
        logger.info("🙌 Downloading NGS receiving data...")
        start_time = time.time()
        try:
            ngs_receiving = nfl.import_ngs_data('receiving', years)
            ngs_receiving.to_sql('ngs_receiving', self.conn, if_exists='replace', index=False)
            self.log_progress('ngs_receiving', years, start_time)
        except Exception as e:
            logger.error(f"❌ NGS receiving download failed: {e}")

        # FTN Charting Data (2022+)
        ftn_years = [y for y in years if y >= 2022]
        if ftn_years:
            logger.info("📋 Downloading FTN charting data...")
            start_time = time.time()
            try:
                ftn_data = nfl.import_ftn_data(ftn_years, downcast=True)
                ftn_data.to_sql('ftn_charting', self.conn, if_exists='replace', index=False)
                self.log_progress('ftn_charting', ftn_years, start_time)
            except Exception as e:
                logger.error(f"❌ FTN data download failed: {e}")

    def download_context_data(self, years: List[int] = None):
        """Download schedules, draft data, and other contextual information"""
        if years is None:
            years = list(range(1999, 2025))

        logger.info(f"📚 Starting contextual data download...")

        # Schedules
        logger.info("📅 Downloading schedules...")
        start_time = time.time()
        try:
            schedules = nfl.import_schedules(years)
            schedules.to_sql('schedules', self.conn, if_exists='replace', index=False)
            self.log_progress('schedules', years, start_time)
        except Exception as e:
            logger.error(f"❌ Schedules download failed: {e}")

        # Draft Picks
        logger.info("🎯 Downloading draft picks...")
        start_time = time.time()
        try:
            draft_picks = nfl.import_draft_picks(years)
            draft_picks.to_sql('draft_picks', self.conn, if_exists='replace', index=False)
            self.log_progress('draft_picks', years, start_time)
        except Exception as e:
            logger.error(f"❌ Draft picks download failed: {e}")

        # Combine Data
        combine_years = [y for y in years if y >= 1987]  # Combine data availability
        if combine_years:
            logger.info("🏃‍♂️ Downloading combine data...")
            start_time = time.time()
            try:
                combine_data = nfl.import_combine_data(combine_years)
                combine_data.to_sql('combine_results', self.conn, if_exists='replace', index=False)
                self.log_progress('combine_results', combine_years, start_time)
            except Exception as e:
                logger.error(f"❌ Combine data download failed: {e}")

    def download_static_data(self):
        """Download static/reference data that doesn't change by year"""
        logger.info("🏛️ Downloading static reference data...")

        # Player ID mappings
        logger.info("🆔 Downloading player ID mappings...")
        start_time = time.time()
        try:
            player_ids = nfl.import_ids()
            player_ids.to_sql('player_ids', self.conn, if_exists='replace', index=False)
            self.log_progress('player_ids', ['all'], start_time)
        except Exception as e:
            logger.error(f"❌ Player IDs download failed: {e}")

        # Team descriptive data
        logger.info("🏟️ Downloading team information...")
        start_time = time.time()
        try:
            team_desc = nfl.import_team_desc()
            team_desc.to_sql('teams', self.conn, if_exists='replace', index=False)
            self.log_progress('teams', ['all'], start_time)
        except Exception as e:
            logger.error(f"❌ Team data download failed: {e}")

        # Draft values
        logger.info("💎 Downloading draft values...")
        start_time = time.time()
        try:
            draft_values = nfl.import_draft_values()
            draft_values.to_sql('draft_values', self.conn, if_exists='replace', index=False)
            self.log_progress('draft_values', ['all'], start_time)
        except Exception as e:
            logger.error(f"❌ Draft values download failed: {e}")

    def create_indexes(self):
        """Create database indexes for better query performance"""
        logger.info("⚡ Creating database indexes for performance...")

        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_plays_passer ON plays(passer_player_name)",
            "CREATE INDEX IF NOT EXISTS idx_plays_season ON plays(season)",
            "CREATE INDEX IF NOT EXISTS idx_plays_week ON plays(week)",
            "CREATE INDEX IF NOT EXISTS idx_plays_team ON plays(posteam)",
            "CREATE INDEX IF NOT EXISTS idx_weekly_player ON weekly_stats(player_name)",
            "CREATE INDEX IF NOT EXISTS idx_weekly_season ON weekly_stats(season)",
            "CREATE INDEX IF NOT EXISTS idx_seasonal_player ON seasonal_stats(player_name)",
            "CREATE INDEX IF NOT EXISTS idx_seasonal_season ON seasonal_stats(season)",
        ]

        for index_sql in indexes:
            try:
                self.conn.execute(index_sql)
                logger.info(f"✅ Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
            except Exception as e:
                logger.warning(f"⚠️ Index creation failed: {e}")

        self.conn.commit()

    def print_download_summary(self):
        """Print a summary of the download operation"""
        logger.info("\n" + "=" * 60)
        logger.info("🏆 NFL DATA DOWNLOAD COMPLETE!")
        logger.info("=" * 60)

        total_time = sum(stats['elapsed_time'] for stats in self.download_stats.values())
        logger.info(f"⏱️  Total download time: {total_time / 60:.1f} minutes")

        # Database size
        db_size = os.path.getsize(self.db_path) / (1024 ** 3)  # GB
        logger.info(f"💾 Database size: {db_size:.2f} GB")

        # Table counts
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"📊 Number of tables: {len(tables)}")

        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            logger.info(f"   📋 {table_name}: {count:,} rows")

        logger.info("\n🎉 Your NFL database is ready for legendary queries!")

    def download_everything(self):
        """Download all available NFL data"""
        total_start = time.time()
        logger.info("🚀 STARTING COMPLETE NFL DATA DOWNLOAD")
        logger.info("This will take a while, but it's going to be AMAZING!")

        try:
            # Core data (1999-2024)
            self.download_core_data()

            # Roster data
            self.download_roster_data()

            # Advanced analytics (limited years)
            self.download_advanced_analytics()

            # Contextual data
            self.download_context_data()

            # Static reference data
            self.download_static_data()

            # Performance indexes
            self.create_indexes()

            # Summary
            self.print_download_summary()

        except Exception as e:
            logger.error(f"💥 Download failed: {e}")
            raise
        finally:
            self.conn.close()
            total_elapsed = (time.time() - total_start) / 60
            logger.info(f"🏁 Total operation time: {total_elapsed:.1f} minutes")


if __name__ == "__main__":
    import sys

    db_path = sys.argv[1] if len(sys.argv) > 1 else "nfl_complete_database.db"

    print("🏈 NFL Complete Data Downloader")
    print("This will download ALL available NFL data from nfl_data_py")
    print("Estimated download time: 30-60 minutes")
    print("Estimated storage: 5-8 GB")

    confirm = input("\nProceed? (yes/no): ")
    if confirm.lower() in ['yes', 'y']:
        downloader = NFLDataDownloader("nfl_complete_database.db")
        downloader.download_everything()
    else:
        print("Download cancelled.")