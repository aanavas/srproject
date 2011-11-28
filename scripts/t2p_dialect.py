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
SAMPLES = [100, 1000, 10000]#, 1250, 12500] #[100, 1000, 5000, 10000]
TEST_SIZE = 0.2
        
if __name__ == '__main__':
    for size in SAMPLES:
        trn_filename = 'data/t2p/roman/all.%s.vec' % size
        trn_file = codecs.open(trn_filename, 'w', 'utf-8')

        #tst_filename = 'data/t2p/roman/all.%s.tst' % size
        #tst_file = codecs.open(tst_filename, 'w', 'utf-8')
        
        for dialect in DIALECTS:
            id = '%s.%s' % (dialect, size)
            print '***', id
            
            ifilename = 'data/lexicons/%s.txt' % dialect
            ofilename = 'data/t2p/roman/%s.txt' % id
            sample_size = int((size*(1+TEST_SIZE))/len(DIALECTS))
            convert_lexicon(ifilename, ofilename, sample_size)
    
            #ifilename = 'data/lexicons/%s.txt' % dialect
            #ofilename = 'data/t2p/arabic/%s.%s.txt' % (dialect, size)
            #convert_lexicon(ifilename, ofilename, size, romanized=False)
    
            cmd = 'perl t2p/t2p_align.pl data/t2p/roman/%s.txt > data/t2p/roman/%s.align' % (id, id)
            print cmd
            os.system(cmd)
            
            print 'split train/test...'
            train_test('data/t2p/roman/%s.align' % id, TEST_SIZE)

            print 'extracting features...'
            cmd = 'perl t2p/con2vec.pl data/t2p/roman/%s.trn > data/t2p/roman/%s.vec' % (id, id)
            print cmd
            os.system(cmd)
            
            vec = codecs.open('data/t2p/roman/%s.vec' % id, 'r', 'utf-8')
            for line in vec:
                trn_file.write(dialect.upper() + ' ' + line)

            #tst = codecs.open('data/t2p/roman/%s.tst' % id, 'r', 'utf-8')
            #for line in tst:
            #    tst_file.write(dialect.upper() + ' ' + line)
        
        trn_file.close()
        #tst_file.close()

        print 'training...'
        cmd = 'perl t2p/t2pd_id3.pl %s > data/dt/roman/all.%s.dt' % (trn_filename, size)
        print cmd
        os.system(cmd)

        for dialect in DIALECTS:
            id = '%s.%s' % (dialect, size)
            
            print 'testing...'
            cmd = 'perl t2p/t2pd_dt.pl data/dt/roman/all.%s.dt data/t2p/roman/%s.tst %s > data/dt/roman/dialect/%s.txt' % (size, id, dialect.upper(), id)
            print cmd
            os.system(cmd)
    
            print 'output (%s)...' % dialect
            cmd = 'perl t2p/t2pd_out.pl data/dt/roman/all.%s.dt data/lexicons/%s.txt %s > data/dt/lexicons/%s.txt' % (size, dialect, dialect.upper(), id)
            print cmd
            os.system(cmd)
