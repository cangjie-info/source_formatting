import pymysql

PUNC_TO_BITMASK = {
        '“': 1, #LEFTQUOTE
        '「': 1,
        '"': 1,
        '‘': 2,    #LEFTINNERQUOTE
        '\'': 2,
        '『': 2,
        '《': 4,    #LEFTTITLE
        '》': 8,    #RIGHTTITLE
        '。': 16,   #PERIOD
        '.': 16,
        '？': 32,   #QUESTION
        '?': 32,
        '！': 64,   #EXCLAMATION
        '!': 64, 
        '、': 128,  #LISTCOMMA
        '，': 256,  #COMMA
        ',': 256, 
        '：': 512,  #COLON
        ':': 512, 
        '’': 1024,  #RIGHTINNERQUOTE
        '』': 1024, 
        '”': 2048,  #RIGHTQUOTE
        '」': 2048}

PREPUNC = '“「"‘\'『《'
POSTPUNC = '》。.？?！!、，,：:’』”」'
PUNC = PREPUNC + POSTPUNC
SENTENCEPUNC = '。.？?！!：:'

def do_sql(sql):
   cursor = db.cursor()
   try:
      cursor.execute(sql)
   except pymysql.IntegrityError as error:
      code, message = error.args
      print("ERROR:", code, message)
      return
   db.commit()

def add_narrative(line):
    sql = 'INSERT '
    sql+= 'INTO narratives(subcontainer_id, number) '
    sql+= 'VALUES ("{}", "{}");'.format(subcontainer_id, narrative_number)
    do_sql(sql)
    return get_insert_id()

def add_text(line):
    global sentence_number
    sentence_number += 1
    sentence = []
    graph_number = 1
    last_graph_in_sentence = False
    index = 0
    while index < len(line):
        graph = ['', 0] #first item in list is the graph, second is punc
        punc = 0
        #get all prepunc
        while index < len(line) and line[index] in PUNC:
            if line[index] in PREPUNC:  #ignore postpunc errors
                punc |= PUNC_TO_BITMASK[line[index]]
            index += 1
        #get graph
        if index < len(line):
            graph[0] = line[index] #if it's not punc, assume it is a graph
            index += 1
        #get all postpunc
        while index < len(line) and line[index] in POSTPUNC:
            punc |= PUNC_TO_BITMASK[line[index]]
            if line[index] in SENTENCEPUNC:
                last_graph_in_sentence = True
            index += 1
        graph[1] = punc
        #graph is done
        sentence.append(graph)
        if last_graph_in_sentence:
            add_sentence(sentence)
            sentence_number += 1
            sentence = []
            graph_number = 1
            last_graph_in_sentence = False
        else:
            graph_number += 1

def add_sentence(sentence):
    sql = 'INSERT '
    sql += 'INTO sentences(narrative_id, number) '
    sql += 'VALUES ("{}", "{}");'.format(narrative_id, sentence_number)
    do_sql(sql)
    global sentence_id
    sentence_id = get_insert_id()
    graph_number = 1
    for graph in sentence:
        sql = 'INSERT '
        sql += 'INTO inscr_graphs(punc, sentence_id, sentence_number, TEST_graph) '
        sql += 'VALUES ("{}", "{}", "{}", "{}");'.format(graph[1],
                sentence_id,
                graph_number,
                graph[0])
        do_sql(sql)
        graph_number += 1

def add_translation_unit(line):
    line = line.replace('"', '\\"')
    sql = 'INSERT '
    sql += 'INTO translation_units(follows_sentence_id, '
    sql += 'translation_text, translation_id) '
    sql += '''VALUES ("{}", "{}", "{}");'''.format(sentence_id,
            line, translation_id)
    do_sql(sql)

def add_subcontainer(line):
    tag, name_zh, name_en = map(str.strip, line.split('\\'))
    sql = 'INSERT '
    sql += 'INTO subcontainers(container_id, name_en, name_zh, number) '
    sql += 'VALUES ("{}", "{}", "{}", "{}");'.format(container_id,
            name_en, name_zh, subcontainer_number)
    do_sql(sql)
    return get_insert_id()

def add_container(line):
   tag, short_name, name_en, name_zh = map(str.strip, line.split('\\'))
   sql = 'INSERT '
   sql += 'INTO containers(short_name, name_en, name_zh) '
   sql += 'VALUES ("{}", "{}", "{}");'.format(short_name, name_en, name_zh)
   do_sql(sql)
   return get_insert_id()

def add_translation(line):
    tag, name_short = map(str.strip, line.split('\\'))
    sql = 'INSERT '
    sql += 'INTO translations(short_name) '
    sql += 'VALUES ("{}");'.format(name_short)
    do_sql(sql)
    return get_insert_id()

def get_insert_id():
   sql = 'SELECT LAST_INSERT_ID();'
   cursor = db.cursor()
   cursor.execute(sql)
   return cursor.fetchone()[0]


db = pymysql.connect(host = 'localhost',
      user = 'python',
      password = 'qazwsx123',
      db = 'ecdb_test',
      charset = 'utf8mb4')

sourcefile = open('mz_extraction1.txt', 'r', encoding='utf-8')

container_id = 0
translation_id = 0
subcontainer_id = 0
subcontainer_number = 0
narrative_id = 0
narrative_number = 0
sentence_id = 0
sentence_number = 0
graph_number = 0
translation = False
line_number = 0
for line in sourcefile:
   line_number += 1
   print(line_number)
   line = line.strip()
   if line == '':
      continue
   if line.startswith('@@container'):
      container_id = add_container(line)
      subcontainer_number = 0
   if line.startswith('@@translation\\'):
       translation_id = add_translation(line)
   elif line.startswith('@@subcontainer'):
      subcontainer_number += 1
      subcontainer_id = add_subcontainer(line)
      narrative_number = 0
   elif line.startswith('@@narrative'):
      narrative_number += 1
      narrative_id = add_narrative(line)
      sentence_number = 0
   elif line.startswith('@@text'):
      translation = False
   elif line.startswith('@@translation_unit'):
      translation = True
   elif translation:
      add_translation_unit(line)
   else:
      add_text(line)
