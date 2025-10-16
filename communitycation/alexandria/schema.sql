CREATE TABLE entry(
    entry_id INTEGER PRIMARY KEY AUTOINCREMENT, 
    title TEXT, 
    body TEXT NOT NULL, 
    --attachments , ? seperate table?    
    platform TEXT NOT NULL, --reddit vs discord, makes differences when reassembling/styling the text! 
    author TEXT,    
    created_at TIMESTAMP                        
);

CREATE TABLE comment(
    comment_id INTEGER,
    entry_id INTEGER, --reference to forum entry 
    parent_id INTEGER, --relevant only if its a comment commenting a comment - that's a whole lotta comments 
    body TEXT, 
    author TEXT, 
    created_at TIMESTAMP, 
    FOREIGN KEY (entry_id) REFERENCES entry(entry_id), 
    FOREIGN KEY  (parent_id) REFERENCES comment(comment_id)

);


CREATE TABLE attachment ( 
    id INTEGER PRIMARY KEY AUTOINCREMENT, 
    entry_id INTEGER, --references id of parent post (which forum entry was this posted in)
    comment_id INTEGER OPTIONAL, --if it wasnt posted inside the original forum entry, but a message in there, this is the one! 
    url TEXT, 
    local_path TEXT, --so where are we storing all of this shit man? 
    filename TEXT, 
    width INTEGER, --needed??
    height INTEGER, --needed?
    FOREIGN KEY (entry_id) REFERENCES entry(entry_id)
    FOREIGN KEY (comment_id) REFERENCES comment(comment_id)
);

