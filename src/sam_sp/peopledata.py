import re, json
from sam_sp.misc import *

PREFERRED_PHONE_TYPES = [
    'Ucar Office',
    'External Office',
    'Cell',
    'Other',
    'Home'
]

RE_ESC_SEQ = re.compile('[\\]U[0-9A-F][0-9A-F][0-9A-F][0-9A-F]')

def make_regex(instr, fuzziness):
    # fuzziness can be 0, 1, or 2
    if instr == '':
        return '[^:]?'
    nchars = len(instr)
    inarr = [ '', '' ]
    outarr = []
    inarr.extend([*instr])
    inarr.extend(['',''])
    for i in range(2,1+nchars):
        lb = i-fuzziness
        la = i+fuzziness+1
        _get_charmatch_regex(inarr, fuzziness, outarr, lb, la)
    outarr.append('(')
    lb = 1+nchars-fuzziness
    la = 1+nchars+fuzziness+1
    _get_charmatch_regex(inarr, fuzziness, outarr, lb, la)
    outarr.append(')?')
    return ''.join(outarr)

def _get_charmatch_regex(inarr, fuzziness, outarr, lookback, lookahead):
    outarr.append('[')
    for i in range(lookback,lookahead):
        ch = inarr[i]
        if ch != '':
            outarr.append(ch)
    outarr.append('][^:]?')
        
def _replace_non_alnum(instr):
    npstr = RE_PUNCT.sub(' ',instr)
    tnpstr = RE_WS.sub(' ',npstr)
    return RE_ESC_SEQ.sub('_',tnpstr)

class Fuzzy(dict):

    def __init__(self, idval, weight, *args) -> dict:
        kval = dict()
        kval['instr'] = ':'.join(args)
        kval['idval'] = int(idval)
        kval['weight'] = int(weight)
        dict.__init__(self, **kval)

    def __str__(self):
        return '%s:%d:%02d' % (self['instr'],self['idval'],self['weight'])
        


class PeopleExternalOrg(dict):

    def __init__(self, kwargs) -> dict:
        kval = dict()
        kval['org_id'] = kwargs.get('org_id',kwargs.get('id',None))
        kval['shortName'] = kwargs['shortName'].strip()
        kval['name'] = kwargs['name'].strip()
        kval['nsfOrgCode'] = kwargs.get('nsfOrgCode',None)
        kval['org_type'] = kwargs.get('type','').strip()
        kval['address'] = kwargs.get('address','').strip()
        kval['city'] = kwargs.get('city','').strip()
        kval['org_zip'] = kwargs.get('zip','').strip()
        kval['state'] = kwargs.get('state','').strip()
        kval['country'] = kwargs.get('country','').strip()
        dict.__init__(self, **kval)

    @staticmethod
    def essential_field_labels():
        return ['external_org_id','Name','City','Address']

    def essential_fields(self):
        return [self['org_id'],self['name'],self['city'],self['address']]

    def make_fuzzies(self):
        C = self.__class__
        fuzzies = []
        # To match against upper case chars. ':' will be a separator, so replace
        name = self['name'].upper().replace(':',' ')
        city = self['city'].upper().replace(':',' ')
        address = self['address'].upper().replace(':',' ')
        fuzzies.extend(self.make_city_address_variants(0,name,city,address))
        nname = _replace_non_alnum(name)
        ncity = _replace_non_alnum(city)
        naddress = _replace_non_alnum(address)
        if nname != name or ncity != city or naddress != address:
            name = nname
            city = ncity
            address = naddress
            fuzzies.extend(self.make_city_address_variants(1,name,city,address))

        name_city = None
        if ncity not in nname:
            name_city = nname + " " + ncity
            city = ncity
            address = naddress
            fuzzies.extend(self.make_city_address_variants(5,name_city,city,
                                                           address))
            
        nname = C.reduce_to_essentials(name)
        ncity = C.reduce_to_essentials(city)
        naddress = C.reduce_to_essentials(address)
        if nname != name or ncity != city or naddress != address:
            name = nname
            city = ncity
            address = naddress
            fuzzies.extend(self.make_city_address_variants(15,name,city,
                                                           address))

        if name_city is not None:
            nname_city = C.reduce_to_essentials(name_city)
            if nname_city != name_city or ncity != city or naddress != address:
                name_city = nname_city
                city = ncity
                address = naddress
                fuzzies.extend(self.make_city_address_variants(20,name_city,
                                                               city,address))
        return fuzzies

    def make_city_address_variants(self, weight, name, city, address):
        fuzzies = []
        fuzzies.append(self.make_fuzzy(weight,name,city,address))
        if city:
            fuzzies.append(self.make_fuzzy(weight+5,name,'',address))
        if address:
            fuzzies.append(self.make_fuzzy(weight+2,name,city,''))
        if city and address:
            fuzzies.append(self.make_fuzzy(weight+7,name,'',''))
        return fuzzies
        
        
    def make_fuzzy(self, weight, name, city, address):
        return Fuzzy(self['org_id'],weight,name,city,address)

    @staticmethod
    def get_normalized_match_param(key, kwargs):
        return _replace_non_alnum(kwargs.get(key,'').upper())


    @staticmethod
    def reduce_to_essentials(instr):
        non_trivial_words = set()
        for word in RE_WS.split(instr):
            if not word in TRIVIAL_WORDS:
                non_trivial_words.add(word)
        non_trivial_sorted_words = sorted(non_trivial_words)
        return ' '.join(non_trivial_sorted_words)

