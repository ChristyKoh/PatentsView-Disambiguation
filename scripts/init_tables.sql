-- initialize tables for USPTO Data
-- download data
CREATE DATABASE patent_20201210;
USE patent_20201210;
CREATE TABLE rawassignee (
    uuid varchar(36) NOT NULL,
    patent_id varchar(20) NOT NULL,
    assignee_id varchar(64) NOT NULL,
    rawlocation_id varchar(128) NOT NULL DEFAULT '',
    type int(4)  NOT NULL DEFAULT 0,
    name_first varchar(64) NOT NULL DEFAULT '',
    name_last varchar(64) NOT NULL DEFAULT '',
    organization varchar(256) NOT NULL DEFAULT '',
    sequence int(11) NOT NULL DEFAULT 1);
CREATE TABLE rawinventor (
    uuid varchar(36) NOT NULL,
    patent_id varchar(20) NOT NULL,
    inventor_id varchar(36) NOT NULL,
    rawlocation_id varchar(128) NOT NULL DEFAULT '',
    name_first varchar(64) NOT NULL DEFAULT '',
    name_last varchar(64) NOT NULL DEFAULT '',
    sequence int(11) NOT NULL DEFAULT 1,
    rule_47 boolean NOT NULL DEFAULT 0);
CREATE TABLE patent (
    id varchar(20) NOT NULL,
    type varchar(100) NOT NULL DEFAULT '',
    number varchar(64) NOT NULL DEFAULT '',
    country varchar(20) NOT NULL DEFAULT '',
    date date NOT NULL,
    abstract mediumtext,
    title mediumtext,
    kind varchar(10) NOT NULL DEFAULT '',
    num_claims int(11) NOT NULL,
    filename varchar(120)  NOT NULL DEFAULT '',
    withdrawn varchar(120) NOT NULL DEFAULT '');

CREATE DATABASE pregrant_publications;
USE pregrant_publications;
CREATE TABLE rawassignee (
    id varchar(128) NOT NULL DEFAULT '',
    document_number bigint(16) NOT NULL,
    sequence int(11) NOT NULL DEFAULT 1,
    name_first varchar(256) NOT NULL DEFAULT '',
    name_last varchar(256) NOT NULL DEFAULT '',
    organization varchar(256) NOT NULL DEFAULT '',
    type int(11) NOT NULL DEFAULT 0,
    city varchar(256) NOT NULL DEFAULT '',
    state varchar(256) NOT NULL DEFAULT '',
    country varchar(256) NOT NULL DEFAULT '',
    filename varchar(16) NOT NULL DEFAULT '');
CREATE TABLE rawinventor (
    id varchar(128) NOT NULL DEFAULT '',
    document_number bigint(16),
    name_first varchar(256) NOT NULL DEFAULT '',
    name_last varchar(256) NOT NULL DEFAULT '',
    sequence int(11) NOT NULL DEFAULT 1,
    designation varchar(32) NOT NULL DEFAULT '',
    deceased boolean NOT NULL DEFAULT 0,
    city varchar(256) NOT NULL DEFAULT '',
    state varchar(256) NOT NULL DEFAULT '',
    country varchar(256) NOT NULL DEFAULT '',
    filename varchar(16) NOT NULL DEFAULT '');
CREATE TABLE application (
    id varchar(128) NOT NULL,
    document_number bigint(16),
    type varchar(20) NOT NULL DEFAULT '',
    application_number varchar(16) NOT NULL DEFAULT '',
    date date NOT NULL,
    country varchar(128) NOT NULL DEFAULT '',
    series_code int(11) NOT NULL DEFAULT 0,
    invention_title mediumtext,
    invention_abstract mediumtext,
    rule_47_flag boolean NOT NULL DEFAULT 0,
    filename varchar(16) NOT NULL DEFAULT '');
