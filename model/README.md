# Identifying Performance-related Parameters & Side-effects



## Embedding & Balancing

```
python3 embedding\ &\ balancing.py
```
__Caution__: this produce a huge training data csv file (3GB), so we cannot upload it into this repository

## Training the model & Prediect tuning guidance
```
Rscript model.R
```
Then the result can be seen in the result file.

## Result in detail

| PostgreSQL     | Precision | Recall   |
|----------------|-----------|----------|
| _Performance_    | 0.84323  | 0.72512  |
| _NonPerformance_ | 0.89212   | 0.78854  |
| __Overall__        | __0.873__     | __0.764__    |

| PostgreSQL     | Precision | Recall   |
|----------------|-----------|----------|
| _MoreCost_       | 0.85213   | 0.72348 |
| _LowSecure_      | 0.73903   | 0.53672  |
| _LowReliable_    | 0.75912   | 0.57865  |
| _Limit_          | 0.78323   | 0.63464  |
| _WorkloadSpec_   | 0.82516   | 0.66321  |
| _ReduceFunc_     | 0.81954   | 0.55267  |
| __Overall__        | __0.812__     | __0.629__    |

| Squid          | Precision | Recall  |
|----------------|-----------|---------|
| _Performance_    | 0.83921   | 0.63216 |
| _NonPerformance_ | 0.89053   | 0.58916 |
| __Overall__        | __0.872__     | __0.602__   |

| Squid          | Precision | Recall  |
|----------------|-----------|---------|
| _MoreCost_       | 0.91534   | 0.71035 |
| _LowSecure_      | 0.68349   | 0.56385 |
| _LowReliable_    | 0.63821   | 0.60123 |
| _Limit_          | 0.83726   | 0.62892 |
| _WorkloadSpec_   | 0.80021   | 0.64657 |
| _ReduceFunc_     | 0.78429   | 0.59249 |
| __Overall__        | __0.830__      | __0.623__   |

| Spark          | Precision | Recall   |
|----------------|-----------|----------|
| _Performance_    | 0.79942   | 0.656294 |
| _NonPerformance_ | 0.80141   | 0.673494 |
| __Overall__        | __0.801__     | __0.669__    |

| Squid          | Precision | Recall   |
|----------------|-----------|----------|
| _MoreCost_       | 0.85204   | 0.73207  |
| _LowSecure_      | 0.68032   | 0.57088  |
| _LowReliable_    | 0.69294   | 0.62737  |
| _Limit_          | 0.78437   | 0.70126  |
| _WorkloadSpec_   | 0.83526   | 0.70317  |
| _ReduceFunc_     | 0.75889   | 0.56825  |
| __Overall__        | __0.792__     | __0.651__    |