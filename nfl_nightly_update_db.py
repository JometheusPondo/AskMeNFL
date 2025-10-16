#!/usr/bin/env python3
"""
NFL Database Nightly Update Script
Run this as a scheduled task/cron job
"""

import nfl_data_py as nfl
import sqlite3
import pandas as pd
import time
import logging
from datetime import datetime, timedelta
import os
import sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('nfl_update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NFLDataUpdater:
    def __init__(self, db_path: str = "nfl_complete_database.db"):
        self.db_path = db_path

        if not os.path.exists(db_path):
            logger.error(f"Database not found: {db_path}")
            raise FileNotFoundError(f"Database {db_path} does not exist. Run full download first.")

        self.conn = sqlite3.connect(db_path)
        self.current_year = datetime.now().year

    def get_current_season_info(self):
        today = datetime.now()

        if today.month >= 9:
            season = today.year
        else:
            season = today.year - 1

        logger.info(f"Current season: {season}")
        return season

    def update_current_season(self):
        season = self.get_current_season_info()
        years = [season]

        logger.info("Starting update...")

        # Play-by-Play Data
        logger.info("Updating play-by-play data...")
        start_time = time.time()
        try:
            pbp_data = nfl.import_pbp_data(years, downcast=True)


            self.conn.execute(f"DELETE FROM plays WHERE season = {season}")
            self.conn.commit()


            pbp_data.to_sql('plays', self.conn, if_exists='append', index=False)
            elapsed = time.time() - start_time
            logger.info(f"Play-by-play updated in {elapsed:.1f}s - {len(pbp_data):,} plays")
        except Exception as e:
            logger.error(f"Play-by-play update failed: {e}")

        # Weekly Stats
        logger.info("Updating weekly player stats...")
        start_time = time.time()
        try:
            weekly_data = nfl.import_weekly_data(years, downcast=True)

            self.conn.execute(f"DELETE FROM weekly_stats WHERE season = {season}")
            self.conn.commit()

            weekly_data.to_sql('weekly_stats', self.conn, if_exists='append', index=False)
            elapsed = time.time() - start_time
            logger.info(f"Weekly stats updated in {elapsed:.1f}s - {len(weekly_data):,} records")
        except Exception as e:
            logger.error(f"Weekly stats update failed: {e}")

        # Seasonal Stats
        logger.info("Updating seasonal stats...")
        start_time = time.time()
        try:
            seasonal_data = nfl.import_seasonal_data(years)

            self.conn.execute(f"DELETE FROM seasonal_stats WHERE season = {season}")
            self.conn.commit()

            seasonal_data.to_sql('seasonal_stats', self.conn, if_exists='append', index=False)
            elapsed = time.time() - start_time
            logger.info(f"Seasonal stats updated in {elapsed:.1f}s - {len(seasonal_data):,} records")
        except Exception as e:
            logger.error(f"Seasonal stats update failed: {e}")

        # Rosters
        logger.info("👥 Updating rosters...")
        start_time = time.time()
        try:
            # Seasonal rosters
            seasonal_rosters = nfl.import_seasonal_rosters(years)
            self.conn.execute(f"DELETE FROM seasonal_rosters WHERE season = {season}")
            self.conn.commit()
            seasonal_rosters.to_sql('seasonal_rosters', self.conn, if_exists='append', index=False)

            # Weekly rosters
            weekly_rosters = nfl.import_weekly_rosters(years)
            self.conn.execute(f"DELETE FROM weekly_rosters WHERE season = {season}")
            self.conn.commit()
            weekly_rosters.to_sql('weekly_rosters', self.conn, if_exists='append', index=False)

            elapsed = time.time() - start_time
            logger.info(f"Rosters updated in {elapsed:.1f}s")
        except Exception as e:
            logger.error(f"Roster update failed: {e}")

        # 5. Schedule
        logger.info("📅 Updating schedule...")
        start_time = time.time()
        try:
            schedules = nfl.import_schedules(years)
            self.conn.execute(f"DELETE FROM schedules WHERE season = {season}")
            self.conn.commit()
            schedules.to_sql('schedules', self.conn, if_exists='append', index=False)
            elapsed = time.time() - start_time
            logger.info(f"Schedule updated in {elapsed:.1f}s - {len(schedules):,} games")
        except Exception as e:
            logger.error(f"Schedule update failed: {e}")

    def update_advanced_stats(self):
        season = self.get_current_season_info()
        years = [season]

        logger.info("Updating advanced analytics...")

        # Next Gen Stats
        ngs_types = ['passing', 'rushing', 'receiving']
        for stat_type in ngs_types:
            try:
                logger.info(f"⚡ Updating NGS {stat_type}...")
                ngs_data = nfl.import_ngs_data(stat_type, years)

                self.conn.execute(f"DELETE FROM ngs_{stat_type} WHERE season = {season}")
                self.conn.commit()

                ngs_data.to_sql(f'ngs_{stat_type}', self.conn, if_exists='append', index=False)
                logger.info(f"NGS {stat_type} updated")
            except Exception as e:
                logger.error(f"NGS {stat_type} update failed: {e}")

    def vacuum_database(self):
        logger.info("Optimizing database...")
        try:
            self.conn.execute("VACUUM")
            self.conn.commit()
            logger.info("Database optimized")
        except Exception as e:
            logger.error(f"Vacuum failed: {e}")

    def print_update_summary(self):
        logger.info("\n" + "=" * 60)
        logger.info("DATABASE UPDATE COMPLETE!")
        logger.info("=" * 60)

        db_size = os.path.getsize(self.db_path) / (1024 ** 3)  # GB
        logger.info(f"Database size: {db_size:.2f} GB")

        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(season) FROM plays")
        latest_season = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM plays WHERE season = {latest_season}")
        plays_count = cursor.fetchone()[0]

        logger.info(f"Latest season: {latest_season}")
        logger.info(f"Plays in {latest_season}: {plays_count:,}")

        logger.info(f"Update completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    def run_update(self, full_advanced: bool = False):
        total_start = time.time()
        logger.info("STARTING NFL DATABASE UPDATE")
        logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            self.update_current_season()

            if full_advanced:
                self.update_advanced_stats()

            self.vacuum_database()

            self.print_update_summary()

        except Exception as e:
            logger.error(f"Update failed: {e}")
            raise
        finally:
            self.conn.close()
            total_elapsed = (time.time() - total_start) / 60
            logger.info(f"Total update time: {total_elapsed:.1f} minutes")


def main():
    """Main entry point for script"""
    import argparse

    parser = argparse.ArgumentParser(description='Update NFL database with latest data')
    parser.add_argument(
        '--db',
        default='nfl_complete_database.db',
        help='Path to NFL database (default: nfl_complete_database.db)'
    )
    parser.add_argument(
        '--full-advanced',
        action='store_true',
        help='Update advanced stats (NGS, FTN) - takes longer'
    )

    args = parser.parse_args()

    try:
        updater = NFLDataUpdater(args.db)
        updater.run_update(full_advanced=args.full_advanced)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Update failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()