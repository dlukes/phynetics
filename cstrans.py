#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Modul pro generování fonetické transkripce na základě "ortografického"
zápisu. Založeno na skriptech init.scp, prepis.scp Nina Peterka
(peterek@ufal.ms.mff.cuni.cz, 11.9.1997).

"""

# TODO:
#
# - map unknown sequences / paralinguistic indicators to silence / laughter /
#   non-verbal sounds (see KALDI Data preparation documentation) models

import re
import sys
import argparse


class Transcription(str):
    """A Czech utterance and its phonetic transcription.

    """

    _trigger_devoicing = "ptťksšcčxxf"
    _devoiced = _trigger_devoicing
    _trigger_voicing = "bdďgzžʒɮhɣ" # ɮ stands for ʒ̆/ʒʒ
    _voiced = _trigger_voicing + "v"
    _devoiced2voiced = str.maketrans(_devoiced, _voiced)
    _voiced2devoiced = str.maketrans(_voiced, _devoiced)

    def __init__(self, ort_string):
        self.ort = ort_string
        self.fon = self._transcribe()
        # print(self.fon)

    def _transcribe(self):
        fon = self.normalize(self.ort)
        fon = self._init_scp(fon)
        fon = self._foreign(fon)
        fon = self._collapse_expand(fon)
        fon = self._ě(fon)
        fon = self._i_í(fon)
        fon = self._voicing_assim(fon)
        fon = self._unify(fon)
        # safer to put _hiatus fairly close to the end of the transcription
        # rules in __init__, so that we don't need to worry about y/ý
        fon = self._hiatus(fon)
        fon = self._heuristic(fon)
        return self._postprocess(fon)

    def normalize(self, string):
        """Normalize orthographic string.

        Remove extraneous whitespace, "tokenize" string (i.e. add whitespace
        between what should be considered as separate tokens), fold case etc.

        """
        string = re.sub(r"(\w)(\W)", r"\1 \2", string.casefold())
        string = re.sub(r"(\W)(\w)", r"\1 \2", string)
        string = re.sub(r"\s+", " ", string)
        return string.strip()

    def _ě(self, string):
        """<ě> induces palatalization.

        """
        string = re.sub(r"([bpfv])ě", r"\1je", string)
        string = re.sub("dě", "ďe", string)
        string = re.sub("tě", "ťe", string)
        string = re.sub("ně", "ňe", string)
        string = re.sub("mě", "mňe", string)
        # replace all remaining <ě> at this point with [je] (as good a guess as
        # any...)
        return re.sub("ě", "je", string)

    def _i_í(self, string):
        """<i> and <í> induce palatalization.

        """
        string = re.sub("di", "ďi", string)
        string = re.sub("ti", "ťi", string)
        string = re.sub("ni", "ňi", string)
        string = re.sub("dí", "ďí", string)
        string = re.sub("tí", "ťí", string)
        return re.sub("ní", "ňí", string)

    def _collapse_expand(self, string):
        """Collapse digraphs and expand graphemes corresponding to multiple phones.

        """
        string = re.sub("x", "ks", string)
        string = re.sub(r"qu?", "kv", string)
        string = re.sub("ch", "x", string)
        string = re.sub("dz", "ʒ", string)
        return re.sub("dž", "ɮ", string) # ɮ stands for ʒ̆

    def _foreign(self, string):
        """Replace or otherwise treat non-Czech graphemes.

        """
        string = re.sub("w", "v", string)
        return string

    def _voicing_assim(self, string):
        """Perform the voicing assimilations.

        Improvement over regex based treatment of voicing assimilations in the
        original script by Nino Peterek, which was sensitive to the ordering of
        the rules. This version performs anticipatory voicing assimilation by
        starting from the back of the string and using the already constructed
        part of the output string as the context for determining voicing.

        """
        result = ""
        # must be done character by character, because the voicing assimilation
        # can propagate from the back.
        for char in reversed(string):
            # first of all, if we're currently at the end of a word, then the
            # default pronunciation is actually unvoiced
            if result and result[0] == " " and char in self._voiced:
                char = char.translate(self._voiced2devoiced)

            if (not result) and char in self._voiced:
                result = char.translate(self._voiced2devoiced)
            elif not result:
                result = char
            elif previous_phone in self._trigger_devoicing and char in self._voiced:
                result = char.translate(self._voiced2devoiced) + result
            elif previous_phone in self._trigger_voicing and char in self._devoiced:
                result = char.translate(self._devoiced2voiced) + result
            else:
                result = char + result

            # set the previous phone (voicing assimilation rules are allowed to
            # skip regular word boundaries, i.e. when words are separated only
            # by a space):
            previous_phone = result[1] if result[0] == " " else result[0]

        return result

    def _unify(self, string):
        """Unify characters which are only orthographic variants of the same
        phone.

        """
        string = re.sub("ů", "ú", string)
        string = re.sub("y", "i", string)
        return re.sub("ý", "í", string)

    def _heuristic(self, string):
        """Make substitutions which are not 100% sure but very probable and in any
        case uncontroversial.

        """
        string = re.sub("nk", "ŋk", string)
        string = re.sub("ng", "ŋg", string)
        string = re.sub("mv", "ɱv", string)
        string = re.sub("mf", "ɱf", string)
        string = re.sub("nť", "ňť", string)
        string = re.sub("nď", "ňď", string)
        string = re.sub("nň", "ň", string)
        string = re.sub("cc", "c", string)
        string = re.sub("dd", "d", string)
        string = re.sub("jj", "j", string)
        string = re.sub("kk", "k", string)
        string = re.sub("ll", "l", string)
        string = re.sub("nn", "n", string)
        string = re.sub("mm", "m", string)
        string = re.sub("ss", "s", string)
        string = re.sub("tt", "t", string)
        string = re.sub("zz", "z", string)
        string = re.sub("čč", "č", string)
        return re.sub("šš", "š", string)

    def _hiatus(self, string):
        """Add [j] in hiatus.

        """
        return re.sub(r"([ií])([aeiouáéíóú])", r"\1j\2", string)

    def _init_scp(self, string):
        """Perform replacements as specified in Nino Peterek's original init.scp
        file.

        These include treating some foreign prefixes which behave specifically,
        some lexical specifities etc. It is not clear whether this list is
        exhaustive (probably not -- it may have been derived from a specific
        set of training data way back when). Some I've deemed useless and
        removed, some I've added in a rather random fashion, some I've slightly
        edited.

        """
        string = re.sub("ccitt", "cécéítété", string)
        string = re.sub("nism", "nyzm", string)
        string = re.sub("nist", "nyst", string)
        string = re.sub("anti", "anty", string)
        string = re.sub("akti", "akty", string)
        string = re.sub("atik", "atyk", string)
        string = re.sub("tick", "tyck", string)
        string = re.sub("kandi", "kandy", string)
        string = re.sub("nie", "nye", string)
        string = re.sub("nii", "nyi", string)
        string = re.sub("arkti", "arkty", string)
        string = re.sub("atrakti", "atrakty", string)
        string = re.sub("audi", "audy", string)
        string = re.sub("automati", "automaty", string)
        string = re.sub("causa", "kauza", string)
        string = re.sub("celsia", "celzia", string)
        string = re.sub("chil", "čil", string)
        string = re.sub("danih", "danyh", string)
        string = re.sub("efektiv", "efektyv", string)
        string = re.sub("finiti", "finyty", string)
        string = re.sub("dealer", "dýler", string)
        string = re.sub("diag", "dyag", string)
        string = re.sub("diet", "dyet", string)
        string = re.sub("dif", "dyf", string)
        string = re.sub("dig", "dyg", string)
        string = re.sub("dikt", "dykt", string)
        string = re.sub("dilet", "dylet", string)
        string = re.sub("dipl", "dypl", string)
        string = re.sub("dirig", "dyryg", string)
        string = re.sub("disk", "dysk", string)
        string = re.sub("display", "dysplej", string)
        string = re.sub("disp", "dysp", string)
        string = re.sub("dist", "dyst", string)
        string = re.sub("divide", "dyvide", string)
        string = re.sub("dukti", "dukty", string)
        string = re.sub("edic", "edyc", string)
        string = re.sub("error", "eror", string)
        string = re.sub(r"\bex([aeiouáéíóúů])", r"egz\1", string)
        string = re.sub("elektroni", "elektrony", string)
        string = re.sub("energetik", "energetyk", string)
        string = re.sub("etik", "etyk", string)
        string = re.sub("femini", "feminy", string)
        string = re.sub("finiš", "finyš", string)
        string = re.sub("monie", "monye", string)
        string = re.sub("geneti", "genety", string)
        string = re.sub("gieni", "gieny", string)
        string = re.sub("imuni", "imuny", string)
        string = re.sub("indiv", "indyv", string)
        string = re.sub("inici", "inyci", string)
        string = re.sub("investi", "investy", string)
        string = re.sub("karati", "karaty", string)
        string = re.sub("kardi", "kardy", string)
        string = re.sub("klaus", "klauz", string)
        string = re.sub("komuni", "komuny", string)
        string = re.sub("kondi", "kondy", string)
        string = re.sub("kredit", "kredyt", string)
        string = re.sub("kriti", "krity", string)
        string = re.sub("komodit", "komodyt", string)
        string = re.sub("konsor", "konzor", string)
        string = re.sub("leasing", "lízing", string)
        string = re.sub("giti", "gity", string)
        string = re.sub("medi", "medy", string)
        string = re.sub("motiv", "motyv", string)
        string = re.sub("manag", "menedž", string)
        string = re.sub("nsti", "nsty", string)
        string = re.sub("temati", "tematy", string)
        string = re.sub("mini", "miny", string)
        string = re.sub("minus", "mínus", string)
        string = re.sub("ing", "yng", string)
        string = re.sub("gativ", "gatyv", string)
        string = re.sub("mati", "maty", string)
        string = re.sub("manip", "manyp", string)
        string = re.sub("moderni", "moderny", string)
        string = re.sub("organi", "organy", string)
        string = re.sub("optim", "optym", string)
        string = re.sub("panick", "panyck", string)
        string = re.sub("pediatr", "pedyatr", string)
        string = re.sub("perviti", "pervity", string)
        string = re.sub("politi", "polity", string)
        string = re.sub("pozit", "pozyt", string)
        string = re.sub("privati", "privaty", string)
        string = re.sub("prostitu", "prostytu", string)
        string = re.sub("radik", "radyk", string)
        string = re.sub(r"\bradio", "radyo", string)
        string = re.sub("relativ", "relatyv", string)
        string = re.sub("restitu", "restytu", string)
        string = re.sub("rock", "rok", string)
        string = re.sub("rutin", "rutyn", string)
        string = re.sub(r"\brádi(\S)", r"rády\1", string)
        string = re.sub("shop", "šop", string)
        string = re.sub(r"\bsho", "scho", string)
        string = re.sub("softwar", "softvér", string)
        string = re.sub("sortim", "sortym", string)
        string = re.sub("spektiv", "spektyv", string)
        string = re.sub("superlativ", "superlatyv", string)
        string = re.sub("nj", "ň", string)
        string = re.sub("statisti", "statysty", string)
        string = re.sub("stik", "styk", string)
        string = re.sub("stimul", "stymul", string)
        string = re.sub("studi", "study", string)
        string = re.sub("techni", "techny", string)
        string = re.sub("telecom", "telekom", string)
        string = re.sub("telefoni", "telefony", string)
        string = re.sub("tetik", "tetyk", string)
        string = re.sub("textil", "textyl", string)
        string = re.sub("tibet", "tybet", string)
        # string = re.sub("tibor", "tybor", string)
        string = re.sub("tirany", "tyrany", string)
        string = re.sub("titul", "tytul", string)
        string = re.sub("tradi", "trady", string)
        string = re.sub("univer", "unyver", string)
        string = re.sub("venti", "venty", string)
        return re.sub("vertik", "vertyk", string)

    def _postprocess(self, string):
        """Make final substitutions to conform to the ORTOFON phonetic
        transcription format.

        """
        string = re.sub("ɮ", "ʒʒ", string)
        return re.sub("x", "ch", string)

# # závěrečný přepis na HTK abecedu -- zatím není jasné, zda bude potřeba
# s/>/rsz /g
# s/EU/eu /g
# s/AU/au /g
# s/OU/ou /g
# s/Á/aa /g
# s/Č/cz /g
# s/Ď/dj /g
# s/É/ee /g
# s/Í/ii /g
# s/Ň/nj /g
# s/Ó/oo /g
# s/Ř/rzs /g
# s/Š/sz /g
# s/Ť/tj /g
# s/Ú/uu /g
# s/Ů/uu /g
# s/Ý/ii /g
# s/Ž/zs /g
# s/Y/i /g
# s/&/dzs /g
# s/@/ts /g
# s/#/ch /g
# s/!//g
# s/\([A-Z]\)/\1 /g
# s/$/ sp/g

def process_command_line(argv):
    """Return settings based on argv.

    `argv` is a list of arguments, or `None` for ``sys.argv[1:]``.

    """
    if argv is None:
        argv = sys.argv[1:]

    # initialize the parser object:
    parser = argparse.ArgumentParser(description="""Transcribe Czech sentence
    phonetically.""")

    # define options here:
    # parser.add_argument("-o", "--output", help="specify file to write output to")
    # parser.add_argument("-m", "--max-tokens-per-seg", type=int, default=25,
    #                     help="""specify maximum allowed number of tokens per
    #                     segment""")
    # parser.add_argument("-f", "--format", help="""specify type of output;
    #                     defaults to eaf""", choices=["eaf", "numbered-log",
    #                                                  "timestamped-log"])
    # parser.add_argument("input_file", nargs="+")
    # parser.add_argument("-q", "--quiet", action="store_true", help="""suppress
    #                     logging messages""")
    parser.add_argument("sentence")

    settings = parser.parse_args(argv)
    # cutoff = args.max_tokens_per_seg
    # input_files = args.input_file

    return settings

def main(argv=None):
    settings = process_command_line(argv)
    trans = Transcription(settings.sentence)
    print(trans.fon)
    return 0

if __name__ == "__main__":
    status = main()
    sys.exit(status)
