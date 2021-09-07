# Semi-supervised Data Expansion

## A. Data set

### 1. For Secsion 3

This dataset contains 6,254 parameters excluding 1,071 ones filtered by the hueristics from all 7,325 parameters.

 - __`studied.csv`__: 1292 configuration parameters in the study, the data distribution (of those performance related parameters) is shown in `Table 2`.  
 - __`to_expand.csv`__: 5808 configuration parameters to be expanded follow `Sec.3`.

### 2. For RQ1.2

This file is for easier evaluation in `RQ1.2` -- simulate different proportion of studied data.

 - __`data_all.csv`__: combining `studied.csv` and `to_expand.csv`.  

## B. Expand

You may change the following arguments in `miner.py` to try data expansion.
```python
confidence_threshold = 0.85 # confidence threshold in Fig.3(a)
               scale = 0.20 # p in in Fig.3(b)
```
And run the expansion process (the code is the implementation in `RQ2.2`, which is more flexible):
```bash
python miner.py
```
> This process may be slow, depends on machine.  

When expansion is done, an output folder `expand_out_[mmdd]` will be generated. With in this folder, `RandSeed-x/epoch-i` contains the _i_-th iteration of mining process (will terminate when no new parameter can be expanded) of the _x_-th repeatition (_x_ from 1 to 10 by default)

In `epoch-i`, you can find the following contents:  
 - `patterns_in_text.txt`: the mined rules in this iteration.  
     - Format: `{rule},  type-of-side-effect,  support,  confidence`

       ```
       {('ADP', 'of'),('NOUN', 'resource'),('NOUN', 'amount')},           MoreCost,    6, 0.857
       {('ADP', 'of'),('NOUN', 'type'),('VERB', 'enable'),('ADP', 'by')}, ReduceFunc,  9, 0.900
       {('VERB', 'set'),('NOUN', 'address'),('ADP', 'of')},               Non-Perf,   20, 0.952
       ```  
  - `study_index_epi.npy`: during _i_-th iteration, __SafeTune__ mines patterns from these parameters
  - `successfully_expanded_at_epi.npy`: during _i_-th iteration, which parameters are expanded (including X and y of data).
  - `to_be_expanded_after_epi.npy`: after _i_-th iteration, which parameters are waiting to be expanded.
  - And other files program-friendly files...
