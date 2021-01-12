CREATE DATABASE patent_benchmark;
USE patent_benchmark;
CREATE TABLE rawassignee (
    patent_number NVARCHAR(100) NOT NULL DEFAULT (''),
    name_first NVARCHAR(500) NOT NULL DEFAULT (''),
    name_last NVARCHAR(500) NOT NULL DEFAULT (''),
    organization VARCHAR(500) NOT NULL DEFAULT (''),
    sequence TINYINT NOT NULL DEFAULT ('0'));
CREATE TABLE rawinventor (
    patent_number NVARCHAR(100) NOT NULL DEFAULT (''),
    name_first NVARCHAR(500) NOT NULL DEFAULT (''),
    name_last NVARCHAR(500) NOT NULL DEFAULT (''),
    city NVARCHAR(500) NOT NULL DEFAULT (''),
    state NVARCHAR(2) NOT NULL DEFAULT (''),
    country NVARCHAR(20) NOT NULL DEFAULT (''),
    id_1 NVARCHAR(100) NOT NULL DEFAULT ('0'),
    id_2 NVARCHAR(100) NOT NULL DEFAULT ('0'),
    sequence TINYINT NOT NULL DEFAULT ('0'));
CREATE TABLE patent (
    patent_number NVARCHAR(100) NOT NULL DEFAULT (''),
    date NVARCHAR(100) NOT NULL DEFAULT ('0'),
    abstract LONGTEXT NOT NULL DEFAULT (''),
    title LONGTEXT NOT NULL DEFAULT (''),
    num_claims INT NOT NULL DEFAULT ('0'));

