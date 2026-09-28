# Sweeps (SYNTHETIC proposal; econ.py sim --sweep, reduced sample: installs/3, 300 engaged players)

## proposal-v0.json --sweep unlocks.0.price=2500,3000,4000

| unlocks.0.price | runs to 1st | min to 1st | day-0 reach | median h per unlock | sink/src | payer conv | earned ARPDAU |
|---|---|---|---|---|---|---|---|
| 2500 | 4.0 | 54 | 13% | 0.9 / 5.0 / 11.5 / - / - | 0.44 | 0.47% | 0.974 |
| 3000 | 5.0 | 68 | 8% | 1.1 / 5.2 / 11.5 / - / - | 0.39 | 0.54% | 1.051 |
| 4000 | 6.0 | 81 | 2% | 1.4 / 5.8 / 11.0 / - / - | 0.33 | 0.67% | 1.323 |

## proposal-v0.json --sweep failed_trip.option=A,B,C

| failed_trip.option | runs to 1st | min to 1st | day-0 reach | median h per unlock | sink/src | payer conv | earned ARPDAU |
|---|---|---|---|---|---|---|---|
| A | 5.0 | 68 | 3% | 1.1 / 3.4 / 9.2 / - / - | 0.32 | 0.51% | 1.038 |
| B | 6.0 | 81 | 2% | 1.4 / 5.8 / 11.0 / - / - | 0.33 | 0.67% | 1.323 |
| C | 6.0 | 81 | 2% | 1.4 / 4.3 / 11.0 / - / - | 0.32 | 0.53% | 1.133 |

## proposal-v0.json --sweep difficulty.Easy.fare_full=1200,1500,1700

| difficulty.Easy.fare_full | runs to 1st | min to 1st | day-0 reach | median h per unlock | sink/src | payer conv | earned ARPDAU |
|---|---|---|---|---|---|---|---|
| 1200 | 6.0 | 81 | 2% | 1.4 / 5.8 / 11.0 / - / - | 0.33 | 0.67% | 1.323 |
| 1500 | 6.0 | 81 | 6% | 1.4 / 4.7 / 10.8 / - / - | 0.37 | 0.43% | 0.744 |
| 1700 | 5.0 | 68 | 8% | 1.1 / 4.3 / 10.8 / - / - | 0.35 | 0.39% | 0.733 |

## proposal-v0.json --sweep prices.coal=40,60,80

| prices.coal | runs to 1st | min to 1st | day-0 reach | median h per unlock | sink/src | payer conv | earned ARPDAU |
|---|---|---|---|---|---|---|---|
| 40 | 6.0 | 81 | 2% | 1.4 / 5.4 / 11.2 / - / - | 0.30 | 0.45% | 0.927 |
| 60 | 6.0 | 81 | 2% | 1.4 / 5.8 / 11.0 / - / - | 0.33 | 0.67% | 1.323 |
| 80 | 7.0 | 94 | 2% | 1.6 / 6.1 / 11.5 / - / - | 0.32 | 0.48% | 1.011 |

## proposal-v1.json --sweep difficulty.Easy.fare_full=1700,1800,1900

| difficulty.Easy.fare_full | runs to 1st | min to 1st | day-0 reach | median h per unlock | sink/src | payer conv | earned ARPDAU |
|---|---|---|---|---|---|---|---|
| 1700 | 3.0 | 40 | 40% | 0.7 / 2.5 / 4.5 / 7.2 / 9.9 | 0.51 | 0.51% | 1.050 |
| 1800 | 2.0 | 27 | 43% | 0.5 / 2.2 / 4.5 / 7.0 / 10.1 | 0.51 | 0.63% | 1.322 |
| 1900 | 2.0 | 27 | 46% | 0.5 / 2.2 / 4.3 / 6.8 / 9.7 | 0.52 | 0.45% | 0.976 |

## proposal-v1.json --set start_coins=N (full sim, reports in data/econ/sweeps/)
- start_coins=100: | runs started short of the supply kit | 2% | ;  PASS | loco_2: median 2.0 runs / 27 min (p90 3.0 runs); target about 2 runs inside 30 min 
- start_coins=200: | runs started short of the supply kit | 2% | ;  PASS | loco_2: median 2.0 runs / 27 min (p90 3.0 runs); target about 2 runs inside 30 min 
