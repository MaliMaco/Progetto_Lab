CREATE DATABASE IF NOT EXISTS db_progetto
USE db_progetto;

CREATE IF NOT EXISTS 'db_user'@'%' IDENTIFIED BY 'biar';
GRANT ALL PRIVILEGES ON db_progetto.* TO 'db_user'@'%' IDENTIFIED BY 'biar';
FLUSH PRIVILEGES;

CREATE TABLE IF NOT EXISTS web_resources (
    url VARCHAR(2048) NOT NULL,
    domain VARCHAR(255) NOT NULL,
    title VARCHAR(2048) NOT NULL,
    html_text LONGTEXT NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (url(512))
);

CREATE TABLE IF NOT EXISTS gold_standard (
    url VARCHAR(2048) NOT NULL,
    gold_text LONGTEXT,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (url(512)),
    FOREIGN KEY (url(512)) REFERENCES web_resources(url(512))
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evaluations (
    url VARCHAR(2048) NOT NULL,
    precision_score FLOAT NOT NULL,
    recall_score FLOAT NOT NULL,
    f1_score FLOAT NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (url(512)),
    FOREIGN KEY (url(512)) REFERENCES web_resources(url(512))
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS llm_judgments (
    url VARCHAR(2048) NOT NULL,
    score FLOAT,
    verdict TEXT,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (url(512)),
    FOREIGN KEY (url(512)) REFERENCES web_resources(url(512))
        ON DELETE CASCADE
);