import codecs
import os
import random
import sys

def escape_char(x):
    return x.upper() if x == x.lower() else '^' + x.upper()

def escape_str(s):
    if '^' in s:
        print 'ERROR: ^ appears in string:', s
    return ''.join([escape_char(x) for x in s])

def get_transcription(filename):
    ifile = codecs.open(filename, 'r', 'utf-8')
    data = ifile.read().split(" --#-- ")
    ifile.close()
    trans = escape_str(data[1].strip())
    return trans

def get_lexicon(filename, phones):
    keys = []
    lexicon = {}
    ifile = codecs.open(filename, 'r', 'utf-8')
    for line in ifile:
        data = line.strip().split()
        key = escape_str(data[1].strip())
        if key in lexicon: continue
        keys.append(key)
        lex_trans = [escape_str(p) for p in data[2:]]
        lexicon[key] = ' '.join([p for p in lex_trans if p in phones])
    return (keys, lexicon)

def get_phones(filename):
    phones = []
    ifile = codecs.open(filename, 'r', 'utf-8')
    parsing = False
    for line in ifile:
        line = line.strip()
        if not parsing and 'Unique Phones' in line:
            parsing = True
            continue
        if len(line) == 0 or not parsing:
            continue
        data = escape_str(line).split()
        phones.append(data[0])
    return phones


def prepare_files(task, raw_paths, files, name, transcriptions, replace):
    print 'Preparing %s files...' % name
    ids_filename = os.path.join(task, 'etc', '%s_%s.fileids' % (task, name))
    ids_file = codecs.open(ids_filename, 'w', 'utf-8')

    trn_filename = os.path.join(task, 'etc', '%s_%s.transcription' % (task, name))
    trn_file = codecs.open(trn_filename, 'w', 'utf-8')

    for task_wav in files:
        task_path = os.path.join(task, 'wav', task_wav)
        raw_path = raw_paths[task_wav]
        if replace:
            command = 'cp %s %s' % (raw_path, task_path)
            #print command
            os.system(command)

        task_path = task_wav.replace('.sph', '')
        ids_file.write('%s\n' % task_path)
        trn_file.write('<S> %s </S> (%s)\n' % (transcriptions[task_wav], task_path))
        
    ids_file.close()
    trn_file.close()
        
def prepare_data(dialect, ctype, task, replace):
    transcriptions = {}
    raw_paths = {}
    task_files = []
    
    print 'Reading raw data...'
    raw_lex_dir = os.path.join('raw', 'lexicons', dialect)
    lexicon_files = [None, None]
    for filename in os.listdir(raw_lex_dir):
        pos = 1 if filename.startswith('README') else 0
        lexicon_files[pos] = os.path.join(raw_lex_dir, filename)

    phones = get_phones(lexicon_files[1])
    (words, lexicon) = get_lexicon(lexicon_files[0], phones)
    
    raw_audio_dir = os.path.join('raw', 'audio', dialect, ctype)
    raw_trans_dir = os.path.join('raw', 'transcriptions', dialect, ctype)
    for session in sorted(os.listdir(raw_audio_dir)):
        session_dir = os.path.join(raw_audio_dir, session)
        for wav in sorted(os.listdir(session_dir)):
            raw_path = os.path.join(session_dir, wav)
            task_wav = session + '_' + wav + '.sph' 
        
            trans_file = os.path.join(raw_trans_dir, session, wav[:-1]+'O')
            if not os.path.exists(trans_file): 
                #print 'ERROR: File not exists:', trans_file
                continue
            trans = get_transcription(trans_file)
            
            error = False
            for word in trans.split():
                if word not in lexicon:
                    #print 'ERROR:', word, 'not in lexicon; ignoring:', raw_path
                    error = True
                    break
            if error:
                continue

            task_files.append(task_wav)
            transcriptions[task_wav] = trans
            raw_paths[task_wav] = raw_path
            
    sample_size = int(0.9 * len(task_files))
    train_files = sorted(random.sample(task_files, sample_size))
    test_files = sorted(list(set(task_files) - set(train_files)))
    
    task_dic_filename = os.path.join(task, 'etc', '%s.dic' % task)
    print 'Writing %s...' % task_dic_filename
    task_dic = codecs.open(task_dic_filename, 'w', 'utf-8')
    for word in words:
        task_dic.write('%-40s %s\n' % (word, lexicon[word]))
    task_dic.close()
    
    filler_dic = os.path.join('formatter', 'xx.filler')
    task_filler_dic = os.path.join(task, 'etc', '%s.filler' % task)
    print 'Writing %s...' % task_filler_dic
    command = 'cp %s %s' % (filler_dic, task_filler_dic)
    print command
    os.system(command)

    phone_dic_filename = os.path.join(task, 'etc', '%s.phone' % task)
    print 'Writing %s...' % phone_dic_filename
    phone_dic = codecs.open(phone_dic_filename, 'w', 'utf-8')
    phones.append('SIL')
    for phone in sorted(phones):
        phone_dic.write('%s\n' % phone)
    phone_dic.close()

    task_txt_filename = os.path.join(task, 'etc', '%s.txt' % task)
    print 'Writing %s...' % task_txt_filename
    task_txt = codecs.open(task_txt_filename, 'w', 'utf-8')
    utrans = set(transcriptions.itervalues())
    for trans in utrans:
        task_txt.write('<S> %s </S>\n' % trans)
    task_txt.close()

    prepare_files(task, raw_paths, train_files, 'train', transcriptions, replace)
    prepare_files(task, raw_paths, test_files, 'test', transcriptions, replace)
    
    
if __name__ == '__main__':
    DIALECT = sys.argv[1]
    CTYPE = sys.argv[2]
    TASK = sys.argv[3]
    REPLACE = sys.argv[4].lower() == 'true'
    
    prepare_data(DIALECT, CTYPE, TASK, REPLACE)
