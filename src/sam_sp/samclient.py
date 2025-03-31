import os
import json
import requests
from miscfuncs import truthy, to_expanded_string
from spexception import (ServiceProviderTemporaryError, ServiceProviderError)
from taskstatus import TaskStatus
from sam_sp.peopledata import PeopleExternalOrg
from sam_sp.samdata import InternalOrg, MnemonicCode
from sam_sp.mnemonic import MnemonicCodeMaker

INTERNAL_ORGS = dict()
MNEMONIC_CODES = dict()
FOS_AOIS = dict
MNEMONIC_CODES_UPDATED = 0
VERIFY_SSL = truthy(os.environ.get("VERIFY_SSL","true"))


class SAMClient(object):

    def __init__(self, url, user, password, tmout_secs, people_client,
                 mnemonic_code_maker):
        if not url.endswith("/"):
            url = url + "/"
        self.url = url

        self.user = user
        self.password = password
        self.session = requests.Session()
        self.session.auth = (user, password)
        self.tmout = int(tmout_secs)
        self.people_client = people_client
        self.mnemonic_code_maker = mnemonic_code_maker

    def _reconnect(self):
        self.session = requests.Session()
        self.session.auth = (self.user, self.password)
        

    def get(self, path):
        url = self._build_full_url(path)
        result = self._try_get(url)

        if result.status_code == 200:
            if result.text is None or result.text == '':
                return None
            return json.loads(result.text)

        self._raise_request_error("GET", url, result)

    def _try_get(self, url):
        global VERIFY_SSL
        try:
            result = self.session.get(url,
                                      verify=VERIFY_SSL,
                                      timeout=self.tmout)
            
        except requests.exceptions.Timeout as te:
            raise ServiceProviderTemporaryError(te)
        except HTTPError as http_err:
            if http_err.response.status_code == 503:
                raise ServiceProviderTemporaryError(http_err)
            else:
                raise http_err
        
        return result

    def put(self, path, data):
        url = self._build_full_url(path)
        result = self._try_put(url, data)

        if result.status_code == 200:
            if result.text is None or result.text == '':
                return None
            return json.loads(result.text)

        self._raise_request_error("PUT", url, result)

    def _try_put(self, url, data):
        global VERIFY_SSL
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        try:
            result = self.session.put(url, data=data, headers=headers,
                                      verify=VERIFY_SSL, timeout=self.tmout)
        except requests.exceptions.Timeout as te:
            raise ServiceProviderTemporaryError(te);
        except HTTPError as http_err:
            if http_err.response.status_code == 503:
                raise ServiceProviderTemporaryError(http_err)
            else:
                raise http_err
        
        return result
        
    def post(self, path, data):
        url = self._build_full_url(path)
        result = self._try_post(url, data)

        if result.status_code == 200:
            if result.text is None or result.text == '':
                return None
            return json.loads(result.text)

        self._raise_request_error("POST", url, result)

    def _try_post(self, url, data):
        global VERIFY_SSL
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        try:
            result = self.session.post(url, data=data, headers=headers,
                                       verify=VERIFY_SSL, timeout=self.tmout)
        except requests.exceptions.Timeout as te:
            raise ServiceProviderTemporaryError(te);

        return result
        
    def _raise_request_error(self, method, url, result):
        if result.status_code == 404:
            # A 404 can occur with any url when SAM is first coming up. If it
            # looks like this is a startup problem, raise a temporary error
            self._check_server_status()
        raise RuntimeError("SAM API returned " + str(result.status_code) + \
                           "\n  method=" + method + " url=" + url +\
                           " result:\n" + to_expanded_string(result.text))

    def _check_server_status(self):
        global VERIFY_SSL
        url = self._build_full_url("status")
        result = None
        try:
            result = self.session.get(url, verify=VERIFY_SSL)
        except requests.exceptions.Timeout as te:
            raise ServiceProviderTemporaryError(te);

        if result.status_code == 404:
            de = RuntimeError("SAM service not (yet) available")
            raise ServiceProviderTemporaryError(de);

        return
    
    def get_internal_org(self, org_id):
        global INTERNAL_ORGS
        # Organizations do not change often and cannot be changed via API
        if not INTERNAL_ORGS:
            self.load_internal_orgs()
        return INTERNAL_ORGS[org_id]

    def get_internal_org_by_acronym(self, acronym):
        """Retrieve internal org by acronym
        """
        global INTERNAL_ORGS
        if not INTERNAL_ORGS:
            self.load_internal_orgs()
        for org in INTERNAL_ORGS.values():
            if org['acronym'] == acronym:
                return org
        return None

    def get_internal_orgs(self):
        global INTERNAL_ORGS
        if not INTERNAL_ORGS:
            self.load_internal_orgs()
        ids = sorted(INTERNAL_ORGS.keys())
        orgs = []
        for org_id in ids:
            org = INTERNAL_ORGS[org_id]
            orgs.append(org)
        return orgs

    def load_internal_orgs(self):
        global INTERNAL_ORGS
        results = self.get("organization")
        allorgs = dict()
        for rec in results:
            internal_org = InternalOrg(rec)
            if not internal_org['active']:
                continue
            idx = int(internal_org['org_id'])
            allorgs[idx] = internal_org
        INTERNAL_ORGS = allorgs

    def get_mnemonic_code_for_org(self, acronym):
        mc, desc, active = self._get_mnemonic_data_for_org(acronym)
        if mc and active:
            return mc
        return None

    def _get_mnemonic_data_for_org(self, acronym):
        organization = self.get_internal_org_by_acronym(acronym)
        desc = organization['name']
        mobj = self._get_mnemonic_code_by_description(desc)
        if mobj:
            code = mobj['code']
            desc = mobj['description']
            active = mobj['active']
        else:
            code = None
            active = False

        return code, desc, active

    def get_mnemonic_code_for_inst(self, org_code):
        mc, desc, active = self._get_mnemonic_data_for_inst(org_code)
        if mc and active:
            return mc
        return None
        
    def _get_mnemonic_data_for_inst(self, org_code):
        institution = self.people_client.get_external_org_by_nsf_code(org_code)
        if not institution:
            raise ServiceProviderError("Institution with nsf code "+org_code+\
                                       " should have been verified" +\
                                       " but people_client could not find it")
        name = institution['name']
        city = institution['city'] if institution['city'] != '' else 'null'
        if city is None or city == '':
            city = 'null'
        desc = name + ', ' + city
        mobj = self._get_mnemonic_code_by_description(desc)

        if mobj is None and city == "null":
            mobj = self._get_mnemonic_code_by_description(name)
        if mobj:
            code = mobj['code']
            desc = mobj['description']
            active = mobj['active']
        else:
            code = None
            active = False

        return code, desc, active

    def _get_mnemonic_code_by_description(self, desc):
        if not MNEMONIC_CODES:
            self.load_mnemonic_codes()
        lcdesc = desc.lower()
        for mc in MNEMONIC_CODES:
            mobj = MNEMONIC_CODES[mc]
            if mobj['description'].lower() == lcdesc:
                return mobj
        return None
    
    def get_mnemonic_codes(self):
        global MNEMONIC_CODES
        if not MNEMONIC_CODES:
            self.load_mnemonic_codes()
        codes = sorted(MNEMONIC_CODES.keys())
        mnemonic_codes = []
        for code in codes:
            mnemonic_code = MNEMONIC_CODES[code]
            mnemonic_codes.append(mnemonic_code)
        return mnemonic_codes

    def build_mnemonic_code_choices(self, site_org, org_code):
        self.load_mnemonic_codes()
        return self._build_mnemonic_code_choices(site_org, org_code)

    def _build_mnemonic_code_choices(self, site_org, org_code):
        maker = self.mnemonic_code_maker

        choices = [["MnemonicCode", "Description", "CodeExists", "Active"]]
        org_choices = []
        inst_choices = []
        
        if site_org:
            mc, desc, active = self._get_mnemonic_data_for_org(site_org)
            if mc:
                org_choices.append([mc, desc, 'True', str(active)])
            if not mc or not active:
                mcs = maker.make_suggestions(MNEMONIC_CODES, site_org)
                mcs.append(maker.make_suggestions(MNEMONIC_CODES, name))
                for mc in mcs:
                    org_choices.append([ mc, desc, 'False', 'False'])
        if org_code:
            mc, desc, active = self._get_mnemonic_data_for_inst(org_code)
            if mc:
                org_choices.append([ mc, desc, 'True', str(active)])
            if not mc or not active:
                mcs = maker.make_suggestions(MNEMONIC_CODES, desc)
                for mc in mcs:
                    org_choices.append([ mc, desc, 'False', 'False' ])

        max_choices = maker.max_suggestions
        choices.extend(self._combine_org_and_inst_choices(org_choices,
                                                          inst_choices,
                                                          max_choices))
        return choices

    def _combine_org_and_inst_choices(self, org_choices, inst_choices, max):
        norg = len(org_choices)
        ninst = len(inst_choices)
        if norg == 0:
            return inst_choices
        elif ninst == 0:
            return org_choices
        choices = []
        if (norg+ninst) <= max:
            choices.extend(org_choices)
            choices.extend(inst_choices)
            return choices
        norg = int((max+1)/2)
        for i in range(0,norg):
            choices.append(org_choices[i])
        for i in range(0,max-norg):
            choices.append(inst_choices[i])
        return choices

    def suggest_mnemonic_codes(self, desc):
        self.load_mnemonic_codes()
        maker = self.mnemonic_code_maker
        return maker.make_suggestions(MNEMONIC_CODES, desc)
        
    def suggest_mnemonic_codes_for_org(self, acronym):
        self.load_mnemonic_codes()
        code = self.get_mnemonic_code_for_org(acronym)
        if code is not None:
            raise RuntimeError("org has mnemonic code: "+str(acronym)+"->"+code)
        maker = self.mnemonic_code_maker
        suggestions = maker.make_suggestions(MNEMONIC_CODES, acronym)
        organization = self.get_internal_org_by_acronym(acronym)
        desc = organization['name']
        suggestions.append(maker.make_suggestions(MNEMONIC_CODES, desc))
        return suggestions

    def suggest_mnemonic_codes_for_inst(self, org_id):
        self.load_mnemonic_codes()
        code = self.get_mnemonic_code_for_inst(org_id)
        if code is not None:
            raise RuntimeError("inst has mnemonic code: "+str(org_id)+"->"+code)
        maker = self.mnemonic_code_maker
        institution = self.get("institution/"+str(org_id))
        name = institution['name']
        city = institution['city'] if institution['city'] != '' else 'null'
        desc = name + ', ' + city
        return maker.make_suggestions(MNEMONIC_CODES, desc)

    def load_mnemonic_codes(self):
        global MNEMONIC_CODES
        results = self.get("mnemoniccode")
        allcodes = dict()
        for rec in results:
            mnemonic_code = MnemonicCode(rec)
            code = mnemonic_code['code']
            allcodes[code] = mnemonic_code
        MNEMONIC_CODES = allcodes

    def _build_full_url(self, path):
        while path.startswith("/"):
            path = path[1:]
        return self.url + path

