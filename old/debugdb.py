#!/usr/bin/env python3
"""
Quick script to get the exact pass attempt counts for comparison
"""
import sqlite3


def get_pass_attempts():
    """Get pass attempts for key QBs from both databases"""

    # nfl_data_py results
    print("🏈 NFL Data Py Results:")
    print("=" * 40)

    conn = sqlite3.connect("nfl_data_py.db")

    qbs = ['J.Goff', 'J.Burrow']

    for qb in qbs:
        # Different filtering approaches
        queries = [
            ("Most permissive (sack = 0)", f"""
                SELECT COUNT(*) FROM plays 
                WHERE passer_player_name = '{qb}' 
                AND season_type = 'REG' AND qb_dropback = 1 AND sack = 0
            """),
            ("Strict filtering", f"""
                SELECT COUNT(*) FROM plays 
                WHERE passer_player_name = '{qb}' 
                AND season_type = 'REG' AND qb_dropback = 1 AND sack = 0 
                AND penalty = 0
            """),
            ("Total dropbacks", f"""
                SELECT COUNT(*) FROM plays 
                WHERE passer_player_name = '{qb}' 
                AND season_type = 'REG' AND qb_dropback = 1
            """)
        ]

        print(f"\n{qb}:")
        for description, query in queries:
            try:
                result = conn.execute(query).fetchone()[0]
                print(f"  • {description}: {result}")
            except Exception as e:
                print(f"  • {description}: Error - {e}")

    conn.close()

    print(f"\n" + "=" * 40)
    print("📊 Comparison Summary:")
    print("Official sites: J.Goff = 539, J.Burrow = 652")
    print("Your nflfastR:  J.Goff = 537, J.Burrow = 653")
    print("nfl_data_py:    See results above")


if __name__ == "__main__":
    get_pass_attempts()