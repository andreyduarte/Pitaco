DROP TABLE IF EXISTS notifications;

CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    embedding TEXT NOT NULL
);
