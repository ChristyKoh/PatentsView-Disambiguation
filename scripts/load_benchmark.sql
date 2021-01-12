-- load benchmark data
LOAD DATA 
INFILE '/Users/koh46433/Downloads/drive-download-20201230T181912Z-001/training_data/td_patent.csv' 
INTO TABLE patent 
FIELDS TERMINATED BY ',' 
OPTIONALLY ENCLOSED BY '"' 
IGNORE 1 LINES
(patent_number,@date,abstract,title,num_claims) 
SET date = IF(@date='',0,@date);

LOAD DATA INFILE '/Users/koh46433/Downloads/drive-download-20201230T181912Z-001/training_data/td_assignee.csv' INTO TABLE rawassignee FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' IGNORE 1 LINES;
LOAD DATA INFILE '/Users/koh46433/Downloads/drive-download-20201230T181912Z-001/training_data/td_inventor.csv' INTO TABLE rawinventor FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' IGNORE 1 LINES;