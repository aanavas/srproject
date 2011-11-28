import random
import re
import codecs
import os

REPLACE_TABLE = {
    '\\': '@',
    "'":  '"',
}

UNREPLACE_TABLE = {
    '@': '\\',
    '"':  "'",
}

def escape(text, table=REPLACE_TABLE):
    for x, y in table.iteritems():
        text = text.replace(x, y)
    return text

def convert_lexicon(ifilename, ofilename, sample=None, romanized=True):
    keys = []
    ifile = codecs.open(ifilename, 'r', 'utf-8')
    ofile = codecs.open(ofilename, 'w', 'utf-8')
    lines = ifile.read().split('\n')[:-1]
    for line in random.sample(lines, sample) if sample else lines:
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
    
def escape_lexicon(ifilename, ofilename, table):
    ifile = codecs.open(ifilename, 'r', 'utf-8')
    ofile = codecs.open(ofilename, 'w', 'utf-8')
    lines = ifile.read().split('\n')[:-1]
    for line in lines:
        ofile.write(escape(line, table))
        ofile.write('\n')
    ofile.close()
        
def split_file(ifilename, ofile1, ofile2, split_size):
    ifile = codecs.open(ifilename, 'r', 'utf-8')
    tst_file = codecs.open(ofile1, 'w', 'utf-8')
    if ofile2: trn_file = codecs.open(ofile2, 'w', 'utf-8')
    
    lines = ifile.read().split('\n')[:-1]
    random.shuffle(lines)
    
    tst_file.write('\n'.join(lines[:split_size+1]))
    if ofile2: trn_file.write('\n'.join(lines[split_size:]))
    tst_file.close()
    if ofile2: trn_file.close()
        
DIALECTS = ['ae', 'eg'] #['ae', 'eg', 'iq', 'ps', 'sy']
SAMPLES = [100, 1000, 10000]#, 1250, 12500] #[100, 1000, 5000, 10000]
TEST_SIZE = 1000
        
if __name__ == '__main__':
    for dialect in DIALECTS:
        input_file = 'data/lexicons/%s.txt' % dialect
        roman_file = 'data/lexicons/roman/%s.txt' % dialect
        
        if not os.path.exists(roman_file):
            print 'extracting romanized version (%s)...' % dialect
            convert_lexicon(input_file, roman_file)

        train_file = 'data/t2p/train/%s.txt' % dialect
        test_file = 'data/t2p/test/%s.txt' % dialect
        
        if not os.path.exists(train_file) or not os.path.exists(test_file):
            print 'split train/test...'
            split_file(roman_file, test_file, train_file, TEST_SIZE)

        test_align_file = 'data/t2p/test/%s.align' % dialect
        if not os.path.exists(test_align_file):
            print 't2p test alignment (%s)...' % dialect
            cmd = 'perl t2p/t2p_align.pl %s > %s' % (test_file, test_align_file)
            print cmd
            os.system(cmd)

        for size in SAMPLES:
            sample_file = 'data/t2p/train/%s.%s.txt' % (dialect, size)
            if not os.path.exists(sample_file):
                print 'sampling training file (%s.%s)...' % (dialect, size)
                split_file(train_file, sample_file, None, size)

            align_file = 'data/t2p/train/%s.%s.align' % (dialect, size)
            if not os.path.exists(align_file):
                print 't2p alignment (%s.%s)...' % (dialect, size)
                cmd = 'perl t2p/t2p_align.pl %s > %s' % (sample_file, align_file)
                print cmd
                os.system(cmd)
            
            vec_file = 'data/t2p/train/%s.%s.vec' % (dialect, size)
            if not os.path.exists(vec_file):
                print 'extracting features (%s.%s)...' % (dialect, size)
                cmd = 'perl t2p/con2vec.pl %s > %s' % (align_file, vec_file)
                print cmd
                os.system(cmd)
            
            dt_file = 'data/t2p/dt/base/%s.%s.dt' % (dialect, size)
            if not os.path.exists(dt_file):
                print 'training decision tree (%s.%s)...' % (dialect, size)
                cmd = 'perl t2p/t2p_id3.pl %s > %s' % (vec_file, dt_file)
                print cmd
                os.system(cmd)
                
            print 'testing decision tree (%s.%s)...' % (dialect, size)
            cmd = 'perl t2p/t2p_dt.pl %s %s' % (dt_file, test_align_file)
            print cmd
            os.system(cmd)

    for dialect in DIALECTS:
        for size in SAMPLES[:-1]:
            test_align_file = 'data/t2p/test/%s.align' % dialect
            train_filename = 'data/t2p/train/dialect/%s.%s.vec' % (dialect, size)
            
            if not os.path.exists(train_filename):
                print 'creating multi-dialect training file (%s.%s)...' % (dialect, size)
                train_file = codecs.open(train_filename, 'w', 'utf-8')
                
                vec_file = 'data/t2p/train/%s.%s.vec' % (dialect, size)
                for line in codecs.open(vec_file, 'r', 'utf-8'):
                    train_file.write(dialect.upper() + ' ' + line)
                    
                for other_dialect in DIALECTS:
                    if dialect == other_dialect:
                        continue
                    
                    vec_file = 'data/t2p/train/%s.%s0.vec' % (dialect, size)
                    for line in codecs.open(vec_file, 'r', 'utf-8'):
                        train_file.write(other_dialect.upper() + ' ' + line)
                
                train_file.close()

            dt_file = 'data/t2p/dt/dialect/%s.%s.dt' % (dialect, size)
            if not os.path.exists(dt_file):
                print 'training multi-dialect decision tree (%s.%s)...' % (dialect, size)
                cmd = 'perl t2p/t2pd_id3.pl %s > %s' % (train_filename, dt_file)
                print cmd
                os.system(cmd)
            
            print 'testing multi-dialect decision tree (%s.%s)...' % (dialect, size)
            cmd = 'perl t2p/t2pd_dt.pl %s %s %s' % (dt_file, test_align_file, dialect.upper())
            print cmd
            os.system(cmd)

            print 'output (%s.%s)...' % (dialect, size)
            lex_file = 'data/lexicons/%s.txt' % dialect
            in_file = 'data/lexicons/dt/%s.in' % dialect
            if not os.path.exists(in_file):
                escape_lexicon(lex_file, in_file, REPLACE_TABLE)
            
            out_file = 'data/lexicons/dt/%s.%s.out' % (dialect, size)
            if not os.path.exists(out_file):
                cmd = 'perl t2p/t2pd_out.pl %s %s %s > %s' % (dt_file, in_file, dialect.upper(), out_file)
                print cmd
                os.system(cmd)

            final_file = 'data/result/%s.%s.txt' % (dialect, size)
            if not os.path.exists(final_file):
                escape_lexicon(out_file, final_file, UNREPLACE_TABLE)
