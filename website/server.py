from flask import Flask, request, Response
from flask_cors import CORS
from pdfminer.high_level import extract_text
import jsonpickle
from werkzeug.utils import secure_filename
from threading import Thread
import time
import random
import string
import urllib.parse
import requests as req
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.corpus import stopwords
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = '/uploaded_files'

pdfs = {}


def get_file_id():
    return ''.join((random.choice(string.ascii_lowercase + string.ascii_uppercase)) for x in range(20))


def read_abstract(tag):
    return pdfs[tag]["text"].split('\n\nabstract', 1)[1].split("\n\nindex", 1)[0].replace('\n', ' ')


def read_references(tag):
    references = pdfs[tag]["text"].split('\n\nreferences', 1)[1].split('\n\n[')
    pdfs[tag]["num_ref"] = len(references)
    ref_link = []
    del_ref = []
    for i in range(pdfs[tag]["num_ref"]):
        if len(references[i]) < 5:
            del_ref.append(i)
            continue
        references[i] = references[i].split('] ')[1].replace('\n', ' ')
        ref_link.append("https://scholar.google.com/scholar?hl=en&as_sdt=0%2C5&q=" + urllib.parse.quote_plus(
            references[i].replace(" ", "+")) + "&btnG=")

    for i in del_ref:
        del references[i]
    pdfs[tag]["num_ref"] = len(references)
    print(len(references))
    print(pdfs[tag]["num_ref"])

    pdfs[tag]["refs"] = references
    return ref_link


def preprocess_text(sen):
    # Remove punctuations and numbers
    sentence = re.sub('[^a-zA-Z]', ' ', sen)

    # Single character removal
    sentence = re.sub(r"\s+[a-zA-Z]\s+", ' ', sentence)

    # Removing multiple spaces
    sentence = re.sub(r'\s+', ' ', sentence)

    return sentence


def fetch_abstracts(tag):
    abstract_results = []
    for i in range(pdfs[tag]["num_ref"]):
        print(f"fetch: {i}")
        abstract_results.append(req.get(pdfs[tag]["ref_link"][i]).text)
        time.sleep(10)
    print(f"len of abs results: {len(abstract_results)}")
    print(f"len of extracted refs: {len(pdfs[tag]['refs'])}")

    references_abstract = []
    ref_selected = []
    for i in range(len(abstract_results)):
        if "did not match" not in abstract_results[i] and "not a robot when JavaScript" not in abstract_results[i]:
            ref_selected.append(pdfs[tag]["refs"][i])
            print(f"Selected: {i}")
            references_abstract.append(
                abstract_results[i].split('</div><div class="gs_rs">', 1)[1].split('</div>', 1)[0].replace("<br>",
                                                                                                           "").replace(
                    "<b>", "").replace("</b>", "").replace("&#8230;", ""))

    references_abstract.insert(0, pdfs[tag]['abstract'])
    for i in range(len(references_abstract)):
        references_abstract[i] = preprocess_text(references_abstract[i]).lower()

    abstract_vectorized = TfidfVectorizer(stop_words=stopwords.words('english')).fit_transform(references_abstract)
    similarity = abstract_vectorized * abstract_vectorized.T
    similarity = similarity.toarray()
    abs_similarity = []
    for i in range(similarity.shape[0]):
        abs_similarity.append(float(similarity[i, 0]))
    print(f"len of cosine similarity: {len(abs_similarity[1:])}")
    print(f"len of selected refs: {len(ref_selected)}")

    pdfs[tag]['similarity'] = abs_similarity[1:]
    pdfs[tag]['refs_selected'] = ref_selected


@app.route('/upload', methods=['POST'])
def pdf_upload():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save("./uploaded_files/" + filename)

    text = extract_text("./uploaded_files/" + filename)
    file_id = get_file_id()
    pdfs[file_id] = {
        "text": text.lower()
    }
    pdfs[file_id]['abstract'] = read_abstract(file_id)
    pdfs[file_id]['ref_link'] = read_references(file_id)
    sim_process = Thread(target=fetch_abstracts, name=file_id, args=[file_id])
    sim_process.start()

    res = {"file_id": file_id, "time": pdfs[file_id]["num_ref"] * 13 + 5}
    return Response(response=jsonpickle.encode(res), status=200, mimetype='application/json')


@app.route("/update", methods=["POST"])
def get_updates():
    tag = request.json['tag']
    df = pd.DataFrame(data=np.array([pdfs[tag]["refs_selected"], pdfs[tag]["similarity"]]).transpose(), columns=['Reference', 'Similarity'])
    df.to_csv("data.csv")
    res = {"similarity": pdfs[tag]["similarity"], "refs_selected": pdfs[tag]["refs_selected"]}
    return Response(response=jsonpickle.encode(res), status=200, mimetype='application/json')


if __name__ == '__main__':
    app.run(debug=True)
