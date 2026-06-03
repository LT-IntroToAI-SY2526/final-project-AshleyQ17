import re, string, calendar, requests, time
from bs4 import BeautifulSoup
from match import match
from typing import List, Callable, Tuple, Any, Match


def get_page_html(title: str) -> str:
    search_response = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={"action": "query", "list": "search", "srsearch": title, "format": "json"},
        headers={"User-Agent": "intro-ai-class/1.0"},
        timeout=10
    )
    results = search_response.json().get("query", {}).get("search", [])
    if results:
        title = results[0]["title"]  # use the top search result title
        print(f"Searching Wikipedia for: {title}")
    
    for attempt in range(5):
        response = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "parse",
                "page": title,
                "prop": "text",
                "format": "json",
                "redirects": True,
            },
            headers={"User-Agent": "intro-ai-class/1.0"}
        )
        if response.status_code == 429:
            wait = int(response.headers.get("Retry-After", 5))
            print(f"Rate limited — waiting {wait}s before retrying '{title}'...")
            time.sleep(wait)
            continue
        if response.status_code == 200 and response.text.strip():
            data = response.json()
            if "error" not in data:
                time.sleep(2)  # polite delay after every successful call
                return data["parse"]["text"]["*"]
    raise ConnectionError(f"Could not retrieve Wikipedia page for '{title}' after 5 attempts")


def get_first_infobox_text(html: str) -> str:
    """Gets first infobox html from a Wikipedia page (summary box)

    Args:
        html - the full html of the page

    Returns:
        html of just the first infobox
    """
    soup = BeautifulSoup(html, "html.parser")
    results = soup.find_all(class_="infobox")

    if not results:
        raise LookupError("Page has no infobox")
    return results[0].text


def clean_text(text: str) -> str:
    """Cleans given text removing non-ASCII characters and duplicate spaces & newlines

    Args:
        text - text to clean

    Returns:
        cleaned text
    """
    only_ascii = "".join([char if char in string.printable else " " for char in text])
    no_dup_spaces = re.sub(" +", " ", only_ascii)
    no_dup_newlines = re.sub("\n+", "\n", no_dup_spaces)
    return no_dup_newlines


def get_match(
    text: str,
    pattern: str,
    error_text: str = "Page doesn't appear to have the property you're expecting",
) -> Match:
    """Finds regex matches for a pattern

    Args:
        text - text to search within
        pattern - pattern to attempt to find within text
        error_text - text to display if pattern fails to match

    Returns:
        text that matches
    """
    p = re.compile(pattern, re.DOTALL | re.IGNORECASE)
    match = p.search(text)

    if not match:
        raise AttributeError(error_text)
    return match


