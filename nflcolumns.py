import nfl_data_py as nfl

# Get full column lists
pbp_cols = nfl.see_pbp_cols()
weekly_cols = nfl.see_weekly_cols()

print("=== PLAY-BY-PLAY COLUMNS ===")
for col in pbp_cols:
    print(f"* {col}")

print("\n=== WEEKLY DATA COLUMNS ===")
for col in weekly_cols:
    print(f"* {col}")

print(f"\nTotal PBP columns: {len(pbp_cols)}")
print(f"Total Weekly columns: {len(weekly_cols)}")