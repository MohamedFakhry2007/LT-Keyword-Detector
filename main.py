from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
import re
from collections import Counter

app = Flask(__name__)


def get_h3_tags(soup):
    h3_tags = soup.find_all("h3")
    h3_text = []
    for tag in h3_tags:
        h3_text.append(tag.text)
    return h3_text


def get_h2_tags(soup):
    h2_tags = soup.find_all("h2")
    h2_text = []
    for tag in h2_tags:
        h2_text.append(tag.text)
    return h2_text


def get_h1_tags(soup):
    h1_tags = soup.find_all("h1")
    h1_text = []
    for tag in h1_tags:
        h1_text.append(tag.text)
    return h1_text


def get_bold_italic_underlined_text(soup):
    bold_text = soup.find_all("b")
    italic_text = soup.find_all("i")
    underlined_text = soup.find_all("u")
    combined_text = []

    for text in bold_text:
        combined_text.append(text.text)
    for text in italic_text:
        combined_text.append(text.text)
    for text in underlined_text:
        combined_text.append(text.text)

    return combined_text


def get_first_two_paragraphs(soup):
    paragraphs = soup.find_all("p")
    if len(paragraphs) >= 3:
        return "\n".join([paragraph.get_text() for paragraph in paragraphs[:3]])
    else:
        return None


def get_meta_description(soup):
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        return meta_desc.get("content")
    else:
        meta_desc = soup.find("meta", attrs={"property": "og:description"})
        if meta_desc:
            return meta_desc.get("content")
        else:
            meta_desc = soup.find("meta", attrs={"name": "twitter:description"})
            if meta_desc:
                return meta_desc.get("content")
            else:
                return None


def get_meta_title(soup):
    # Check for title in meta name tag
    meta_title = soup.select_one("meta[name=title]")
    if meta_title:
        return meta_title.get("content")

    # Check for title in meta property tag
    meta_title = soup.find("meta", attrs={"property": "og:title"})
    if meta_title:
        return meta_title.get("content")

    # Check for title in meta name tag with content attribute
    meta_title = soup.find("meta", attrs={"name": "og:title", "content": True})
    if meta_title:
        return meta_title.get("content")

    # Check for title in title tag
    title = soup.find("title")
    if title:
        return title.text

    # If title cannot be found in any of the 4 cases
    return None


def get_html_elements(theurl):
    # Make a GET request to the URL
    page = requests.get(theurl)
    # Check if the request was successful
    if page.status_code == 200:
        # Use BeautifulSoup to parse the HTML content of the page
        soup = BeautifulSoup(page.content, 'html.parser')
        # Return the HTML elements of the page as a variable
        return soup
    else:
        # If the request was not successful, return an error message
        return "Could not retrieve HTML elements. Check the URL and try again."


def get_text_from_url(theurl):
    text = re.sub(r'^https?://[^/]+/', '', theurl)
    words = re.split(r'[-\.]', text)
    return ' '.join(words)


def split_text(text):
    words = re.findall(r'\w+', text)
    return [word.lower() for word in words]


def most_used_phrases(geturl, metatitle, metadescription):
    texts = [geturl, metatitle, metadescription]
    all_phrases = []
    for text in texts:
        words = split_text(text)
        phrases = [words[i] + " " + words[i+1] + " " + words[i+2] + " " + words[i+3] for i in range(len(words) - 3)]
        all_phrases += phrases
    phrase_counts = Counter(all_phrases)
    return phrase_counts.most_common(3)


def most_used_text_in_h(h1tags):
    all_phrases = []
    for text in h1tags:
        words = split_text(text)
        phrases = [words[i] + " " + words[i+1] + " " + words[i+2] + " " + words[i+3] for i in range(len(words) - 3)]
        all_phrases += phrases
    phrase_counts = Counter(all_phrases)
    return phrase_counts.most_common(3)


def most_used_text_in_p(text):
    all_phrases = []
    words = text.split()
    phrases = [words[i] + " " + words[i+1] + " " + words[i+2] + " " + words[i+3] for i in range(len(words) - 3)]
    all_phrases += phrases
    phrase_counts = Counter(all_phrases)
    return phrase_counts.most_common(3)


def compare_lists(lists):
    all_phrases = []
    for lst in lists:
        all_phrases += [item[0] for item in lst]
    phrase_counts = Counter(all_phrases)
    return phrase_counts.most_common(3)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/result", methods=["POST"])
def result():
    theurl = request.form["text_field"]
    soup = get_html_elements(theurl)
    geturl = get_text_from_url(theurl)
    metatitle = get_meta_title(soup)
    metadescription = get_meta_description(soup)
    openingp = get_first_two_paragraphs(soup)
    styledtext = get_bold_italic_underlined_text(soup)
    h1tags = get_h1_tags(soup)
    h2tags = get_h2_tags(soup)
    h3tags = get_h3_tags(soup)
    probability1 = most_used_phrases(geturl, metatitle, metadescription)
    print(type(probability1))
    commoninh1 = most_used_text_in_h(h1tags)
    print(type(commoninh1))
    commoninh2 = most_used_text_in_h(h2tags)
    print(type(commoninh2))
    commoninh3 = most_used_text_in_h(h3tags)
    print(type(commoninh3))
    commoninp = most_used_text_in_p(openingp)
    print(type(commoninp))
    liststoanalyze = [probability1, commoninh1, commoninh2, commoninh3, commoninp]
    winningkeywords = compare_lists(liststoanalyze)
    return render_template("result.html", metatitle=metatitle, metadescription=metadescription,
                           openingp=openingp, styledtext=styledtext, geturl=geturl,
                           h1tags=h1tags, h2tags=h2tags, h3tags=h3tags, probability1=probability1,
                           commoninh1=commoninh1, commoninh2=commoninh2, commoninh3=commoninh3,
                           commoninp=commoninp, winningkeywords=winningkeywords)


if __name__ == "__main__":
    app.run(debug=True)
