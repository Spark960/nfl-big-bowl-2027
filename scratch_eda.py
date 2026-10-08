import pandas as pd

pp = pd.read_csv('data/nfl-big-data-bowl-2027/player_play.csv', nrows=50000)
p = pd.read_csv('data/nfl-big-data-bowl-2027/players.csv')

# Merge to get positions
merged = pp.merge(p[['nfl_id','nfl_position']], on='nfl_id')

# For edge rushers — check key metrics availability
edge = merged[merged.nfl_position.isin(['DE','OLB'])]
print('=== EDGE RUSHER KEY METRICS (non-null counts) ===')
edge_cols = ['player_get_off','time_to_pressure','time_to_qb_hurry','sack','tackle',
             'quick_pressure','pressure_allowed','blitzing','tackle_for_loss']
for c in edge_cols:
    if c in edge.columns:
        non_null = edge[c].notna().sum()
        print(f'  {c}: {non_null}/{len(edge)} ({100*non_null/len(edge):.1f}%)')

print(f'\n=== OL KEY METRICS (non-null counts) ===')
ol = merged[merged.nfl_position.isin(['T','G','C'])]
ol_cols = ['pressure_allowed','sack_allowed','peak_pressure_probability_allowed',
           'time_to_pressure_allowed','pass_rushers_encountered','dropback_duration','extended_sack_allowed']
for c in ol_cols:
    if c in ol.columns:
        non_null = ol[c].notna().sum()
        print(f'  {c}: {non_null}/{len(ol)} ({100*non_null/len(ol):.1f}%)')

print(f'\n=== WR KEY METRICS (non-null counts) ===')
wr = merged[merged.nfl_position == 'WR']
wr_cols = ['separation_at_pass_forward','cushion','route_ran','target','rec_yards',
           'yards_after_catch','expected_yards_after_catch']
for c in wr_cols:
    if c in wr.columns:
        non_null = wr[c].notna().sum()
        print(f'  {c}: {non_null}/{len(wr)} ({100*non_null/len(wr):.1f}%)')

print(f'\n=== DB KEY METRICS (non-null counts) ===')
db = merged[merged.nfl_position.isin(['CB','SS','FS','DB'])]
db_cols = ['coverage_assignment','coverage_assignment_at_snap','tackle','assist',
           'blitzing','time_to_pressure','sack']
for c in db_cols:
    if c in db.columns:
        non_null = db[c].notna().sum()
        print(f'  {c}: {non_null}/{len(db)} ({100*non_null/len(db):.1f}%)')

# Career successes
cs = pd.read_csv('data/nfl-big-data-bowl-2027/player_career_successes.csv')
cs = cs.merge(p[['nfl_id','nfl_position']], on='nfl_id')

print(f'\n=== CAREER SUCCESS BY POSITION GROUP ===')
for pos_group, positions in [('Edge', ['DE','OLB']), ('OL', ['T','G','C']), ('WR', ['WR']), ('DB', ['CB','SS','FS','DB']), ('DT', ['DT','NT']), ('TE', ['TE'])]:
    sub = cs[cs.nfl_position.isin(positions)]
    all_pro = sub['ap_all_pro_1st_team'].sum() + sub['ap_all_pro_2nd_team'].sum()
    pro_bowl = sub['pro_bowl_original_ballot'].sum()
    avg_starts = sub['career_games_started'].mean()
    print(f'  {pos_group} (n={len(sub)}): All-Pro={all_pro}, Pro Bowl={pro_bowl}, Avg Starts={avg_starts:.1f}')
