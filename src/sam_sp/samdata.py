import re, json

class InternalOrg(dict):

    def __init__(self, kwargs) -> dict:
        kval = dict()
        kval['org_id'] = kwargs['id']
        kval['name'] = kwargs['name']
        kval['acronym'] = kwargs['acronym']
        kval['active'] = kwargs['active']
        kval['parent_org_id'] = kwargs.get('parentOrgId',None)
        dict.__init__(self, **kval)

class AMIEPerson(dict):

    def __init__(self, kwargs) -> dict:
        kval = dict()
        kval['username'] = kwargs['username']
        kval['accessPersonID'] = kwargs['accessPersonID']
        kval['accessGlobalID'] = kwargs['accessGlobalID']
        kval['firstName'] = kwargs['firstName']
        kval['middleName'] = kwargs['middleName']
        kval['lastName'] = kwargs['lastName']
        kval['email'] = kwargs['email']
        kval['phone'] = kwargs['phone']
        kval['organization'] = kwargs['organization']
        kval['academicStatus'] = kwargs['academicStatus']
        dict.__init__(self, **kval)
    
class MnemonicCode(dict):

    def __init__(self, kwargs) -> dict:
        kval = dict()
        kval['code'] = kwargs['code']
        kval['description'] = kwargs['description']
        kval['active'] = kwargs['active']
        dict.__init__(self, **kval)
    

