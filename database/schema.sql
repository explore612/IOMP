CREATE TABLE Project (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    abstract TEXT NOT NULL,
    embedding JSON
);

INSERT INTO project (Title, Abstract) VALUES
('Project Alpha', 'This is the abstract for Project Alpha. It discusses...'),
('Project Beta', 'This is the abstract for Project Beta, focusing on...'),
('Project Gamma', 'This is the abstract for Project Gamma. It covers...');


SELECT * FROM Project