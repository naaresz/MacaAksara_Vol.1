# Javanese to Indonesian Dictionary and Transliteration Processor

JAVANESE_TO_INDONESIAN = {
    "maca": "membaca",
    "aksara": "aksara / huruf",
    "jawa": "Jawa",
    "sega": "nasi",
    "bapa": "bapak / ayah",
    "ibu": "ibu",
    "tuku": "membeli",
    "turu": "tidur",
    "mangan": "makan",
    "ngombe": "minum",
    "kopi": "kopi",
    "susu": "susu",
    "adus": "mandi",
    "dahar": "makan (halus/krama)",
    "tindak": "pergi (halus/krama)",
    "rawuh": "datang (halus/krama)",
    "sare": "tidur (halus/krama)",
    "luwe": "lapar",
    "kencot": "lapar (ngoko)",
    "wara": "berita / pengumuman",
    "kana": "sana",
    "rata": "rata / datar",
    "gajah": "gajah",
    "macan": "harimau",
    "kucing": "kucing",
    "pitik": "ayam",
    "iwak": "ikan",
    "sura": "berani",
    "baya": "buaya",
    "karta": "makmur / subur",
    "sala": "Solo (Surakarta)",
    "desa": "desa",
    "negara": "negara",
    "kanca": "teman",
    "dalan": "jalan",
    "omah": "rumah",
    "banyu": "air",
    "geni": "api",
    "angin": "angin",
    "lemah": "tanah",
    "langit": "langit",
    "lintang": "bintang",
    "rembulan": "bulan",
    "srengenge": "matahari",
    "sabar": "sabar",
    "seneng": "senang / suka",
    "sedih": "sedih",
    "sinahu": "belajar",
    "apik": "bagus / baik",
    "elek": "jelek",
    "anyar": "baru",
    "lawas": "lama / kuno",
    "gedhe": "besar",
    "cilik": "kecil",
    "dhuwur": "tinggi",
    "cendhek": "rendah / pendek",
    "adoh": "jauh",
    "cedhak": "dekat",
    "siji": "satu",
    "loro": "dua",
    "telu": "tiga",
    "papat": "empat",
    "lima": "lima",
    "nem": "enam",
    "pitu": "tujuh",
    "wolu": "delapan",
    "sanga": "sembilan",
    "sepuluh": "sepuluh",
    "nulis": "menulis",
    "krungu": "mendengar",
    "ndeleng": "melihat",
    "mlaku": "berjalan",
    "mela": "ikut",
    "bocah": "anak",
    "wong": "orang",
    "lanang": "laki-laki",
    "wadon": "perempuan",
    "sapa": "siapa",
    "kowe": "kamu",
    "aku": "saya / aku",
    "dheweke": "dia",
    "sampeyan": "kamu / Anda (krama)",
    "panjenengan": "Anda (krama alus)",
    "apa": "apa",
    "kowe": "kamu",
    "kamu": "kamu",
    "siapa": "siapa",
    "saya": "saya",
    "dia": "dia",
    "bisa": "bisa",
    "ora": "tidak",
    "neng": "di",
    "ing": "di",
    "saka": "dari",
    "menyang": "ke"
}

# Mapping of raw classes to their Javanese Script representations (for cheatsheet/breakdown UI)
SANDHANGAN_INFO = {
    "": "Vokal bawaan /a/",
    "h": "Sandhangan Wignyan (menambahkan konsonan akhir /h/)",
    "ng": "Sandhangan Cecak (menambahkan konsonan akhir /ng/)",
    "r": "Sandhangan Layar (menambahkan konsonan akhir /r/)",
    "e": "Sandhangan Pepet (mengubah vokal menjadi /e/ seperti pada kata 'segar')",
    "è": "Sandhangan Taling (mengubah vokal menjadi /è/ seperti pada kata 'lele')",
    "i": "Sandhangan Wulu (mengubah vokal menjadi /i/)",
    "o": "Sandhangan Taling-Tarung (mengubah vokal menjadi /o/)",
    "u": "Sandhangan Suku (mengubah vokal menjadi /u/)"
}

BASIC_LETTERS = {
    "ha": "ꦲ", "na": "ꦤ", "ca": "ꦕ", "ra": "ꦫ", "ka": "ꦏ",
    "da": "ꦢ", "ta": "ꦠ", "sa": "ꦱ", "wa": "ꦮ", "la": "ꦭ",
    "pa": "ꦥ", "dha": "ꦝ", "ja": "ꦗ", "ya": "ꦪ", "nya": "ꦚ",
    "ma": "ꦩ", "ga": "ꦒ", "ba": "ꦧ", "tha": "ꦛ", "nga": "ꦔ"
}

