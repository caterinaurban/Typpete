from typing import Dict, TypeVar, Type, List, Callable
from .model import Hint, Message, Move, Object, Room, Word

# The Adventure data file knows only the first five characters of each
# word in the game, so we have to know the full verion of each word.

long_words = { w[:5]: w for w in """upstream downstream forest
forward continue onward return retreat valley staircase outside building stream
cobble inward inside surface nowhere passage tunnel canyon awkward
upward ascend downward descend outdoors barren across debris broken
examine describe slabroom depression entrance secret bedquilt plover
oriental cavern reservoir office headlamp lantern pillow velvet fissure tablet
oyster magazine spelunker dwarves knives rations bottle mirror beanstalk
stalactite shadow figure drawings pirate dragon message volcano geyser
machine vending batteries carpet nuggets diamonds silver jewelry treasure
trident shards pottery emerald platinum pyramid pearl persian spices capture
release discard mumble unlock nothing extinguish placate travel proceed
continue explore follow attack strike devour inventory detonate ignite
blowup peruse shatter disturb suspend sesame opensesame abracadabra
shazam excavate information""".split(" ") }

class Data(object):
    def __init__(self):
        self.rooms = {}
        self.vocabulary = {}
        self.objects = {}
        self.messages = {}
        self.class_messages = []
        self.hints = {}
        self.magic_messages = {}
        self._last_travel_first = 0
        self._last_travel_second = []
        self._object = None

    def referent(self, word):
        if word.kind == 'noun':
            return self.objects[word.n % 1000]


# KEYS = TypeVar("KEYS", bound=int)
# VALS = TypeVar("VALS", bound='HasN')
# def make_object(dictionary: Dict[int, VALS], klass: Callable[[], VALS], n: int) -> VALS:
def make_object(dictionary, klass, n):
    obj = None
    if n not in dictionary:
        obj = klass()
        dictionary[n] = obj
        obj.n = n
    if (1 == 2):
        return obj
    return dictionary[n]

def expand_tabs(segments):
    it = iter(segments)
    line = next(it)
    for segment in it:
        spaces = 8 - len(line) % 8
        line += ' ' * spaces + segment
    return line


def accumulate_message(dictionary, n, line):
    dictionary[n] = dictionary.get(n) + line + '\n'

def section1(data, n, etc):
    room = make_object(data.rooms, lambda :Room(), n)
    if not etc[0].startswith('>$<'):
        room.long_description += expand_tabs(etc) + '\n'

def section2(data, n, line):
    make_object(data.rooms, lambda :Room(), n).short_description += line + '\n'

def section3(data, x, y, verbs):
    last_travel_first = data._last_travel_first
    last_travel_second = data._last_travel_second
    if last_travel_first == x and last_travel_second[0] == verbs[0]:
        verbs = last_travel_second  # same first verb implies use whole list
    else:
        data._last_travel_first = x
        data._last_travel_second = verbs

    m, n = divmod(y, 1000)
    mh, mm = divmod(m, 100)

    condition = (None, None, None)
    if m == 0:
        condition = (None, None, None)
    elif 0 < m < 100:
        condition = ('%', m, None)
    elif m == 100:
        condition = ('not_dwarf', None, None)
    elif 100 < m <= 200:
        condition = ('carrying', mm, None)
    elif 200 < m <= 300:
        condition = ('carrying_or_in_room_with', mm, None)
    elif 300 < m:
        condition = ('prop!=', mm, mh - 3)

    if n <= 300:
        action = make_object(data.rooms, lambda :Room(), n)
    elif 300 < n <= 500:
        action = n  # special computed goto
    else:
        action = make_object(data.messages, lambda :Message(), n - 500)

    move = Move()
    if len(verbs) == 1 and verbs[0] == 1:
        move.is_forced = True
    else:
        move.verbs = [ make_object(data.vocabulary, lambda :Word(), verb_n)
                       for verb_n in verbs if verb_n < 100 ] # skip bad "109"
    move.condition = condition
    move.action = action
    data.rooms[x].travel_table.append(move)

def section4(data, n, text, etc):
    text = text.lower()
    text = long_words.get(text)
    word = make_object(data.vocabulary, lambda :Word(), n)
    if word.text is None:  # this is the first word with index "n"
        word.text = text
    else:  # there is already a word sitting at "n", so create a synonym
        original = word
        word = Word()
        word.n = n
        word.text = text
        original.add_synonym(word)
    word.kind = ['travel', 'noun', 'verb', 'snappy_comeback'][n // 1000]
    if word.kind == 'noun':
        n %= 1000
        obj = make_object(data.objects, lambda :Object(), n)
        obj.names.append(text)
        obj.is_treasure = (n >= 50)
        data.objects[n] = obj
    if text not in data.vocabulary:  # since duplicate names exist
        data.vocabulary[n] = word

def section5(data, n, etc):
    if 1 <= n <= 99:
        data._object = make_object(data.objects, lambda :Object(), n)
        data._object.inventory_message = expand_tabs(etc)
    else:
        n //= 100
        messages = data._object.messages
        if etc[0].startswith('>$<'):
            more = ''
        else:
            more = expand_tabs(etc) + '\n'
        messages[n] = messages.get(n) + more

def section6(data, n, etc):
    message = make_object(data.messages, lambda :Message(), n)
    message.text += expand_tabs(etc) + '\n'


def section7(data, n, room_n, etc):
    if not room_n:
        return
    obj = make_object(data.objects, lambda :Object(), n)
    room = make_object(data.rooms, lambda :Room(), room_n)
    obj.drop(room)
    if len(etc):
        if etc[0] == -1:
            obj.is_fixed = True
        else:
            room2 = make_object(data.rooms, lambda :Room(), etc[0])
            obj.rooms.append(room2)  # exists two places, like grate
    obj.starting_rooms = obj.rooms  # remember where things started


def section8(data, word_n, message_n):
    if not message_n:
        return
    word = make_object(data.vocabulary, lambda :Word(), word_n + 2000)
    message = make_object(data.messages, lambda :Message(), message_n)
    for word2 in word.synonyms:
        word2.default_message = message


def section9(data, bit, nlist):
    for n in nlist:
        room = make_object(data.rooms, lambda :Room(), n)
        if bit == 0:
            room.is_light = True
        elif bit == 1:
            room.liquid = make_object(data.objects, lambda :Object(), 22) #oil
        elif bit == 2:
            room.liquid = make_object(data.objects, lambda :Object(), 21) #water
        elif bit == 3:
            room.is_forbidden_to_pirate = True
        else:
            hint = make_object(data.hints, lambda :Hint(), bit)
            hint.rooms.append(room)

def section10(data, score, line, etc):
    data.class_messages.append((score, line))

def section11(data, n, turns_needed, penalty, question_n, message_n):
    hint = make_object(data.hints, lambda :Hint(), n)
    hint.turns_needed = turns_needed
    hint.penalty = penalty
    hint.question = make_object(data.messages, lambda :Message(), question_n)
    hint.message = make_object(data.messages, lambda :Message(), message_n)

def section12(data, n, line):
    accumulate_message(data.magic_messages, n, line)
