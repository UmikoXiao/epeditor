import db_eplusout_reader.constants
from db_eplusout_reader.sql_reader import get_ids_dict,to_sql_frequency
from db_eplusout_reader import Variable
import sqlite3
import string
import random
import sys
import os
import re
from .epluspath import idd_files

cPath = os.listdir(r'C:\\')
epPath = os.path.realpath(os.path.join(os.path.dirname(__file__), r'../'))
TimeStep = db_eplusout_reader.constants.TS
Hourly = db_eplusout_reader.constants.H
Daily = db_eplusout_reader.constants.D
Monthly = db_eplusout_reader.constants.M
Annually = db_eplusout_reader.constants.A
RunPeriod = db_eplusout_reader.constants.RP

ANYTHING = 0
CLASS = 1
OBJECT = 2
FIELD = 3


def remove_chinese_characters(input_file, output_file=None):
    """
    Remove all Chinese characters from a file and save with UTF-8 encoding.
    Tries multiple encodings for better compatibility with different file formats.

    Parameters:
        input_file (str): Path to the input file
        output_file (str, optional): Path to save the processed file.
                                   Overwrites input file if not specified.
    """
    # Set output file to input file if not specified
    output_file = output_file or input_file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            pass
    except UnicodeDecodeError:
        # Common encodings to try (in priority order)
        encodings_to_try = ['gbk', 'gb2312', 'big5', 'utf-16', 'latin-1']
        content = None

        # Attempt to read file with different encodings
        for encoding in encodings_to_try:
            try:
                with open(input_file, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Successfully read file with encoding: {encoding}")
                break  # Exit loop if read successfully
            except UnicodeDecodeError:
                continue  # Try next encoding if decoding fails
            except Exception as e:
                print(f"Error reading with {encoding}: {str(e)}")
                continue

        # Fallback: read in binary mode if all encodings fail
        if content is None:
            print("All encoding attempts failed. Using binary mode with error replacement.")
            with open(input_file, 'rb') as f:
                raw_bytes = f.read()
            # Decode with replacement for unrecognizable bytes
            content = raw_bytes.decode('utf-8', errors='replace')

        # Regular expression pattern to match Chinese characters
        # Covers: Basic Chinese characters, punctuation, and full-width characters
        chinese_pattern = re.compile(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]')
        cleaned_content = chinese_pattern.sub('', content)

        # Save cleaned content with UTF-8 encoding
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        print(f"File saved to: {output_file} with utf-8 encoding")

def get_variables(sql_file)->dict:
    sql_variables={}
    conn = sqlite3.connect(sql_file)
    frequency = [to_sql_frequency(freq) for freq in [TimeStep,Hourly,Daily,Monthly,Annually,RunPeriod]]
    for freq in frequency:
        idsDict = get_ids_dict(conn,[Variable(None,None,None)], freq, True)
        sql_variables[freq]=[variable for id_,variable in idsDict.items()]
    conn.close()
    return sql_variables
def generate_code(bit_num):
    all_str = string.digits + string.ascii_lowercase[0:6]
    code = ''.join([random.choice(all_str) for i in range(bit_num)])
    return '0x' + code

def bar(process, total, dig=0,msg="Processing"):
    q = round(process / total * 100, dig)
    print(f'\r[{msg}:', "*" * round(q / 2), '_' * (50 - round(q / 2)), q, '%]', end="")

def get_version(idf_path):
    with open(idf_path, 'r',encoding='utf-8') as f:
        line = f.readline().strip('\n')
        while re.search('Version,', line, re.IGNORECASE) is None:
            line = f.readline().strip('\n')
        head = line
        while not line == '':
            line = f.readline().strip('\n')
            head += line
        version = re.sub(' +', '', head).split(';')[0].split(',')[1]
        version = '-'.join(version.split('.')[:2] + ['0'])
        return version

def check_installation(idf_path):
    version = get_version(idf_path)
    for pth in cPath:
        if re.search(version, pth) is not None:
            return True
    return False

def innitilize_stdout(stdout):
    sys.stdout = stdout

def get_idd(idf_path):
    version = get_version(idf_path)
    if version not in idd_files.keys():
        raise VersionError('Energy+ idd file not found, version unsupported. Required version: ' + version)

    return idd_files[version]

def normal_pattern(pattern:str):
    pattern=list(pattern)
    strange_pattern = list(r'$()*+.[]?\^{}|')
    for i in range(len(pattern)):
        if pattern[i] in strange_pattern:
            pattern[i] = '\\'+ pattern[i]
    return ''.join(pattern)

class redirect:
    content=''
    def write(self,str):
        self.content += str
    def flush(self):
        self.content = ''
    def dump(self,path):
        with open(path,'w+') as f:
            f.write(self.content)
            self.flush()

class hiddenPrint:
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    def __enter__(self):
        r=redirect()
        sys.stdout = r
        sys.stderr = r
        return r

    def __exit__(self, exc_type, exc_val, exc_tb):
        print(f'Finish. Error: {exc_type} {exc_val} in {exc_tb}')
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

class NotFoundError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

class VersionError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg



if __name__=='__main__':
    print('hello1')
    with hiddenPrint() as r:
        print('hello')
        print('hello')
        print('hello')
        print('hello')
        #raise RuntimeError('error')

    print('hello2')