def is_javanese_word(word):
    word = word.lower().strip()
    if word in JAVANESE_TO_INDONESIAN:
        return True
    # Strip suffixes/prefixes to find base word
    if word.endswith("ne") and word[:-2] in JAVANESE_TO_INDONESIAN:
        return True
    if word.startswith("di") and word[2:] in JAVANESE_TO_INDONESIAN:
        return True
    return False

def group_unmatched_syllables(syllables):
    """
    Groups consecutive unmatched syllables into natural 2-syllable word pairs.
    """
    grouped = []
    m = len(syllables)
    k = 0
    while k < m:
        syl1 = syllables[k]
        
        # Check if next syllable exists and is not a lone final consonant
        if k + 1 < m:
            syl2 = syllables[k+1]
            
            # Check if syl2 is a single final consonant modifier (e.g. 'n', 'ng', 'r', 'h')
            # that should be merged with the current syllable
            is_syl2_consonant = len(syl2) <= 2 and not any(syl2.endswith(v) for v in ["a", "i", "u", "e", "o", "è"])
            
            if is_syl2_consonant:
                # Merge them and try to pair with the next syllable
                if k + 2 < m:
                    grouped.append([syl1, syl2, syllables[k+2]])
                    k += 3
                else:
                    grouped.append([syl1, syl2])
                    k += 2
            else:
                # Normal pair of syllables
                grouped.append([syl1, syl2])
                k += 2
        else:
            # Lone syllable at the end: attach it to the last group to avoid a single-letter word
            if grouped:
                grouped[-1].append(syl1)
            else:
                grouped.append([syl1])
            k += 1
    return grouped

def segment_syllables_to_word_groups(syllables):
    """
    Segments a list of syllables into groups of syllables corresponding to words.
    E.g. ['ma', 'ca', ' ', 'se', 'ga'] -> [['ma', 'ca'], [' '], ['se', 'ga']]
    Uses a hybrid approach: Maximum Matching dictionary lookup + 2-syllable grouping fallback.
    """
    if not syllables:
        return []
        
    # First, split the input syllables list by space tokens
    sublists = []
    current_sub = []
    for syl in syllables:
        if syl == " ":
            if current_sub:
                sublists.append(current_sub)
                current_sub = []
            sublists.append([" "])
        else:
            current_sub.append(syl)
    if current_sub:
        sublists.append(current_sub)
        
    word_groups = []
    for sub in sublists:
        if sub == [" "]:
            word_groups.append([" "])
            continue
            
        n = len(sub)
        i = 0
        unmatched_buffer = []
        
        while i < n:
            matched = False
            for j in range(n, i, -1):
                candidate = "".join(sub[i:j])
                if is_javanese_word(candidate):
                    # Flush unmatched buffer first
                    if unmatched_buffer:
                        word_groups.extend(group_unmatched_syllables(unmatched_buffer))
                        unmatched_buffer = []
                        
                    word_groups.append(sub[i:j])
                    i = j
                    matched = True
                    break
            if not matched:
                unmatched_buffer.append(sub[i])
                i += 1
                
        # Flush remaining unmatched syllables at the end
        if unmatched_buffer:
            word_groups.extend(group_unmatched_syllables(unmatched_buffer))
            
    return word_groups

def clean_and_format_transliteration(syllables):
    """
    Cleans up a list of recognized syllables and joins them into words with spaces.
    E.g. ['ma', 'ca', 'se', 'ga'] -> 'maca sega', 'moco sego'
    """
    if not syllables:
        return "", ""
        
    word_groups = segment_syllables_to_word_groups(syllables)
    
    latin_words = []
    pron_words = []
    
    for group in word_groups:
        if group == [" "]:
            latin_words.append(" ")
            pron_words.append(" ")
            continue
            
        # Latin word
        latin_word = "".join(group)
        latin_words.append(latin_word)
        
        # Pronunciation word: apply A-to-O logic only if the word ends with 'a'
        pron_parts = []
        if latin_word.endswith("a"):
            for syl in group:
                if syl.endswith("a") and len(syl) <= 3:
                    pron_parts.append(syl[:-1] + "o")
                else:
                    pron_parts.append(syl)
        else:
            for syl in group:
                pron_parts.append(syl)
                
        pron_word = "".join(pron_parts)
        pron_words.append(pron_word)
        
    # Join and format
    # Join with spaces, then collapse multiple spaces and strip
    def join_clean(words_list):
        joined = ""
        for w in words_list:
            if w == " ":
                joined += " "
            else:
                if joined and not joined.endswith(" "):
                    joined += " "
                joined += w
        return joined.replace("  ", " ").strip()
        
    latin_text = join_clean(latin_words)
    pron_text = join_clean(pron_words)
    
    return latin_text, pron_text

