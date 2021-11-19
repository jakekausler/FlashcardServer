import json
import urllib.request
from pprint import pprint
import csv
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify
from random import choices
from datetime import datetime
import threading
import sys
import traceback
import re

VERSION = 6

SCHEMA = 'http'
HOST = '192.168.2.100'
PORT = 8765

DECK = 'All::Vocabulary'

DATABASE = 'database4.txt'

PHI = (1 + 5 ** 0.5) / 2

USE_AUDIO = False

MEMORY = 5

def anki_request(action, **params):
    return {'action': action, 'params': params, 'version': VERSION}

def invoke(action, **params):
    requestJson = json.dumps(anki_request(action, **params)).encode('utf-8')
    response = json.load(urllib.request.urlopen(urllib.request.Request('{}://{}:{}'.format(SCHEMA, HOST, PORT), requestJson)))
    if len(response) != 2:
        raise Exception('resonse has an unexpected number of fields')
    if 'error' not in response:
        raise Exception('response requires an "error" field')
    if 'result' not in response:
        raise Exception('response requires a "result" field')
    if response['error'] is not None:
        raise Exception(response['error'])
    return response['result']

def getLeeches():
    try:
        cardIds = invoke('findCards', query='deck:{} tag:leech'.format(DECK))
        cardDetails = invoke('cardsInfo', cards=cardIds)
        leeches = []
        for card in cardDetails:
            audioSearch = ""
            if USE_AUDIO:
                audioPattern = r'\[sound:(.*)\]'
                audioSearch = re.search(audioPattern, card['fields']['Front']['value'])
                if audioSearch:
                   audioSearch = audioSearch.group(1)
                else:
                    audioSearch = "" 
            leeches.append(Card(card['note'], format_card(card['fields']['Front']['value']), format_card(card['fields']['Back']['value']), audio=audioSearch))
        print("Leeches fetched at {}".format(datetime.now()))
        return leeches
    except Exception as e:
        print()
        print('Unable to get leeches:')
        traceback.print_tb(e)
        print()
        return []

cards = {}
past_cards = []

def getAverageScore():
    if len(cards) == 0:
        return 1
    return int(round(sum(cards[id].score for id in cards)/len(cards)))

def getMaxScore():
    return max(cards[id].score for id in cards) 

class Card:
    def __init__(self, id, front, back, score=-1, audio=""):
        self.id = id
        self.front = front
        self.back = back
        self.score = score if score > 0 else getAverageScore()
        self.audio = audio

    def __repr__(self):
        return self.front + ': ' + self.back

    def toDict(self):
        return {
            'id': self.id,
            'front': self.front,
            'back': self.back,
            'score': self.score,
            'audio': self.audio,
            'maxScore': getMaxScore()
        }

def saveCards():
    with open(DATABASE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter='\t')
        for id in cards:
            card = cards[id]
            writer.writerow([card.id, card.front, card.back, card.score, card.audio])

def loadCards():
    with open(DATABASE, encoding='utf-8') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if len(row) != 0:
                cards[row[0]] = Card(row[0], row[1], row[2], int(row[3]), row[4])
    for leech in getLeeches():
        if leech.id not in cards:
            cards[leech.id] = leech

def format_card(text):
    return re.sub(r'\[.*\]', '', text).replace("<br/>", "").replace("<br>", "").replace("</br>", "")

def updateScore(id, score):
    cards[id].score += score
    while cards[id].score <= 0:
        for id in cards:
            cards[id].score += 1

def nthFibbonacci(n):
    return round(((PHI ** n) - ((-PHI)**(-n))) / (5 ** 0.5))

def getRandomCard():
    id_list = list(cards.keys())
    weight_list = [min(1000, nthFibbonacci(cards[id].score)) for id in cards]
    chosen = cards[choices(id_list, weights=weight_list)[0]]
    while chosen.front in past_cards:
        chosen = cards[choices(id_list, weights=weight_list)[0]]
    if len(past_cards) >= MEMORY:
        past_cards.pop(0)
    past_cards.append(chosen.front)
    return chosen

app = Flask(__name__)
app.config['DEBUG'] = False

def runApp():
    refresh()
    app.run(host='0.0.0.0')

@app.route('/', methods=['GET'])
def home():
    return render_template('index.html')

@app.route('/api/sendScore', methods=['POST'])
def sendScore():
    data = request.json
    updateScore(data["id"], data["score"])
    saveCards()
    return json.dumps({'success':True}), 200, {'ContentType':'application/json'}

@app.route('/api/getCard', methods=['GET'])
def getCard():
    card = getRandomCard()
    return jsonify(card.toDict())

def refresh():
    threading.Timer(60*60, refresh).start()
    loadCards()
    saveCards()

if __name__ == '__main__':
    #loadCards()
    #saveCards()
    runApp()
