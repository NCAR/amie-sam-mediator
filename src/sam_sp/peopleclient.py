import sys, os, json, time, re
from pathlib import Path
import requests
from miscfuncs import truthy
import tempfile
from miscfuncs import to_expanded_string
from spexception import ServiceProviderTemporaryError
from sam_sp.peopledata import (Fuzzy, PeopleInternalOrg,
                               PeopleExternalOrg, PeoplePerson, make_regex)

INTERNAL_ORGS = dict()
EXTERNAL_ORGS = dict()
EXTERNAL_ORG_FUZZIES = []
RE_FUZZY_SPLIT = re.compile('^(.*):([0-9][0-9]*):([0-9][0-9]*)\s$')
PERSONS = dict()
VERIFY_SSL = truthy(os.environ.get("VERIFY_SSL","true"))

class PeopleCache(object):
    def __init__(self):
        TEMPDIR = os.environ.get('PEOPLECLIENT_TEMPDIR',None)
        self.tempdir = TEMPDIR if TEMPDIR else '/tmp/peopleclient'
        if not Path(self.tempdir).is_dir():
            os.makedirs(self.tempdir)
        self.eorgmatchfile = self.tempdir + "/match-external-org"
        self.eorgfile = self.tempdir + "/external-org"
        self.iorgfile = self.tempdir + "/internal-org"
        self.personfile = self.tempdir + "/person"

        # person-updated contains three lines: the first line is the unix time
        # just before peopledb is queried, the second line is the number
        # of bytes in the personfile, and the third line is the modification
        # time of the personfile. The first time is used the next time peopledb
        # is queried to get just the updates, and the size and second time
        # are used to validate the person-updated file.
        self.personupdated = self.tempdir + "/person-updated"

    def have_ext_org_matchfile(self):
        return self._have_file(self.eorgmatchfile)

    def have_ext_org_file(self):
        return self._have_file(self.eorgfile)

    def have_int_org_file(self):
        return self._have_file(self.iorgfile)

    def have_person_file(self):
        return self._have_file(self.personfile)

    def person_file_metadata(self):
        if self._have_file(self.personfile):
            size = os.stat(self.personfile).st_size
            mtime = os.stat(self.personfile).st_mtime
            return (size, mtime)
        return (None, None)

    def person_file_updated(self):
        if self._have_file(self.personfile) and \
           self._have_file(self.personupdated):
            personfile_size = os.stat(self.personfile).st_size
            personfile_mtime = os.stat(self.personfile).st_mtime
            (recorded_qtime, recorded_size, recorded_mtime) = \
                self._get_recorded_person_metadata()
            if recorded_qtime and recorded_size and recorded_mtime and \
               recorded_size == personfile_size and \
               recorded_mtime == personfile_mtime:
                    return recorded_qtime
        return 0
    
    def _get_recorded_person_metadata(self):
        qtime = None
        size = None
        mtime = None
        with open(self.personupdated, "r") as file:
            if (line := file.readline()):
                qtime = int(float(line))
            if (line := file.readline()):
                size = int(float(line))
            if (line := file.readline()):
                mtime = int(float(line))
        return (qtime, size, mtime)
        
                        
    def _have_file(self,filename):
        return (Path(filename).is_file() and os.stat(filename).st_size > 0)

