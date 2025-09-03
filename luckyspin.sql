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

CREATE TABLE LottoDraw (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    draw_date TIMESTAMP NOT NULL,
    total_pool DECIMAL(12,2) DEFAULT 0.00
);

-- LottoDraw numbers (ElementCollection)
CREATE TABLE LottoDraw_Numbers (
    draw_id BIGINT NOT NULL,
    number INT NOT NULL,
    PRIMARY KEY (draw_id, number),
    CONSTRAINT fk_draw_numbers FOREIGN KEY (draw_id) REFERENCES LottoDraw(id)
);

-- Game table
CREATE TABLE Game (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    played_at TIMESTAMP NOT NULL,
    wager_amount DECIMAL(9,2) NOT NULL,
    matched_numbers INT NOT NULL,
    winnings DECIMAL(9,2) DEFAULT 0.00,

    -- foreign keys
    player_id INT NOT NULL,
    draw_id BIGINT NOT NULL,

    outcome ENUM('WIN','PARTIAL','LOSS'),

    CONSTRAINT fk_game_player FOREIGN KEY (player_id) REFERENCES participant(id),
    CONSTRAINT fk_game_draw FOREIGN KEY (draw_id) REFERENCES LottoDraw(id)
);

-- Game chosen numbers (ElementCollection)
CREATE TABLE Game_ChosenNumbers (
    game_id BIGINT NOT NULL,
    number INT NOT NULL,
    PRIMARY KEY (game_id, number),
    CONSTRAINT fk_game_numbers FOREIGN KEY (game_id) REFERENCES Game(id)
);
