import random
import re
import codecs
import os

REPLACE_TABLE = {
    '\\': '@',
    "'":  '"',
}

def escape(text):
    for x, y in REPLACE_TABLE.iteritems():
        text = text.replace(x, y)
    return text

def convert_lexicon(ifilename, ofilename, sample, romanized=True):
    keys = []
    ifile = codecs.open(ifilename, 'r', 'utf-8')
    ofile = codecs.open(ofilename, 'w', 'utf-8')
    lines = ifile.read().split('\n')[:-1]
    for line in random.sample(lines, sample):
        data = line.strip().split()
        key = data[1 if romanized else 0].strip()
        phones = []
        last = None
        for p in data[2:]:
            if re.match('[0-9\.]+', p):
                continue
            phones.append(p)
        ofile.write(escape(key))
        ofile.write(' ')
        ofile.write(escape(' '.join(phones)))
        ofile.write('\n')
    ofile.close()
        
def train_test(ifilename, test_size):
    ifile = codecs.open(ifilename, 'r', 'utf-8')
    ofilename = '.'.join(ifilename.split('.')[:-1])
    tst_file = codecs.open(ofilename + '.tst', 'w', 'utf-8')
    trn_file = codecs.open(ofilename + '.trn', 'w', 'utf-8')
    
    lines = ifile.read().split('\n')[:-1]
    random.shuffle(lines)
    
    test_lines = int(test_size * len(lines))
    tst_file.write('\n'.join(lines[:test_lines]))
    trn_file.write('\n'.join(lines[test_lines:]))
    tst_file.close()
    trn_file.close()
        
DIALECTS = ['ae', 'eg'] #['ae', 'eg', 'iq', 'ps', 'sy']
SAMPLES = [50, 500, 5000] #[100, 1000, 5000, 10000]
TEST_SIZE = 0.2
        
if __name__ == '__main__':
    for size in SAMPLES:
        for dialect in DIALECTS:
            id = '%s.%s' % (dialect, size)
            print '***', id
            
            ifilename = 'data/lexicons/%s.txt' % dialect
            ofilename = 'data/t2p/roman/%s.txt' % id
            convert_lexicon(ifilename, ofilename, size)
    
            #ifilename = 'data/lexicons/%s.txt' % dialect
            #ofilename = 'data/t2p/arabic/%s.%s.txt' % (dialect, size)
            #convert_lexicon(ifilename, ofilename, size, romanized=False)
    
            cmd = 'perl t2p/t2p_align.pl data/t2p/roman/%s.txt > data/t2p/roman/%s.align' % (id, id)
            print cmd
            os.system(cmd)
            
            print 'split train/test...'
            train_test('data/t2p/roman/%s.align' % id, TEST_SIZE)

            print 'training...'
            cmd = 'perl t2p/con2vec.pl data/t2p/roman/%s.trn > data/t2p/roman/%s.vec' % (id, id)
            print cmd
            os.system(cmd)
            cmd = 'perl t2p/t2p_id3.pl data/t2p/roman/%s.vec > data/dt/roman/%s.dt' % (id, id)
            print cmd
            os.system(cmd)

            print 'testing...'
            cmd = 'perl t2p/t2p_dt.pl data/dt/roman/%s.dt data/t2p/roman/%s.tst > data/dt/roman/base/%s.txt' % (id, id, id)
            print cmd
            os.system(cmd)