def get_polar_radius(planet_name: str) -> str:
    """Gets the radius of the given planet

    Args:
        planet_name - name of the planet to get radius of

    Returns:
        radius of the given planet
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(planet_name)))
    pattern = r"(?:Polar radius|Mean radius)(?:[^\d]*)(?P<radius>[\d,.]+)(?:.*?)km"
    error_text = "Page infobox has no polar radius information"
    match = get_match(infobox_text, pattern, error_text)

    return match.group("radius")


def get_birth_date(name: str) -> str:
    """Gets birth date of the given person

    Args:
        name - name of the person

    Returns:
        birth date of the given person
    """
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Born\D*)(?P<birth>\d{4}-\d{2}-\d{2})"
    error_text = (
        "Page infobox has no birth information (at least none in xxxx-xx-xx format)"
    )
    match = get_match(infobox_text, pattern, error_text)

    return match.group("birth")

def get_death_date(name: str) -> str:
    """Gets death date of the given person"""
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Died\D*)(?P<death>\d{4}-\d{2}-\d{2})"
    error_text = "Page infobox has no death information (xxxx-xx-xx format)"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("death") 

def get_population(place: str) -> str:
    """Gets population of a city/country from its infobox"""
    infobox_text = clean_text(get_first_infobox_text(get_page_html(place)))
    print(infobox_text)
    pattern = r"(?:Population).*(?:City|State capital)(?P<pop>[0-9,]+)"
    error_text = "Page infobox has no population information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("pop")

def get_capital_city(country: str) -> str:
    """Gets the capital city of a country from its infobox"""
    infobox_text = clean_text(get_first_infobox_text(get_page_html(country)))
    print(infobox_text)
    pattern = r"Capital(?:and largest city)?\s*(?P<cap>[A-Z][a-zA-Z\s]+)"
    error_text = "Page infobox has no capital city information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("cap").strip()

def get_age(name: str) -> str:
    """Gets the age of the given person"""
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    # Matches: (age 33)
    pattern = r"\(age\s*(?P<age>\d{1,3})\)"
    error_text = "Page infobox has no age information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("age")

def get_origin(name: str) -> str:
    """Gets the place of birth or origin of the given person"""
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    print(infobox_text)
    # After "(age XX)" capture something like "Medell n, Colombia"
    pattern = r"\(age\s*\d{1,3}\)[^\n]*?(?P<origin>[A-Z][A-Za-z n'.-]+,\s*[A-Z][A-Za-z n'.-]+)"
    error_text = "Page infobox has no origin/birthplace information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("origin").strip()

def get_genre(item: str) -> str:
    """Gets the musical genre of an album or artist"""
    infobox_text = clean_text(get_first_infobox_text(get_page_html(item)))
    print(infobox_text)

    pattern = r"Genre[s]?\s*(?P<genre>[A-Za-z /,\-]+)"
    error_text = "Page infobox has no genre information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("genre").strip()

def get_occupation(name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"Occupation[s]?\s*(?P<occ>[A-Za-z ,/.\-]+)"
    error_text = "Page infobox has no occupation information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("occ").strip()

def get_release_date(item: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(item)))
    pattern = r"Released\s*(?P<date>[A-Za-z0-9 ,]+)"
    error_text = "Page infobox has no release date information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("date").strip()

def get_album_length(item: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(item)))
    pattern = r"Length\s*(?P<length>[0-9:]+)"
    error_text = "Page infobox has no length information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("length").strip()

def get_label(item: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(item)))
    pattern = r"Label[s]?\s*(?P<label>[A-Za-z0-9 ,/.\-]+)"
    error_text = "Page infobox has no label information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("label").strip()

def get_relationship(name: str) -> str:
    "gets the given person's spouse"
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Spouse|Partner|Domestic partner)s?\s*(?P<rel>[A-Za-z .'\-]+)"
    error_text = "Page infobox has no relationship information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("rel").strip()

def get_education(name: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(name)))
    pattern = r"(?:Education|Alma mater|School[s]?)\s*(?P<edu>[A-Za-z0-9 ,.'\-()]+)"
    error_text = "Page infobox has no education information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("edu").strip()
    print(infobox_text)

def get_num_seasons(show: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(show)))
    pattern = r"(?:No\. of seasons|Number of seasons|Seasons)\s*(?P<seasons>\d+)"
    error_text = "Page infobox has no season information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("seasons").strip()

def get_show_release(show: str) -> str:
    infobox_text = clean_text(get_first_infobox_text(get_page_html(show)))
    print(infobox_text)
    pattern = r"(?:Original release|First aired|Original run)\s*(?P<date>[A-Za-z0-9 ,–\-]+)"
    error_text = "Page infobox has no release date information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("date").strip()

def get_creator(show: str) -> str:
    "gets the creator of a tv show"
    infobox_text = clean_text(get_first_infobox_text(get_page_html(show)))
    pattern = r"(?:Created by|Creator|Developed by)\s*(?P<creator>[A-Za-z0-9 ,.'\-()]+)"
    error_text = "Page infobox has no creator information"
    match = get_match(infobox_text, pattern, error_text)
    return match.group("creator").strip()

# below are a set of actions. Each takes a list argument and returns a list of answers
# according to the action and the argument. It is important that each function returns a
# list of the answer(s) and not just the answer itself.


def birth_date(matches: List[str]) -> List[str]:
    """Returns birth date of named person in matches

    Args:
        matches - match from pattern of person's name to find birth date of

    Returns:
        birth date of named person
    """
    return [get_birth_date(" ".join(matches))]


def polar_radius(matches: List[str]) -> List[str]:
    """Returns polar radius of planet in matches

    Args:
        matches - match from pattern of planet to find polar radius of

    Returns:
        polar radius of planet
    """
    return [get_polar_radius(matches[0])]

def death_date(matches: List[str]) -> List[str]:
    return [get_death_date(" ".join(matches))]

def population(matches: List[str]) -> List[str]:
    return [get_population(" ".join(matches))]

def capital_city(matches: List[str]) -> List[str]:
    return [get_capital_city(" ".join(matches))]

def age_action(matches: List[str]) -> List[str]:
    return [get_age(" ".join(matches))]

def origin_action(matches: List[str]) -> List[str]:
    return [get_origin(" ".join(matches))]

def genre_action(matches: List[str]) -> List[str]:
    return [get_genre(" ".join(matches))]

def occupation_action(matches: List[str]) -> List[str]:
    return [get_occupation(" ".join(matches))]

def release_date_action(matches: List[str]) -> List[str]:
    return [get_release_date(" ".join(matches))]

def album_length_action(matches: List[str]) -> List[str]:
    return [get_album_length(" ".join(matches))]

def label_action(matches: List[str]) -> List[str]:
    return [get_label(" ".join(matches))]

def relationship_action(matches: List[str]) -> List[str]:
    return [get_relationship(" ".join(matches))]

def education_action(matches: List[str]) -> List[str]:
    return [get_education(" ".join(matches))]

def seasons_action(matches: List[str]) -> List[str]:
    return [get_num_seasons(" ".join(matches))]

def show_release_action(matches: List[str]) -> List[str]:
    return [get_show_release(" ".join(matches))]

def creator_action(matches: List[str]) -> List[str]:
    return [get_creator(" ".join(matches))]

# dummy argument is ignored and doesn't matter
def bye_action(dummy: List[str]) -> None:
    raise KeyboardInterrupt


# type aliases to make pa_list type more readable, could also have written:
# pa_list: List[Tuple[List[str], Callable[[List[str]], List[Any]]]] = [...]
Pattern = List[str]
Action = Callable[[List[str]], List[Any]]

# The pattern-action list for the natural language query system. It must be declared
# here, after all of the function definitions
pa_list: List[Tuple[Pattern, Action]] = [
    ("when was % born".split(), birth_date),
    ("what is the polar radius of %".split(), polar_radius),
    ("when did % die".split(), death_date),
    ("what is the population of %".split(), population),
    ("what is the capital of %".split(), capital_city),


    # NEW FEATURES    
    ("how old is %".split(), age_action),
    ("where was % born".split(), origin_action),
    ("what is the genre of %".split(), genre_action),
    ("what is the occupation of %".split(), occupation_action),
    ("when was % released".split(), release_date_action),
    ("what is the length of %".split(), album_length_action),
    ("what is the label of %".split(), label_action),
    ("who is % dating".split(), relationship_action),
    ("who is % married to".split(), relationship_action),
    ("what school did % go to".split(), education_action),
    ("how many seasons does % have".split(), seasons_action),
    ("when did % come out".split(), show_release_action),
    ("who created %".split(), creator_action),

    (["bye"], bye_action),
]

def search_pa_list(src: List[str]) -> List[str]:
    """Takes source, finds matching pattern and calls corresponding action. If it finds
    a match but has no answers it returns ["No answers"]. If it finds no match it
    returns ["I don't understand"].

    Args:
        source - a phrase represented as a list of words (strings)

    Returns:
        a list of answers. Will be ["I don't understand"] if it finds no matches and
        ["No answers"] if it finds a match but no answers
    """
    for pat, act in pa_list:
        mat = match(pat, src)
        if mat is not None:
            answer = act(mat)
            return answer if answer else ["No answers"]

    return ["I don't understand"]


def query_loop() -> None:
    """The simple query loop. The try/except structure is to catch Ctrl-C or Ctrl-D
    characters and exit gracefully"""
    print("Welcome to the wikipedia chatbot!\n")
    while True:
        try:
            print()
            query = input("Your query? ").replace("?", "").lower().split()
            answers = search_pa_list(query)
            for ans in answers:
                print(ans)

        except (KeyboardInterrupt, EOFError):
            break

    print("\nSo long!\n")


# uncomment the next line once you've implemented everything are ready to try it out
query_loop()
