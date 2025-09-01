CREATE DATABASE IF NOT EXISTS LuckySpin;
USE LuckySpin;

CREATE TABLE participant (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    sa_id VARCHAR(13) UNIQUE,
    full_name VARCHAR(100),
    email VARCHAR(50),
    p_password VARCHAR(50),
    balance DECIMAL(9 , 2 ),
    mobile_number VARCHAR(10),
    created_at timestamp,
    last_login timestamp
);
