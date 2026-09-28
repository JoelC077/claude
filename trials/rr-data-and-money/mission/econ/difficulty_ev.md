proposal-v0.json (failed trip option B)
| difficulty | fare_full | p_arrive | kit cost | expected fare | net per run | vs Easy |
|---|---|---|---|---|---|---|
| Easy | 1,200 | 0.65 | 90 | 780 | 688 | 1.00x |
| Medium | 1,500 | 0.55 | 210 | 825 | 614 | 0.89x |
| Hard | 1,700 | 0.40 | 515 | 680 | 164 | 0.24x |
| Insane | 1,900 | 0.25 | 780 | 475 | -306 | -0.45x |
ladder: INVERTED at Medium, Hard, Insane (a harder tier pays less than the one below)

proposal-v1.json (failed trip option A)
| difficulty | fare_full | p_arrive | kit cost | expected fare | net per run | vs Easy |
|---|---|---|---|---|---|---|
| Easy | 1,700 | 0.65 | 90 | 1,402 | 1,311 | 1.00x |
| Medium | 2,300 | 0.55 | 210 | 1,782 | 1,571 | 1.20x |
| Hard | 3,100 | 0.40 | 515 | 2,170 | 1,654 | 1.26x |
| Insane | 4,200 | 0.25 | 780 | 2,625 | 1,844 | 1.41x |
ladder: monotonic (harder pays more)

economy.json (failed trip option A)
| difficulty | fare_full | p_arrive | kit cost | expected fare | net per run | vs Easy |
|---|---|---|---|---|---|---|
| Easy | 1,700 | 0.65 | 65 | 1,402 | 1,336 | 1.00x |
| Medium | 2,100 | 0.55 | 141 | 1,628 | 1,485 | 1.11x |
| Hard | 2,650 | 0.40 | 229 | 1,855 | 1,624 | 1.22x |
| Insane | 3,300 | 0.25 | 344 | 2,062 | 1,717 | 1.29x |
ladder: monotonic (harder pays more)