class PeopleClient(object):

    def __init__(self, url=None, user=None, password=None, logger=None):
        self.cache = PeopleCache()
        if not url:
            return
        if not url.endswith("/"):
            url = url + "/"
        self.url = url
        self.user = user
        self.password = password
        self.session = requests.Session()
        self.session.auth = (user, password)
        self.logger = logger

    def _reconnect(self):
        if self.logger is not None:
            self.logger.debug("Re-establishing session")
        self.session = requests.Session()
        self.session.auth = (self.user, self.password)

    def get_internal_orgs(self):
        global INTERNAL_ORGS
        if not INTERNAL_ORGS:
            self.load_internal_orgs()
        acronyms = sorted(INTERNAL_ORGS.keys())
        orgs = []
        for acronym in acronyms:
            org = INTERNAL_ORGS[acronym]
            orgs.append(org)
        return orgs

    def get_internal_org(self, id_or_acronym):
        url = "orgs/"+str(id_or_acronym)
        iorg = self._get(url)
        if iorg is None:
            return None
        org = PeopleInternalOrg(iorg)
        self._update_cached_internal_org(org)
        return org

    def get_cached_internal_org(self, acronym):
        global INTERNAL_ORGS
        if not INTERNAL_ORGS:
            self.load_internal_orgs()
        return INTERNAL_ORGS[acronym]
        
    def get_external_org_by_nsf_code(self, nsf_org_code):
        url = "protected/admin/externalOrgs?nsfOrgCode="+str(nsf_org_code)
        ol = self._get(url)
        if ol is None or len(ol) == 0:
            return None
        org = PeopleExternalOrg(ol[0])
        self._update_cached_external_org(org)
        return org
        
        
    def set_nsf_code_for_external_org(self, org_id, nsf_org_code):
        url = "protected/admin/externalOrgs/"+str(org_id)
        response = self._get(url)
        if 'nsfOrgCode' in response:
            current_nsf_org_code = response['nsfOrgCode']
            if current_nsf_org_code == nsf_org_code:
                return response
        response['nsfOrgCode'] = nsf_org_code
        request_data = json.dumps(response)
        self._put(url,request_data)
        org = self._get(url)
        self._update_cached_external_org(org)
        return org

    def get_external_org_by_id(self, org_id):
        org = self._get("protected/admin/externalOrgs/"+str(org_id))
        if org is None:
            return None
        self._update_cached_external_org(org)
        return org

    def get_cached_org_by_nsf_code(self, nsf_org_code):
        global EXTERNAL_ORGS
        if not EXTERNAL_ORGS:
            self.load_external_orgs()
        for org in EXTERNAL_ORGS.values():
            if EXTERNAL_ORGS.get('nsfOrgCode',None) == nsf_org_code:
                return org
        return None

    def get_external_orgs(self):
        global EXTERNAL_ORGS
        if not EXTERNAL_ORGS:
            self.load_external_orgs()
        ids = sorted(EXTERNAL_ORGS.keys())
        orgs = []
        for org_id in ids:
            org = EXTERNAL_ORGS[org_id]
            orgs.append(org)
        return orgs

    def fuzzymatch_org(self, **kwargs):
        global EXTERNAL_ORG_FUZZIES
        if not EXTERNAL_ORG_FUZZIES:
            self._load_org_matchfile()
        
        name = PeopleExternalOrg.get_normalized_match_param('name',kwargs)
        city = PeopleExternalOrg.get_normalized_match_param('city',kwargs)
        name_city = name + " " + city
        address = PeopleExternalOrg.get_normalized_match_param('address',kwargs)
        matches = []
        matches.extend(self._fuzzyfind_org(name,city,address))
        matches.extend(self._fuzzyfind_org(name_city,city,address))

        name = PeopleExternalOrg.reduce_to_essentials(name)
        city = PeopleExternalOrg.reduce_to_essentials(city)
        name_city = PeopleExternalOrg.reduce_to_essentials(name_city)
        address = PeopleExternalOrg.reduce_to_essentials(address)
        matches.extend(self._fuzzyfind_org(name,city,address))
        matches.extend(self._fuzzyfind_org(name_city,city,address))

        weighted_unique_ids = self._sort_unique_weighted(matches)
        matched_orgs = []
        for org_id in weighted_unique_ids:
            org_dict = self.get_external_org_by_id(org_id)
            
            if org_dict is not None:
                org = PeopleExternalOrg(org_dict)
                matched_orgs.append(org.essential_fields())

        if matched_orgs:
            labeled_list = [PeopleExternalOrg.essential_field_labels()]
            labeled_list.extend(matched_orgs)
            return labeled_list
        return []
    
    def load_internal_orgs(self):
        global INTERNAL_ORGS
        filename = self.cache.iorgfile
        if not self.cache.have_int_org_file():
            results = self._get("orgs")
            allorgs = dict()
            for rec in results:
                internal_org = PeopleInternalOrg(rec)
                acronym = internal_org['acronym']
                allorgs[acronym] = internal_org
            INTERNAL_ORGS = allorgs
            tmpname = filename + ".t"
            with open(tmpname, "w") as file:
                json.dump(INTERNAL_ORGS, file, indent=4)
            os.rename(tmpname,filename)
        else:
            with open(filename, "r") as file:
                orgdata = json.load(file)
            orgs = dict()
            for acronym in orgdata.keys():
                org = PeopleInternalOrg(orgdata[acronym])
                orgs[acronym] = org
            INTERNAL_ORGS = orgs

    def _get(self, path):
        url = self._build_full_url(path)
        result = self._try_get(url)
        
        if result.status_code == 200:
            return json.loads(result.text)
        elif result.status_code == 404:
            return None
        elif result.status_code == 500 and "Object not found" in response.text:
            return None

        self._raise_request_error('GET',url,result)
                         
    def _try_get(self, url):
        global VERIFY_SSL
        result = None
        try:
            result = self.session.get(url, verify=VERIFY_SSL)
            
        except requests.exceptions.Timeout as te:
            raise ServiceProviderTemporaryError(te);

        return result

    def _put(self, path, data):
        url = self._build_full_url(path)
        result = self._try_put(url, data)
                         
        if result.status_code == 200:
            return json.loads(result.text)

        self._raise_request_error('PUT',url,result)

    def _try_put(self, url, data):
        global VERIFY_SSL
        try:
            result = self.session.put(url, data=data, verify=VERIFY_SSL)
        except requests.exceptions.Timeout as te:
            raise ServiceProviderTemporaryError(te);

        return result

    def _raise_request_error(self, method, url, result):
        raise RuntimeError("People API returned " + str(result.status_code) + \
                           "\n  method=" + method + " url=" + url +\
                           " result:\n" + to_expanded_string(result.text))

    def _update_cached_internal_org(self, org):
        global INTERNAL_ORGS
        if not INTERNAL_ORGS:
            return
        INTERNAL_ORGS[org['acronym']] = org
    
    def load_external_orgs(self):
        global EXTERNAL_ORGS
        filename = self.cache.eorgfile
        if not self.cache.have_ext_org_file():
            results = self._get("protected/admin/externalOrgs?name=%%")
            allorgs = dict()
            for rec in results:
                external_org = PeopleExternalOrg(rec)
                idx = self._get_org_id(external_org)
                allorgs[idx] = external_org
            EXTERNAL_ORGS = allorgs
            tmpname = filename + ".t"
            with open(tmpname, "w") as file:
                json.dump(EXTERNAL_ORGS, file, indent=4)
            os.rename(tmpname,filename)
        else:
            with open(filename, "r") as file:
                orgdata = json.load(file)
            orgs = dict()
            for org_id in orgdata.keys():
                org = PeopleExternalOrg(orgdata[org_id])
                orgs[int(org_id)] = org
            EXTERNAL_ORGS = orgs

    def _get_org_id(self, org):
        org_id = org.get('id',None)
        if not org_id:
            org_id = org.get('org_id',None)
        return int(org_id)
        
    def _update_cached_external_org(self, org):
        global EXTERNAL_ORGS
        if not EXTERNAL_ORGS:
            return
        org_id = self._get_org_id(org)
        EXTERNAL_ORGS[org_id] = org
        
    def _load_org_matchfile(self):
        global EXTERNAL_ORG_FUZZIES, RE_FUZZY_SPLIT
        if not self.cache.have_ext_org_matchfile():
            self._build_org_matchfile()
        fuzzies = []
        filename = self.cache.eorgmatchfile
        with open(filename, "r") as file:
            while line := file.readline():
                m = RE_FUZZY_SPLIT.match(line)
                data = m.group(1)
                idval = m.group(2)
                weight = m.group(3)
                fuzzy = Fuzzy(idval,weight,data)
                fuzzies.append(fuzzy)
        EXTERNAL_ORG_FUZZIES = fuzzies

    def _build_org_matchfile(self):
        global EXTERNAL_ORG_FUZZIES
        if len(EXTERNAL_ORG_FUZZIES) == 0:
            self._build_org_fuzzy_data()

        filename = self.cache.eorgmatchfile
        tmpname = filename + ".t"
        with open(tmpname, "w") as file:
            for fuzzy in EXTERNAL_ORG_FUZZIES:
                file.write(str(fuzzy)+"\n")
        os.rename(tmpname,filename)

    def _build_org_fuzzy_data(self):
        global EXTERNAL_ORG_FUZZIES
        fuzzies = []
        for org in self.get_external_orgs():
            org_fuzzies = org.make_fuzzies()
            fuzzies.extend(org_fuzzies)
        EXTERNAL_ORG_FUZZIES = fuzzies

    def _fuzzyfind_org(self,name,city,address):
        matches = []
        for fuzziness in range(0,3):
            matched_fuzzies = self._find_org(fuzziness,name,city,address)
            for matched_fuzzy in matched_fuzzies:
                org_id = matched_fuzzy['idval']
                weight = str(fuzziness) + str(matched_fuzzy['weight'])
                matches.append(weight+":"+str(org_id))
        return matches

    def _find_org(self,fuzziness,name,city,address):
        global EXTERNAL_ORG_FUZZIES
        fuzzies = EXTERNAL_ORG_FUZZIES
        name_pat = make_regex(name,fuzziness) + '[^:]*'
        city_pat = make_regex(city,fuzziness) + '[^:]*'
        address_pat = make_regex(address,fuzziness) + '[^:]*'
        #        rawpat = '^' + name_pat + ':' + city_pat + ':' + address_pat + '$'
        rawpat = '^' + name_pat + ':' + city_pat + '.*:?$'
        pattern = re.compile(rawpat)
        matched_fuzzies = []
        for fuzzy in fuzzies:
            data = fuzzy['instr']
            if pattern.match(data):
                matched_fuzzies.append(fuzzy)
        return matched_fuzzies

    def _sort_unique_weighted(self, in_wo):
        sorted_objs = self._get_sorted_reasonably_weighted_matches(in_wo)
        unique = set()
        sorted_unique = []
        for o in sorted_objs:
            if o not in unique:
                sorted_unique.append(o)
                unique.add(o)
        return sorted_unique

    def _get_sorted_reasonably_weighted_matches(self, in_wo):
        min_weight = 0
        sorted_wo = sorted(in_wo)
        if len(sorted_wo) > 0:
            best_wo = sorted_wo[0]
            min_weight,o = best_wo.split(':')
        max_weight = min_weight * 5
        sorted_rwo = []
        for wo in sorted_wo:
            w,o = wo.split(':')
            if w >= max_weight:
                continue
            sorted_rwo.append(o)
        return sorted_rwo


    def get_person_by_upid(self, upid):
        global PERSONS
        if not PERSONS:
            self._load_persons()
        return PERSONS[int(upid)]
        
    def get_persons(self):
        global PERSONS
        if not PERSONS:
            self._load_persons()
        upids = sorted(PERSONS.keys())
        persons = []
        for upid in upids:
            person = PERSONS[upid]
            persons.append(person)
        return persons

    def fuzzymatch_person(self, **kwargs):
        global PERSONS
        if not PERSONS:
            self._load_persons()
        
        first = PeoplePerson.get_normalized_match_param('firstName',kwargs)
        last = PeoplePerson.get_normalized_match_param('lastName',kwargs)
        middle = PeoplePerson.get_normalized_match_param('middleName',kwargs)
        preferred = PeoplePerson.get_normalized_match_param('preferredName',kwargs)
        matches = []
        matches.extend(self._fuzzyfind_person(first,last,middle,preferred,1))
        if middle:
            matches.extend(self._fuzzyfind_person(first,last,'',preferred,2))
        if first:
            matches.extend(self._fuzzyfind_person('',last,'',preferred,4))

        weighted_unique_ids = self._sort_unique_weighted(matches)
        matched_persons = []
        for upid in weighted_unique_ids:
            person = self.get_person_by_upid(upid)
            if person is not None:
                matched_persons.append(person.essential_fields())

        if matched_persons:
            labeled_list = [PeoplePerson.essential_field_labels()]
            labeled_list.extend(matched_persons)
            return labeled_list
        return []

    def _load_persons(self):
        global PERSONS
        if not PERSONS:
            self._load_cached_persons()
            
        persons = []
        qtime = int(time.time())
        last_run = str(int(self.cache.person_file_updated()))
        persons.extend(self._load_typed_persons("internal",last_run))
        persons.extend(self._load_typed_persons("external",last_run))
        
        if len(persons) == 0:
            return
        
        updatefile = self.cache.personupdated
        tmpupdatename = updatefile + ".t"
        filename = self.cache.personfile
        tmpname = filename + ".t"
        mode = "w" if last_run == "0" else "a"
        with open(tmpname,mode) as file:
            for person in persons:
                file.write(json.dumps(person)+"\n")
        size = os.stat(tmpname).st_size
        mtime = os.stat(tmpname).st_mtime
        with open(tmpupdatename,"w") as file:
            file.write(str(qtime)+"\n"+str(size)+"\n"+str(mtime)+"\n")
            
        os.rename(tmpname,filename)
        os.rename(tmpupdatename,updatefile)
        for person in persons:
            upid = int(person['upid'])
            PERSONS[upid] = person

    def _load_cached_persons(self):
        if not self.cache.have_person_file():
            return
        filename = self.cache.personfile
        with open(filename,"r") as file:
            for rec in file:
                if not rec:
                    break
                rdict = json.loads(rec)
                person = PeoplePerson(rdict)
                upid = int(person['upid'])
                PERSONS[upid] = person
        
    def _load_typed_persons(self, ptype, lastRun):
        global PERSONS
        start_idx = 0
        count = 5000
        results = []
        while True:
            partial_results = \
                self._get_person_records(ptype, start_idx, count, lastRun)
            if not partial_results:
                break
            results.extend(partial_results)
            nrec = len(partial_results)
            start_idx = start_idx + nrec

        persons = []
        for rec in results:
            rec['type'] = ptype
            person = PeoplePerson(rec)
            upid = int(person['upid'])
            existing_person = PERSONS.get(upid,None)
            if existing_person and \
               existing_person['lastChanged'] >= person['lastChanged']:
                continue
            if not 'org' in person:
                org = '(unknown)' if ptype == 'external' else "UCAR/NCAR"
                person['org'] = org
            person.add_fuzzies()
            persons.append(person)
        return persons

    def _get_person_records(self, type, start, count, lastRun):
        return self._get(type+"Persons?name=%&includeInactive=true&size="+str(count)+"&start="+str(start)+"&lastRun="+lastRun)

    def _fuzzyfind_person(self,first,last,middle,preferred,factor):
        matches = []
        for fuzziness in range(0,3):
            matched_fuzzies = self._find_person(fuzziness,first,last,middle,preferred)
            for matched_fuzzy in matched_fuzzies:
                upid = matched_fuzzy['idval']
                weight = (str(fuzziness) + str(factor*matched_fuzzy['weight']))
                matches.append(weight+":"+str(upid))
        return matches

    def _find_person(self,fuzziness,first,last,middle,preferred):
        global PERSONS
        first_pat = make_regex(first,fuzziness) + '[^:]*'
        last_pat = make_regex(last,fuzziness) + '[^:]*'
        middle_pat = make_regex(middle,fuzziness) + '[^:]*'
        preferred_pat = make_regex(preferred,fuzziness) + '[^:]*'
        rawpat = '^' + first_pat + ':' + last_pat + ':' + middle_pat + \
            ':' + preferred_pat + '$'
        pattern = re.compile(rawpat)
        matched_fuzzies = []
        for upid in PERSONS.keys():
            person = PERSONS[upid]
            for fuzzy in person['fuzzies']:
                data = fuzzy['instr']
                if pattern.match(data) is not None:
                    matched_fuzzies.append(fuzzy)
        return matched_fuzzies

    def _build_full_url(self, path):
        while path.startswith("/"):
            path = path[1:]
        return self.url + path
