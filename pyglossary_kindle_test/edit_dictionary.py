import collections
import unicodedata
from pyglossary import Glossary


# This should remove accents from the words exactly like the kindle fuzzy algorithm, which we don't know
def strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn"
    )


def load_tabfile(filename) -> list[tuple[list[str], str]]:

    entries: list[tuple[list[str], str]] = []
    # Load the file
    with open(filename, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
        for line in lines:
            # Load two TSV columns: lemma and definition
            line = line.strip()
            if line == "":
                continue
            line_split = line.split("\t")
            if len(line_split) != 2:
                print("Error: line has wrong number of columns: " + line)
                continue
            # The first row is the word and its inflections, all separated by |
            word_and_inflections = line_split[0].split("|")
            # The second row is the definition
            definition = line_split[1]
            # Add the entry to the list
            entries.append((word_and_inflections, definition))
    return entries


def fix_entry_list(entries: list[tuple[list[str], str]]) -> Glossary:

    Glossary.init()
    glos = Glossary()

    defiFormat = "h"

    # Create a list of all lemmas without diacritics (and lowercase)
    lemmas_lower_without_diacritics: set[str] = set()
    for entry in entries:
        lemmas_lower_without_diacritics.add(strip_accents(entry[0][0]).lower())
    
    # Create a list of all inflections without diacritics (and lowercase)
    inflections_lower_without_diacritics: set[str] = set()
    for entry in entries:
        for inflection in entry[0][1:]:
            inflections_lower_without_diacritics.add(strip_accents(inflection).lower())

    nodiacritic_inflection_counts = collections.Counter(inflections_lower_without_diacritics)

    for entry in entries:
        lemma = entry[0][0]
        inflections = entry[0][1:]
        definition = entry[1]

        # If definition is empty, skip it
        if definition == "" or definition == None:
            print("Empty definition: " + lemma)
            continue
        
        fixed_inflections: list[str] = []
        for inflection in inflections:
            # This seeks to avoid double entries like aquella and aquélla
            if strip_accents(inflection) != strip_accents(lemma):
                fixed_inflections.append(inflection)
        
        # Remove duplicates from the inflections
        fixed_inflections = list(set(fixed_inflections))

        already_separated_nodiacritic_inflections = set()

        rest_inflections = []

        for inflection in fixed_inflections:
            nodiacritic_inflection = strip_accents(inflection).lower() 
            if nodiacritic_inflection not in already_separated_nodiacritic_inflections and \
                 (nodiacritic_inflection in lemmas_lower_without_diacritics or \
                     nodiacritic_inflection_counts[nodiacritic_inflection] > 1):
                new_entry_word_list = ["HTML_HEAD<b>" +
                            lemma + "</b>", inflection]
                glos.addEntryObj(glos.newEntry(
                    new_entry_word_list, definition, defiFormat))
                already_separated_nodiacritic_inflections.add(
                    nodiacritic_inflection)
            else: 
                rest_inflections.append(inflection)
        
        all_forms = ["HTML_HEAD<b>" + lemma + "</b>", lemma]
        all_forms.extend(rest_inflections)
        glos.addEntryObj(glos.newEntry(all_forms, definition, defiFormat))

    return glos

if __name__ == "__main__":
    KINDLEGEN_PATH = "C:/Users/hanne/AppData/Local/Amazon/Kindle Previewer 3/lib/fc/bin/kindlegen.exe"

    entries = load_tabfile("Es-En.txt")

    glos = fix_entry_list(entries)

    print("Creating dictionary")
    glos.setInfo("title", "Spanish-English dictionary")
    glos.setInfo("author", "Vuizur")
    glos.sourceLangName = "Spanish"
    glos.targetLangName = "English"
    print("Writing dictionary")
    glos.write("Spanish_English-Dictionary", format="Mobi", keep=True, exact=True, spellcheck=False,
               kindlegen_path=KINDLEGEN_PATH)
    
