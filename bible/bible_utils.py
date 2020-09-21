# -*- coding: utf-8 -*-
"""
Created on Wed Apr 22 22:27:17 2020

@author: Kidus
"""
from bs4 import BeautifulSoup
import re
import io
import os
from collections import OrderedDict
import sqlite3


books = dict()
script_path = os.path.dirname(os.path.realpath(__file__))

class InvalidFormatException(Exception): pass
class InvalidBookException(Exception): pass
class InvalidVerseException(Exception): pass

def verse_to_index(query, books):
    parts = query.strip().split()
    if len(parts) == 3: parts= [' '.join(parts[0:2])] + parts[2:]
    if ':' in parts[1]:
        parts = parts[:1] + parts[1].split(":")
    print(parts)
    parts[0] = books[parts[0].title()]
    return ":".join(parts)

def index_to_verseid(index, books):
    verse = index.split(":")
    for name, num in books.items():
        if num == verse[0]: verse[0] = name; break;
    return verse[0] + " " + ':'.join(verse[1:])

def default_lang(user_id):
    db = sqlite3.connect("saves.db")
    lang = db.execute("SELECT lang FROM users WHERE id = ?", (int(user_id),) ).fetchone()[0]
    db.close()
    if lang == 0: return 'am'
    else: return 'en'
    
def change_lang(user_id, language):
    db = sqlite3.connect("saves.db")
    lang = 0 if language == 'am' else 1
    db.execute("UPDATE users SET lang = ? WHERE id = ?", (lang, int(user_id)))
    db.commit()
    db.close()
    
    
    
    
def get_verse(query, books, user_id):
    if default_lang(user_id) == 'am': 
        return get_verse_am(query, books)
    else:
        return get_verse_en(query, books)


def get_verse_en(query, books):
    parts = list()
    try:
        parts = query.strip().split()
        
        if len(parts) == 3: 
            parts= [' '.join(parts[0:2])] + parts[2:]
            
        if ':' in parts[1]:
            parts = parts[:1] + parts[1].split(":")
            #These next lines check that the chapter and verses are integers
            a = int(parts[1])
            if '-' in parts[-1]: 
                a = int(parts[-1].split('-')[0]), int(parts[-1].split('-')[1])
            else: 
                a = int(parts[-1])
        else:
            a = int(parts[1])
    except Exception as e:
        print(e)
        raise InvalidFormatException(query)
    
    if not (parts[0].title() in books): raise InvalidBookException(query)
    
    db = sqlite3.connect("nkjv.db")
    if '-' in parts[-1]:
        start, end = parts[-1].split('-')
        start, end = int(start), int(end)
        result = str()
        for verse in range(start, end+1):
            temp = db.execute( "SELECT text FROM bible WHERE book = ? AND \
                            chapter = ? AND verse = ?", (parts[0].title(), 
                            int(parts[1]), verse) ).fetchone()
            if not temp: raise InvalidVerseException(query) 
            result += temp[0] +  "\n"    
        db.close()
        
        return result
            
    else:
        result = db.execute( "SELECT text FROM bible WHERE book = ? AND \
                            chapter = ? AND verse = ?", (parts[0].title(), 
                            int(parts[1]), int(parts[2])) ).fetchone()
        db.close()
        if not result: raise InvalidVerseException(query)
        else: return result[0]
    
    pdb.set_trace()
    

def get_verse_am(query, books):
    parts = list()
    try:
        parts = query.strip().split()
        
        if len(parts) == 3: 
            parts= [' '.join(parts[0:2])] + parts[2:]
            
        if ':' in parts[1]:
            parts = parts[:1] + parts[1].split(":")
            #These next lines check that the chapter and verses are integers
            a = int(parts[1])
            if '-' in parts[-1]: a = int(parts[-1].split('-')[0]), int(parts[-1].split('-')[1])
            else: a = int(parts[-1])
        else:
            a = int(parts[1])                
        del(a)
    except Exception as e:
        print(e)
        raise InvalidFormatException(query)
    bib = list()
    try:
        path = os.path.join(script_path, "am_new", books[parts[0].title()], parts[1] + ".htm")
        bib = parse_bible(path)
    except Exception as e:
        print(e)
        raise InvalidBookException(query)
    final = str()
    try:
        if(len(parts) == 2):
            final = '\n'.join(bib)
        elif '-' in parts[-1]: #Get a verse that spans multiple verses
            begin = int(parts[-1].split('-')[0])
            end = int(parts[-1].split('-')[1])
            for i in range(begin-1,end):
                final += bib[i] + "\n"
        else: final = bib[int(parts[-1])-1] + "\n"
    except Exception as e:
        print(e)
        raise InvalidVerseException(query)
    
    return final

def parse_dir(filepath, outfilepath):
    global books
    index_books("books.txt")
    line_list = list()
    with open(filepath) as lines_file:
        for line in lines_file:
            line_list.append(line.replace("\n", "").split(":"))

    with io.open(outfilepath, 'w', encoding='utf-8') as out:
        for line in line_list:
            out.write(books[line[0]] + ":" + line[1] + ":" + line[2] + "\n")
            path = "am_new/" + line[0] +"/" + line[1] + ".htm"
            bib = parse_bible(path)
            final = str()
            if not '-' in line[2]:
                final = bib[int(line[2])-1] + "\n"
            else:
                begin = int(line[2].split('-')[0])
                end = int(line[2].split('-')[1])
                for i in range(begin-1,end):
                    final += bib[i] + "\n"
            out.write(final)
            out.write("\n\n")


    # print(line_list)



def parse_bible(filepath):

    with open(filepath, encoding='utf-8') as parsed_file:
        contents = parsed_file.read()
        bs  = BeautifulSoup(contents, 'lxml')
        bs.find('div', {'class':'textBody'})
        trial = bs.find('div', {'class':'textBody'})
        trial2 = trial.findAll('p')
        final = re.sub(r'<.{1,30}>','', str(trial2))
        final = final.replace('[', '')
        final = final.replace(']', '')
        final_list = final.split('\n')
        final_final_list = final_list.copy()
        counter = 0
        for index, value in enumerate(final_list):
            try:
                int1 = int(value.split()[0])
                int2 = int(value.split()[1])
                int3 = None
                try:
                    int3 = int(value.split()[2])
                except:
                    pass
                diff = (int3-int1) if int3 else (int2-int1)
                for i in range(diff):
                    final_final_list.insert(index+counter+1, ' ')
                    counter += 1
            except:
                continue
        return final_final_list


def index_books(filename):
    global books
    with open(filename, encoding='utf-8') as books_text:
        for index, line in enumerate(books_text):
            books[str(index+1)] = line.strip()

def index_books_en(filename):
    books = OrderedDict()
    with open(filename) as books_text:
        for index, line in enumerate(books_text):
            books[line.strip().title()] = str(index+1)

    return books

