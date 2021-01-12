-- load data from patent_20201210 folder
USE patent_20201210;
LOAD DATA 
INFILE '/Users/koh46433/Christy/PatentsView-Disambiguation/data/patent_20201210/patent.tsv' 
INTO TABLE patent 
FIELDS TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"' 
IGNORE 1 LINES
(id, type, number, country, @date, abstract, title, kind, num_claims, filename, withdrawn)
SET date = IF(@date = '' OR ISNULL(@date), date("9999-12-31"), @date);

LOAD DATA 
INFILE '/Users/koh46433/Christy/PatentsView-Disambiguation/data/patent_20201210/rawassignee.tsv' 
INTO TABLE rawassignee 
FIELDS TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"' 
IGNORE 1 LINES
(uuid, patent_id, assignee_id, rawlocation_id, @type, name_first, name_last, organization, sequence)
SET type = IF(@type = '' OR ISNULL(@type), 0, @type);

LOAD DATA 
INFILE '/Users/koh46433/Christy/PatentsView-Disambiguation/data/patent_20201210/rawinventor.tsv' 
INTO TABLE rawinventor
FIELDS TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"' 
IGNORE 1 LINES
(uuid, patent_id, inventor_id, rawlocation_id, name_first, name_last, sequence, @rule_47, @deceased)
SET rule_47 = IF(@rule_47 = 'FALSE', 0, 1);

-- load pregranted data from the pregranted/ folder
USE pregrant_publications;
LOAD DATA 
INFILE '/Users/koh46433/Christy/PatentsView-Disambiguation/data/pregranted/application.tsv' 
INTO TABLE application
FIELDS TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"' 
IGNORE 1 LINES
(id, document_number, type, application_number, @date, country, series_code, invention_title, invention_abstract, @rule_47, filename)
SET date = IF(@date = '' OR ISNULL(@date), date("9999-12-31"), @date),
rule_47_flag = IF(@rule_47 = 'FALSE', 0, 1);

LOAD DATA 
INFILE '/Users/koh46433/Christy/PatentsView-Disambiguation/data/pregranted/rawassignee.tsv' 
INTO TABLE rawassignee 
FIELDS TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"' 
IGNORE 1 LINES
(id, document_number, sequence, name_first, name_last, organization, @type, city, state, country, filename)
SET type = IF(@type = '' OR ISNULL(@type), 0, @type);

LOAD DATA 
INFILE '/Users/koh46433/Christy/PatentsView-Disambiguation/data/pregranted/rawinventor.tsv' 
INTO TABLE rawinventor
FIELDS TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"' 
IGNORE 1 LINES
(id, document_number, name_first, name_last, sequence, designation, @deceased, city, state, country, filename)
SET deceased = IF(@deceased = 'FALSE', 0, 1);