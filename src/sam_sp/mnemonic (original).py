import sam_sp.misc

class MnemonicCodeMaker(object):

    def __init__(self, mnemonic_codes_map):
        self.mcmap = mnemonic_codes_map

    def make_suggestions(self, desc, acronym):
        self.min_suggestions = 5
        self.max_suggestions = 10
        self.suggestions = []
        self.unique_suggestions = set()

        if acronym:
            self._check_short_name(acronym.upper())

        desc = misc.RE_PUNCT.sub(' ',desc)

        self._check_short_name(desc)

        descwords = misc.RE_WS.split(desc.upper())
        firstword = descwords[0]
        if len(firstword) <= 5:
            self._check_short_name(firstword)

        acronym = self._make_acronym(descwords)
        self._check_short_name(acronym)

        mainwords = self._drop_trivial_words(descwords)
        acronym = self._make_acronym(mainwords)
        self._check_short_name(acronym)

        firstword = mainwords[0]

        typelesswords = self._drop_type_words(mainwords)
        acronym = self._make_acronym(typelesswords)
        self._check_short_name(acronym)

        type_abbrev = ""
        if self._is_org_type(firstword) and len(mainwords) > 1:
            type_abbrev = firstword[0:1]
            self._check_short_name(type_abbrev+mainwords[1])

        firstword = typelesswords[0]
        if len(firstword) <= 5:
            self._check_short_name(firstword)

        if len(self.unique_suggestions) >= self.min_suggestions:
            return self.suggestions[0:self.max_suggestions]

        allwords = type_abbrev + ''.join(typelesswords)
        allconsonants = self._drop_vowels(allwords)
        self._last_ditch_effort(allconsonants)
        self._last_ditch_effort(allwords)

        return self.suggestions[0:self.max_suggestions]

    def _check_short_name(self, short_name):
        if len(short_name) == 3:
            self._checkmc(short_name)
        elif len(short_name) <= 5:
            self._checkmc(short_name[0:3])
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

    def _last_ditch_effort(self, word):
        n_alts = len(word) - 3
        if n_alts < 1:
            return
        for index in range(n_alts):
            self._checkmc(word[index:index+3])

    def _checkmc(self, suggestion):
        if suggestion in self.unique_suggestions:
            return
        if not suggestion in self.mcmap:
            self.suggestions.append(suggestion)
            self.unique_suggestions.add(suggestion)