def translate_javanese_to_indonesian(latin_text):
    """
    Translates Latin Javanese text into Indonesian by split-matching words.
    """
    if not latin_text:
        return "Tidak ada teks untuk diterjemahkan."
        
    words = latin_text.lower().strip().split()
    translated_words = []
    
    for word in words:
        # Direct dictionary match
        if word in JAVANESE_TO_INDONESIAN:
            translated_words.append(JAVANESE_TO_INDONESIAN[word])
        # Try to strip basic Javanese prefixes/suffixes if not found
        elif word.endswith("ne") and word[:-2] in JAVANESE_TO_INDONESIAN:
            base_trans = JAVANESE_TO_INDONESIAN[word[:-2]]
            translated_words.append(f"{base_trans}-nya")
        elif word.startswith("di") and word[2:] in JAVANESE_TO_INDONESIAN:
            base_trans = JAVANESE_TO_INDONESIAN[word[2:]]
            translated_words.append(f"di-{base_trans}")
        else:
            translated_words.append(f"[{word}]") # Keep untranslated words in brackets
            
    return " ".join(translated_words)

CONSONANT_TO_BASE = {
    "h": "ha", "n": "na", "c": "ca", "r": "ra", "k": "ka",
    "d": "da", "t": "ta", "s": "sa", "w": "wa", "l": "la",
    "p": "pa", "dh": "dha", "j": "ja", "y": "ya", "ny": "nya",
    "m": "ma", "g": "ga", "b": "ba", "th": "tha", "ng": "nga"
}

def get_character_breakdown(syllable):
    """
    Deconstructs a syllable into its Javanese base character and sandhangan.
    E.g. 'bo' -> Base: 'ba', Sandhangan: 'o' (Taling-Tarung)
    """
    syllable = syllable.strip().lower()
    
    if syllable == "pangkon" or syllable == "꧀":
        return {
            "syllable": "꧀",
            "base": "pangkon",
            "sandhangan": "pangkon",
            "base_desc": "Tanda Pangkon (꧀)",
            "sandhangan_desc": "Tanda penyangga/paten (menghilangkan vokal bawaan /a/ di akhir kata)"
        }
        
    # Check if it is a muted consonant (pasangan/pangkon)
    if syllable in CONSONANT_TO_BASE:
        base_char = CONSONANT_TO_BASE[syllable]
        return {
            "syllable": syllable,
            "base": base_char,
            "sandhangan": "pasangan",
            "base_desc": f"Aksara dasar '{base_char}'",
            "sandhangan_desc": "Mati / Pasangan (menghilangkan vokal bawaan /a/)"
        }
        
    # Check if direct match in Javanese basic letters
    if syllable in BASIC_LETTERS:
        return {
            "syllable": syllable,
            "base": syllable,
            "sandhangan": "",
            "base_desc": f"Aksara dasar '{syllable}'",
            "sandhangan_desc": "Tanpa sandhangan (vokal bawaan /a/)"
        }
        
    # Search for sandhangan modifiers
    modifiers = ["ng", "ah", "h", "r", "è", "e", "i", "o", "u"]
    for mod in modifiers:
        if syllable.endswith(mod):
            # Special case for 'ah' which is parsed as 'h' (wignyan)
            actual_mod = "h" if mod == "ah" else mod
            base_char = syllable[:-len(mod)] + "a"
            
            # Double check if base char is valid
            if base_char in BASIC_LETTERS or base_char == "nga":
                return {
                    "syllable": syllable,
                    "base": base_char,
                    "sandhangan": actual_mod,
                    "base_desc": f"Aksara dasar '{base_char}'",
                    "sandhangan_desc": SANDHANGAN_INFO.get(actual_mod, "Sandhangan aksara")
                }
                
    # Fallback if parsing fails
    return {
        "syllable": syllable,
        "base": syllable,
        "sandhangan": "",
        "base_desc": f"Aksara '{syllable}'",
        "sandhangan_desc": "Modifikasi sandhangan tidak terdeteksi secara spesifik."
    }
