import os
from bible.bible_utils import verse_to_index, index_books_en, index_to_verseid, get_verse
from random import randint
import sqlite3
import pdb




DEV = 447076481
en_books = index_books_en(os.path.join("bible", "books_en.txt"))

class NoSuchVerseException(Exception): pass
class NotTrainingException(Exception): pass
class NoVersesException(Exception): pass

def add_user(user_id):
    db = sqlite3.connect("saves.db")
    
    db.execute("INSERT INTO users (id) VALUES (?)", (int(user_id),))
    db.commit(); db.close()


def add_verse(user_id, verse_id):
    db = sqlite3.connect("saves.db")
    verse_index = verse_to_index(verse_id, en_books)
    
    if not len(db.execute("SELECT * FROM saves WHERE (user_id = ?) AND (verse_index = ?)",
               (int(user_id), verse_index)).fetchall()):
        
        db.execute("INSERT INTO saves (user_id, verse_id, verse_index) VALUES (?,?,?)"
                   , (int(user_id), verse_id.title(), verse_index))
        db.commit(); db.close();
    
    else: 
        db.commit(); db.close();
        return -1;
    
def remove_verse(user_id, verse_id):
    db = sqlite3.connect("saves.db")
    if not len(db.execute("SELECT * FROM saves WHERE (user_id = ?) AND (verse_id = ?)",
                       (user_id, verse_id)).fetchall()):
        db.commit(); db.close()
        raise NoSuchVerseException();
    
    db.execute("DELETE FROM saves WHERE (user_id = ?) AND (verse_id = ?)", 
               (user_id, verse_id))
    db.commit(); db.close()
    
    
def get_all_verses(user_id):
    db = sqlite3.connect("saves.db")
    verses = list(db.execute("SELECT verse_id FROM saves WHERE user_id = ?", (user_id,)))
    verses = [verse[0] for verse in verses]
    db.commit(); db.close()
    return '\n'.join(verses)
    
        
def update_state(user_id, training): #training can be 0, 1, 2: not training, training personal, training default
    db = sqlite3.connect("saves.db")    
    db.execute("UPDATE users SET training = ? WHERE id = ?",(int(training)%2, int(user_id)))
    db.commit(); db.close()

def get_status(user_id):
    db = sqlite3.connect("saves.db")
    temp = list(db.execute("SELECT training FROM users WHERE id = ?", (user_id,)))[0][0]
    db.commit(); db.close()
    return temp

def get_next_verse(user_id):
    status = get_status(user_id)
    
    #make sure the user is in training and they have verses saved
    if not status: raise NotTrainingException()
    if not len(get_all_verses(user_id)): raise NoVersesException()
    
    db = sqlite3.connect("saves.db")
    current_verse = db.execute("SELECT current_verse FROM users WHERE id = ?", 
                               (int(user_id),) ).fetchall()
    print("Current verse: ", current_verse)
    if current_verse[0][0]:
        db.execute("UPDATE users SET current_verse = NULL WHERE id = ?", (int(user_id),) )
        db.commit(); db.close();
        return current_verse[0][0]
    
    else:
        available = db.execute("SELECT verse_id FROM saves WHERE (user_id = ?)\
                                    AND seen = 0", (int(user_id),) ).fetchall()
        available = [item[0] for item in available]
        print("Available: ", available)
        if len(available):
            rand_verse = available[randint(0,len(available)-1)]
            db.execute("UPDATE saves SET seen = 1 WHERE (user_id = ?) AND (verse_id = ?)"
                       , (int(user_id), rand_verse) )
            
            db.execute("UPDATE users SET current_verse = ? WHERE id = ?",
                       (rand_verse, int(user_id)) )
            db.commit(); db.close();
            return get_verse(rand_verse, en_books)
        else:
            db.execute("UPDATE saves SET seen = 0 WHERE (user_id = ?)", (int(user_id),) )
            db.commit(); db.close();
            return get_next_verse(user_id)

def clear_training(user_id):
    
    db = sqlite3.connect("saves.db")
    db.execute("UPDATE saves SET seen = 0 WHERE user_id = ?", (int(user_id,),) )
    db.execute("UPDATE users SET current_verse = NULL WHERE id = ?", (int(user_id),) )
    db.commit(); db.close();
        


        