# Harry Kane 2015/16 Centre-Forward Shortlist

Which centre-forwards in the 2015/16 open-data sample had event profiles closest to Harry Kane?

## Benchmark

Harry Kane, Tottenham Hotspur, Premier League 2015/2016; 3487 minutes.

## Method

Players are filtered to centre-forwards with at least 900 minutes and 60% of minutes in role. Similarity uses robust-scaled, league-position-normalised event metrics.

## Shortlist

| Rank | Player | Team | Competition | Distance | Rank interval | Note |
| --- | --- | --- | --- | ---: | --- | --- |
| 2 | Giovanni-Guy Yann Sio | Rennes | Ligue 1 | 0.607 | 2-10 | Closest to Kane on Avg NP xG/shot and xG assisted/90. |
| 3 | Bafétimbi Gomis | Swansea City | Premier League | 0.624 | 2-24 | Closest to Kane on xG assisted/90 and Avg NP xG/shot. |
| 4 | Aleksandar Mitrović | Newcastle United | Premier League | 0.636 | 2-21 | Closest to Kane on Avg NP xG/shot and xG assisted/90. |
| 5 | Michy Batshuayi Tunga | Olympique de Marseille | Ligue 1 | 0.669 | 2-38 | Closest to Kane on xG assisted/90 and Avg NP xG/shot. |
| 6 | Romelu Lukaku Menama | Everton | Premier League | 0.678 | 2-27 | Closest to Kane on NP xG/90 and Avg NP xG/shot. |
| 7 | Éderzito António Macedo Lopes | Lille | Ligue 1 | 0.687 | 2-28 | Closest to Kane on Avg NP xG/shot and xG assisted/90. |
| 8 | Edin Džeko | AS Roma | Serie A | 0.723 | 3-41 | Closest to Kane on xG assisted/90 and Avg NP xG/shot. |
| 9 | Marco Borriello | Atalanta | Serie A | 0.760 | 3-30 | Closest to Kane on Avg NP xG/shot and xG assisted/90. |
| 10 | Olivier Giroud | Arsenal | Premier League | 0.806 | 9-39 | Closest to Kane on Avg NP xG/shot and NP xG/90. |
| 11 | Andy Delort | Stade Malherbe Caen | Ligue 1 | 0.810 | 3-43 | Closest to Kane on xG assisted/90 and Avg NP xG/shot. |

## Validation

Bootstrap rank intervals use 100 match-resampling iterations. Weight sensitivity checks whether players remain near the top when threat, link play, or pressing receives extra emphasis.

## Limitations

- Historical event-profile similarity only; not a transfer recommendation.
- No contract, wage, age, injury, physical, or scouting-video context.
- League-normalised metrics are relative to the observed open-data cohort.
