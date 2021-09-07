# __Dataset__
Including 8,060 manually labeled configuration parameters, 1,100+ working hours.
You can import this data into a database (`safetune.db`), and we provide several simple sql to see the data distribution.

## __A. Training set__

### 1. All parameters

```sql
SELECT SUM(num) FROM (SELECT software, COUNT(DISTINCT name) AS num FROM configDocs WHERE software<>'spark' AND software<>'squid' AND software<>'postgresql' GROUP BY software);

-- The result would be:
7325
```

### 2. All parameters after filtering

```sql
SELECT count(DISTINCT name) FROM configDocs WHERE filter=0 AND software<>'spark' AND software<>'squid' AND software<>'postgresql';

-- The result would be:
6254
``` 

### 3. All parameters studied  

```sql
SELECT count(*) FROM (SELECT DISTINCT software, name FROM configDocs WHERE software<>'spark' AND software<>'squid' AND software<>'postgresql' AND filter=0 AND study=1);

-- The result would be:
1292
``` 

### 4. Distribution (Table 2)

```sql
SELECT label, count(*) FROM (SELECT DISTINCT software, name, label FROM configDocs WHERE software<>'spark' AND software<>'squid' AND software<>'postgresql' AND study=1) GROUP BY label;

-- The result would be:
Reduced Functionality	138
Limited Side-effect	    126
Performance-unrelated	767
Lower Reliability	    33
Higher Cost			    114
Lower Security	        46
Lower Perf (other user)	68
```

## __B. Testing set__

### All parameters (testing set)

```sql
SELECT SUM(num) FROM (SELECT software, COUNT(DISTINCT name) AS num FROM configDocs WHERE software='spark' OR software='squid' OR software='postgresql' GROUP BY software);

-- The result would be:
735
```
