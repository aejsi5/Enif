from .models import *
from django.conf import settings
import os
import json
import numpy as np
import spacy
nlp = spacy.load('de_core_news_md')


class PreProcessor:
    def __init__(self):
        base_dir = settings.MEDIA_ROOT
        self.filename = os.path.join(base_dir, str("dnn/preprocessed_data.json"))
        try:
            with open(self.filename, encoding='utf-8') as f:
                data = json.load(f)
                self.words = data['words']
                self.labels = data['labels']
                self.stopwords = data['stopwords']
                self.training = np.array(data['training'])
                self.output = np.array(data['output'])
        except:
            self.get_training_data()

    def get_training_data(self):

        words = []
        stopwords = [x.Pattern for x in Stopword.objects.filter(D=False)]
        labels = []
        docs_x = []
        docs_y = []

        patterns = Pattern.objects.filter(D=False)
        for p in patterns:
            wrds = nlp.tokenizer(p.Pattern)
            wrds_a = []
            for w in wrds:
                l = w.lemma_
                if l not in stopwords:
                    wrds_a.append(l.lower())
            words.extend(wrds_a)
            docs_x.append(wrds_a)
            docs_y.append(p.Intent.ID)
        words = sorted(list(set(words)))

        intents = Intent.objects.filter(D=False)
        for i in intents:
            if i.ID not in labels:
                labels.append(i.ID)
        labels = sorted(labels)

        training = []
        output = []

        out_empty = [0 for _ in range(len(labels))]

        for x, doc in enumerate(docs_x):
            bag = []

            for w in words:
                if w in doc:
                    bag.append(1)
                else:
                    bag.append(0)

            output_row = out_empty[:]
            output_row[labels.index(docs_y[x])] = 1

            training.append(bag)
            output.append(output_row)
        
        with open(self.filename, "w", encoding='utf-8') as f:
            data = {
                "words": words,
                "labels": labels,
                "stopwords": stopwords,
                "training": training,
                "output": output
            }
            json.dump(data, f)

        self.__init__()

def bag_of_words(inp):
    base_dir = settings.MEDIA_ROOT
    filename = os.path.join(base_dir, str("dnn/preprocessed_data.json"))
    with open(filename, encoding='utf-8') as f:
        data = json.load(f)

    bag = [0 for _ in range(len(data['words']))]

    s_words = nlp.tokenizer(inp)
    wrds_a = []
    for i in s_words:
        l = i.lemma_
        if l not in data['stopwords']:
            wrds_a.append(l.lower())

    for l in wrds_a:
        for i, w in enumerate(data['words']):
            if w == l:
                bag[i] = 1
    return np.array(bag)


