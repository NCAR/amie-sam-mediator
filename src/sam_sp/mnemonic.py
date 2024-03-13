import sam_sp.misc as misc

class Context(object):
    def __init__(self, mnemonic_codes_map):
        self.mcmap = mnemonic_codes_map;
        self.suggestions = []
        self.unique_suggestions = set()

class MnemonicCodeMaker(object):

            
    def __init__(self, min_suggestions, max_suggestions):
        self.min_suggestions = min_suggestions
        self.max_suggestions = max_suggestions

    def make_suggestions(self, mnemonic_codes_map, desc):
        ctxt = Context(mnemonic_codes_map)

        desc = misc.RE_PUNCT.sub(' ',desc)

        self._check_short_name(ctxt, desc)

        descwords = misc.RE_WS.split(desc.upper())
        firstword = descwords[0]
        if len(firstword) <= 5:
            self._check_short_name(ctxt, firstword)

        if len(descwords) > 2:
            acronym = self._make_acronym(descwords)
            self._check_short_name(ctxt, acronym)

        mainwords = self._drop_trivial_words(descwords)
        if len(mainwords) > 2:
            acronym = self._make_acronym(mainwords)
            self._check_short_name(ctxt, acronym)

        firstword = mainwords[0]

        typelesswords = self._drop_type_words(mainwords)
        if len(typelesswords) > 2:
            acronym = self._make_acronym(typelesswords)
            self._check_short_name(ctxt, acronym)

        type_abbrev = ""
        if self._is_org_type(firstword) and len(mainwords) > 1:
            type_abbrev = firstword[0:1]
            self._check_short_name(ctxt, type_abbrev+mainwords[1])

        firstword = typelesswords[0]
        if len(firstword) <= 5:
            self._check_short_name(ctxt, firstword)

        if len(ctxt.unique_suggestions) >= self.min_suggestions:
            return ctxt.suggestions[0:self.max_suggestions]

        allwords = type_abbrev + ''.join(typelesswords)
        allconsonants = self._drop_vowels(allwords)
        self._last_ditch_effort(ctxt, allconsonants)
        self._last_ditch_effort(ctxt, allwords)

        return ctxt.suggestions[0:self.max_suggestions]

    def _check_short_name(self, ctxt, short_name):
        if len(short_name) == 3:
            self._checkmc(ctxt, short_name)
        elif len(short_name) <= 5:
            self._checkmc(ctxt, short_name[0:3])
        consonants = self._drop_vowels(short_name)
        if len(consonants) <= 4:
            return consonants[0:3]

    def _drop_vowels(self, name):
        return misc.RE_VOWELS.sub('',name)
            
    def _make_acronym(self, words):
        ac = []
        for word in words:
            c = word[0:1]
            if misc.RE_ALPHA.match(c):
                ac.append(c)
        return ''.join(ac)

    def _drop_trivial_words(self, words):
        nontrivial = []
        for word in words:
            if not word in misc.TRIVIAL_WORDS:
                nontrivial.append(word)
        return nontrivial

    def _is_org_type(self, word):
        for pattern in misc.ORG_TYPE_PATTERNS:
            if pattern.match(word):
                return True
        return False

    def _drop_type_words(self, words):
        nontype = []
        for word in words:
            if not self._is_org_type(word):
                nontype.append(word)
        return nontype

    def _last_ditch_effort(self, ctxt, word):
        n_alts = len(word) - 3
        if n_alts < 1:
            return
        for index in range(n_alts):
            self._checkmc(ctxt, word[index:index+3])

    def _checkmc(self, ctxt, suggestion):
        if suggestion in ctxt.unique_suggestions:
            return
        if not suggestion in ctxt.mcmap:
            ctxt.suggestions.append(suggestion)
            ctxt.unique_suggestions.add(suggestion)
