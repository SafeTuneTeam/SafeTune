# Artifacts of __SafeTune__
This repository includes the artifacts (including data and source code) of the our paper: "_Multi-Intention Aware Configuration Selection for Performance Tuning_"

The repository includes the following artifacts:
 - `dataset`: Section 2. Understanding Side-effects
   - labeled dataset including 7,325 parameters from 13 software covering four software domains
   - labeled dataset including 735 parameters from PostgreSQL, Squid, Spark (in RQ1)
 - `expansion`: Section 3. Semi-supervised Data Expansion
   - source code
   - small-scaled labeled data (1,292 parameters) to be expanded 
   - rules mined and new data expanded at each iteration  
   - domain-specific synonym list retrived from the study in Section 2 and supplemented from wiki.  
   - results including how many & how accurate are the new data  
 - `model`: Section 4. Learning Based Model to Predict Tuning Guidance
   - source code
   - training data (24,528 pieces, obtained after expansion)
   - testing data (735 parameters from PostgreSQL, Squid, Spark)
 - `comparing_existing`: RQ2. Comparing __SafeTune__ with State-of-art-tool
   - scripts and commands to validate the parameters missed by the existing work do have performance impacts
   - results including
     - performance impact of each parameter
     - __FULL__ comparision between __SafeTune__ and [the existing work](https://www.usenix.org/conference/hotstorage20/presentation/kanellis)
     - all the inital testing results, by which we get the evaluation result in RQ2 
 - `case_study`: RQ3. Effectiveness of __SafeTune__ in Helping [__OtterTune__](https://github.com/cmu-db/ottertune)
   - the other four cases that are not present in the paper due to the limited space
