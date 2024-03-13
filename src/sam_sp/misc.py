import re

RE_WS = re.compile('\s\s*')
RE_ALPHA = re.compile('[A-Z]')
RE_PUNCT = re.compile('[^\w\s]')
RE_VOWELS = re.compile('[AEIOU]')
TRIVIAL_WORDS = { \
                  "THE","EL","LA","LE","DIE","DAS","DER","DET","L", \
                  "AT","A","AU", \
                  "OF","DE","DES","DI","DEGLI","DEL","D", \
                  "IN","ON", \
                  "AND","ET","E", \
                 }
ORG_TYPE_PATTERNS = {
    re.compile(".*UNIVERSI.*"),
    re.compile(".*INSTITU.*"),
    re.compile(".*COLLEGE.*"),
    }
