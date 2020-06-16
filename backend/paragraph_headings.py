# Install Modules
# !pip install pysbd
# !pip install spacy-universal-sentence-encoder
# !pip install sumy
# !pip install spacy==2.1.0
# !pip install neuralcoref

'''
Input : text
Output : List of tuples [(heading1,para1),...]

Threshold:
Similarity_threshold = Degree of similarity between two sentences (paragraph function)
Word_threshold = Number of words in a paragraph (paragraph function)
Sentence_threshold = Number of sentences in a paragraph (get_titles_paras function)
''' 
from collections import Counter
import pysbd
from math import floor
import spacy
import neuralcoref
import spacy.cli

import math
import numpy as np
import os
# import tensorflow_hub as hub
from sklearn.metrics.pairwise import cosine_similarity

spacy.cli.download('en_core_web_lg')
nlp = spacy.load('en_core_web_lg')
neuralcoref.add_to_pipe(nlp)

def paragraph(text,model,similarity_threshold=0.27,word_threshold = 20):
    # Sentence Boundary Detection
    seg = pysbd.Segmenter(language="en", clean=True)
    sentences = seg.segment(text) # List of sentences as string
    # print("Number of sentences : ",len(res))

    # Sentence Similarity : USE - Universal Sentence Encoder
    embedding = model(sentences)
    similarity = cosine_similarity(embedding, embedding)
    
    para = ''
    n = len(similarity)
    for i in range(n-1):
        first = sentences[i]
        second = sentences[i+1]
        similar = similarity[i][i+1]
        similar = round(similar,2)
        # print("Sentence ",i,',',i+1," : ",similar)
        
        if similar < 0: 
            continue

        if similar >= similarity_threshold:
            para += first.strip() + ' '

        else:
            para += first.strip() + '\n'
        
    para += second.strip()        

    # Merge Small Sentences with the previous para
    p = para.split('\n')
    final = ''
    for i in range(1,len(p)):
        small = len(p[i-1].split(' '))

        if small >= word_threshold:
            final += p[i-1] + '\n'
      
        else:
            final += p[i-1] + ' '

    final += p[len(p)-1]

    return final.split('\n')    # List of paragraphs

def GenerateTitle(i):
    string=""
    isfound=False
    doc = nlp(i)
    nlp.remove_pipe("neuralcoref")
    coref = neuralcoref.NeuralCoref(nlp.vocab)
    nlp.add_pipe(coref, name='neuralcoref')

    #remove stopwords and punctuations
    words = [token.text for token in doc if token.is_stop != True and token.is_punct != True]
    Nouns = [chunk.text for chunk in doc.noun_chunks]
    Adjectives = [token.lemma_ for token in doc if token.pos_ == "ADJ"]
    word_freq = Counter(words)
    word_freqNoun = Counter(Nouns)
    word_freqADJ = Counter(Adjectives)
    common_words = word_freq.most_common(5)
    common_wordsNoun = word_freqNoun.most_common(10)
    common_wordsADJ = word_freqADJ.most_common(10)
    maxcount = common_words[0][1]
    Range = min(len(common_wordsNoun),len(common_wordsADJ))

    for j in range(Range):
        title2 = common_wordsADJ[j][0]+" "+common_wordsNoun[j][0]
        if title2 in i:
            # print("Adjective + Noun Title : ",title2)
            break

    for j in common_words:
        if j[1]==maxcount:
            string+=j[0]+" "
    string = string[:-1]
    while not isfound:
        if string in i:
            isfound = True
            title1 = string
            # print("Title : ",title1)
        else :
            string = ' '.join(string.split(' ')[:-1])
    title = [common_wordsNoun[0][0]]
    title = ' '.join(title)
    # print("Noun Title : ",title)

    if title1 != '' : 
        return title1
    
    elif title != '':
        return title

    else:
        return ''

def get_titles_paras(list_para,sentence_threshold = 5):
    no_of_para = len(list_para)
    seg = pysbd.Segmenter(language="en", clean=True)
    sent = seg.segment(' '.join(list_para)) # List of sentences as string
    no_of_sent = len(sent)

    # print("\nNumber of paragraphs : ",no_of_para)
    # print("Number of sentences : ",no_of_sent)

    i=0
    in_para = ''
    title = []
    while(i<no_of_para):
        in_para = in_para + ' ' + list_para[i]
        seg = pysbd.Segmenter(language="en", clean=True)
        res = seg.segment(in_para) # List of sentences as string

        if len(res) >= sentence_threshold:
            # print(len(res))
            heading = GenerateTitle(in_para).strip().upper()
            title.append((heading,in_para))
            in_para = ''

        i+=1

    if in_para != '':
        # print(len(res))
        heading = GenerateTitle(in_para).strip().upper()
        title.append((heading,in_para))

    with open("paragraph_headings.txt","w",encoding="utf-8") as f:
        for i,j in title:
            f.write(i + " $ " + j.strip() + "\n")

    return title


if __name__ == '__main__':
    module_url = "https://tfhub.dev/google/universal-sentence-encoder/4"
    model = hub.load(module_url)
    
    text = input("Enter transcript : ")
    list_para = paragraph(text,model)
    title_para = get_titles_paras(list_para)

    print(title_para)