class PeoplePerson(dict):

    def __init__(self, kwargs) -> dict:
        kval = dict()
        kval['upid'] = kwargs['upid']
        kval['uid'] = str(kwargs.get('uid',''))
        kval['type'] = kwargs['type']
        kval['firstName'] = kwargs.get('firstName','').strip()
        kval['lastName'] = kwargs.get('lastName','').strip()
        kval['middleName'] = kwargs.get('middleName','').strip()
        kval['nameSuffix'] = kwargs.get('nameSuffix','').strip()
        kval['preferredName'] = kwargs.get('preferredName','').strip()
        kval['email'] = kwargs.get('email','').strip()
        kval['forwardEmail'] = kwargs.get('forwardEmail','').strip()
        kval['username'] = kwargs.get('username','').strip()
        kval['active'] = kwargs['active']
        kval['title'] = kwargs.get('title','')
        kval['lastChanged'] = int(kwargs['lastChanged'])
        if 'phones' in kwargs:
            phone =  PeoplePerson._get_best_phone(kwargs.get('phones',[]))
        else:
            phone = ""
        kval['phone'] = phone
        if 'externalOrgName' in kwargs:
            kval['org'] = kwargs['externalOrgName']
        if 'positions' in kwargs:
            kval['org'] = \
                PeoplePerson._get_internal_org(kwargs['positions'])
        if 'org' in kwargs:
            kval['org'] = kwargs['org']
        if 'fuzzies' in kwargs:
            kval['fuzzies'] = kwargs['fuzzies']
        dict.__init__(self, **kval)

    @staticmethod
    def _get_best_phone(phones):
        global PREFERRED_PHONE_TYPES
        if not phones:
            return ""
        type2number = dict()
        for phoneDetail in phones:
            pt = phoneDetail['phoneType']
            pn = phoneDetail['phoneNumber']
            type2number[pt] = pn
        for preferred_type in PREFERRED_PHONE_TYPES:
            if preferred_type in type2number:
                return type2number[preferred_type]
        return ""

    def _get_internal_org(positions):
        if not positions:
            return "UCAR/NCAR"
        for position in positions:
            primary = str(position['primary'])
            if primary.lower() == 'true':
                org = position.get('organization','')
                return "UCAR/NCAR:" + org
        return "UCAR/NCAR"

    @staticmethod
    def essential_field_labels():
        return ['upid','LastName','FirstName','PreferredName','MiddleName','Organization','Type','Active','Title/Note']

    def essential_fields(self):
        return [self['upid'],self['lastName'],self['firstName'],self['preferredName'],self['middleName'],self['org'],self['type'],self['active'],self['title']]

    def add_fuzzies(self):
        fuzzies = []
        # To match against upper case chars. ':' will be a separator, so replace
        first = self['firstName'].upper().replace(':',' ')
        last = self['lastName'].upper().replace(':',' ')
        middle = self['middleName'].upper().replace(':',' ')
        preferred = self['preferredName'].upper().replace(':',' ')
        fuzzies.extend(self.make_name_variants(0,first,last,middle,preferred))
        nfirst = _replace_non_alnum(first)
        nlast = _replace_non_alnum(last)
        nmiddle = _replace_non_alnum(middle)
        npreferred = _replace_non_alnum(preferred)
        if nfirst != first or nlast != last or nmiddle != middle or npreferred != preferred:
            first = nfirst
            last = nlast
            middle = nmiddle
            preferred = npreferred
            fuzzies.extend(self.make_name_variants(1,first,last,middle,preferred))
        self['fuzzies'] = fuzzies

    def make_name_variants(self, weight, first, last, middle, preferred):
        fuzzies = []
        fuzzies.append(self.make_fuzzy(weight,first,last,middle,preferred))
        fuzzies.append(self.make_fuzzy(weight+1,preferred,last,middle,first))
        if middle:
            fuzzies.append(self.make_fuzzy(weight+3,first,last,'',preferred))
            fuzzies.append(self.make_fuzzy(weight+3,preferred,last,'',first))
            fuzzies.append(self.make_fuzzy(weight+10,last,first,'',preferred))
            fuzzies.append(self.make_fuzzy(weight+10,last,preferred,'',first))
            fuzzies.append(self.make_fuzzy(weight+15,last,middle,preferred,first))
            fuzzies.append(self.make_fuzzy(weight+15,last,middle,first,preferred))
        if first:
            fuzzies.append(self.make_fuzzy(weight+5,'',last,middle,preferred))
            fuzzies.append(self.make_fuzzy(weight+5,preferred,last,middle,''))
            fuzzies.append(self.make_fuzzy(weight+10,last,first,middle,preferred))
        if preferred:
            fuzzies.append(self.make_fuzzy(weight+5,first,last,middle,''))
            fuzzies.append(self.make_fuzzy(weight+5,'',last,middle,first))
            fuzzies.append(self.make_fuzzy(weight+10,last,preferred,middle,first))
        fuzzies.append(self.make_fuzzy(weight+10,'',last,'',''))

        return fuzzies
        
        
    def make_fuzzy(self, weight, first, last, middle, preferred):
        return Fuzzy(self['upid'], weight, first, last, middle, preferred)

    @staticmethod
    def get_normalized_match_param(key, kwargs):
        return _replace_non_alnum(kwargs.get(key,'').upper())

class PeopleInternalOrg(dict):

    def __init__(self, kwargs) -> dict:

        kval = dict()
        kval['orgId'] = kwargs['orgId']
        kval['acronym'] = kwargs['acronym']
        kval['name'] = kwargs['name']
        kval['active'] = kwargs['name']
        kval['parentOrgAcronym'] = kwargs.get('parentOrgAcronym',None)
        dict.__init__(self, **kval)
