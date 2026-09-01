# Harry Kane Similarity Shortlist

Baseline centre-forward profile similarity using StatsBomb open event data.

## Benchmark

Harry Kane, Tottenham Hotspur, Premier League 2015/2016. Player ID `10955`; minutes `3486.65`; matches `38`.

## Method

The model filters to centre-forwards with at least 900 minutes and at least 60% of their minutes at centre-forward. It compares players with robust-scaled, league-position-normalised role metrics and feature-group weights for threat, link play, progression, pressing and ball security.

Similarity is a relative ranking inside this historical reference cohort, not a statement that one player is a transfer recommendation or a universal percentage match.

## Top 10 Candidates

| candidate_rank | similarity_rank | similarity_percentile | profile_distance | player_id | player_name | team_name | competition_name | minutes | matches | non_penalty_xg_p90 | non_penalty_shots_p90 | average_non_penalty_xg_per_shot | successful_box_receipts_p90 | xg_assisted_p90 | completed_open_play_passes_p90 | final_third_pressures_p90 | counterpressures_p90 | ball_security_errors_p90 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2 | 97.826 | 0.607 | 3018 | Giovanni-Guy Yann Sio | Rennes | Ligue 1 | 2724.867 | 34 | 0.295 | 2.312 | 0.128 | 2.708 | 0.101 | 15.259 | 8.522 | 3.369 | 5.384 |
| 2 | 3 | 95.652 | 0.624 | 20521 | Bafétimbi Gomis | Swansea City | Premier League | 1811.733 | 33 | 0.340 | 2.881 | 0.118 | 2.981 | 0.079 | 17.486 | 5.862 | 2.832 | 6.210 |
| 3 | 4 | 93.478 | 0.636 | 4269 | Aleksandar Mitrović | Newcastle United | Premier League | 2326.000 | 34 | 0.398 | 3.018 | 0.132 | 3.405 | 0.099 | 16.793 | 6.191 | 2.902 | 7.003 |
| 4 | 5 | 91.304 | 0.669 | 3457 | Michy Batshuayi Tunga | Olympique de Marseille | Ligue 1 | 3052.417 | 36 | 0.505 | 3.568 | 0.142 | 3.863 | 0.080 | 12.737 | 7.106 | 3.951 | 5.926 |
| 5 | 6 | 89.130 | 0.678 | 3289 | Romelu Lukaku Menama | Everton | Premier League | 3299.483 | 37 | 0.453 | 3.110 | 0.146 | 3.792 | 0.132 | 19.258 | 4.310 | 1.991 | 5.919 |
| 6 | 7 | 86.957 | 0.687 | 15996 | Éderzito António Macedo Lopes | Lille | Ligue 1 | 1158.733 | 13 | 0.251 | 2.330 | 0.108 | 3.495 | 0.132 | 16.078 | 7.379 | 3.961 | 6.214 |
| 7 | 8 | 84.783 | 0.723 | 6973 | Edin Džeko | AS Roma | Serie A | 2087.267 | 31 | 0.513 | 3.708 | 0.138 | 5.174 | 0.074 | 15.048 | 6.899 | 3.838 | 5.950 |
| 8 | 9 | 82.609 | 0.760 | 8871 | Marco Borriello | Atalanta | Serie A | 1695.817 | 27 | 0.286 | 2.866 | 0.100 | 3.344 | 0.058 | 15.497 | 5.626 | 2.919 | 5.838 |
| 9 | 10 | 80.435 | 0.806 | 3604 | Olivier Giroud | Arsenal | Premier League | 2548.167 | 38 | 0.432 | 3.603 | 0.120 | 6.110 | 0.151 | 16.600 | 6.428 | 3.532 | 5.227 |
| 10 | 11 | 78.261 | 0.810 | 3038 | Andy Delort | Stade Malherbe Caen | Ligue 1 | 3244.983 | 36 | 0.286 | 3.827 | 0.075 | 2.940 | 0.115 | 13.285 | 7.128 | 3.411 | 7.488 |

## Feature Weights

| feature | weight |
| --- | --- |
| non_penalty_xg_p90_league_pos_z | 0.100 |
| non_penalty_shots_p90_league_pos_z | 0.100 |
| average_non_penalty_xg_per_shot_league_pos_z | 0.100 |
| xg_assisted_p90_league_pos_z | 0.083 |
| completed_open_play_passes_p90_league_pos_z | 0.083 |
| pressured_pass_completion_pct | 0.083 |
| successful_box_receipts_p90_league_pos_z | 0.050 |
| carries_into_box_p90_league_pos_z | 0.050 |
| progressive_carry_distance_p90_league_pos_z | 0.050 |
| successful_dribbles_p90_league_pos_z | 0.050 |
| final_third_pressures_p90_league_pos_z | 0.075 |
| counterpressures_p90_league_pos_z | 0.075 |
| ball_security_errors_p90_league_pos_z | 0.100 |
