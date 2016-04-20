from collections import OrderedDict
from itertools import islice
import operator
import curses
import inspect

from pick import Picker


def back_pick(_options, prompt="Pick: ", indicator='=>'):
    """Instantiates a picker, registers custom handlers for
    going back, and starts the picker.
    """
    def go_back(picker):
        return None, -1

    picker = Picker(_options, title=prompt, indicator=indicator)
    picker.register_custom_handler(ord('h'), go_back)
    picker.register_custom_handler(curses.KEY_LEFT, go_back)
    return picker.start()


def back_pick_multiple(_options, prompt="Pick multiple: ",
                       indicator='=>', ALL="all", DONE="done..."):
    """Calls `pick` in a while loop to allow user to pick multiple
    options. Returns a list of chosen options.
    """
    _options, options = [ALL] + _options + [DONE], []
    while True:
        option, i = back_pick(_options, '{}{}'.format(prompt, options),
                              indicator=indicator)
        if i < 0: # user went back
            return options, i
        if option == ALL:
            return ([ALL], i)
        if option == DONE:
            return (options, i)
        options.append(option)
        _options.remove(option)


class Condition:
    """Container for condition properties.
    """
    _OPERATORS = {
        '==' : operator.eq,
        '!=' : operator.ne,
        '<=' : operator.le,
        '>=' : operator.ge,
        'in' : lambda x, y: x in y,
        'not in' : lambda x, y: x not in y
        }

    def get_operator(op):
        return Condition._OPERATORS[op] if op in Condition._OPERATORS else op

    def check_operator(op):
        if op in Condition._OPERATORS:
            return True
        try:
            n_args = len(inspect.getargspec(op)[0])
            return n_args == 2
        except:
            return False

    def __init__(self, condition):
        self._keys = condition['keys']
        self._vals = condition['vals']
        self._operators = condition['operators'] \
                          if 'operators' in condition \
                          else ['==']*len(self._keys)
        vars = [self._keys, self._vals, self._operators]

        assert all(type(var) == list for var in vars), \
            "All condition properties must be lists"
        assert all(len(var) == len(vars[0]) for var in vars), \
            "All condition properties must have the same length"
        assert all(Condition.check_operator(op) for op in self._operators), \
            "Condition has invalid operator(s)"

    def keys(self):
        return self._keys

    def vals(self):
        return self._vals

    def operators(self):
        return self._operators


class Question:
    """Container for question properties.
    """
    def __init__(self, key, options, multiple=False, condition={}):
        self._key = key
        self._options = options
        self._multiple = multiple
        self._condition = Condition(condition) \
                          if 'keys' in condition and 'vals' in condition \
                          else None

    def key(self):
        return self._key

    def options(self):
        return self._options

    def multiple(self):
        return self._multiple

    def condition(self):
        return self._condition


class Questionnaire:
    """Class with methods for adding questions to a questionnaire,
    and running the questionnaire.
    """
    def __init__(self):
        self.questions = OrderedDict() # key -> list of Question instances
        self.choices = OrderedDict() # key -> option(s)

    def show_choices(self, s=""):
        """Helper method for displaying the choices made so far.
        """
        padding = len(max(self.questions.keys(), key=len)) + 5
        for key in list(self.choices.keys()):
            s += "{:>{}} : {}\n".format(key, padding, self.choices[key])
        return s

    def go_back(self, n=1):
        """Move `n` questions back in the questionnaire, and remove
        the last `n` choices.
        """
        N = max(len(self.choices)-n-1, 0)
        self.choices = OrderedDict(islice(self.choices.items(), N))

    def prompt(self, key, options, prompt="", multiple=False, indicator='=>'):
        """Interactive prompt allowing user to choose option(s) from a list
        using the arrow keys to navigate.
        """
        prompt = prompt if prompt else "{}: ".format(key)
        _pick = back_pick_multiple if multiple else back_pick
        self.choices[key], i = \
            _pick(options, self.show_choices() + "\n{}".format(prompt),
                  indicator=indicator)
        if i < 0: # user went back
            if multiple:
                self.go_back(0) if self.choices[key] else self.go_back(1)
            else:
                self.go_back(1)
            return False
        return True

    def add_question(self, question):
        """Add a Question instance to the questions dict. Each key points
        to a list of Question instances with that key.
        """
        self.questions.setdefault(question.key(), []).append(question)

    def which_question(self, key):
        """Decide which Question instance to select from the list of questions
        corresponding to the key, based on condition. Returns first question
        for which condition is satisfied, or for which there is no condition.
        """
        questions = self.questions[key]
        for question in questions:
            if self.check_condition(question.condition()):
                return question
        return None

    def check_condition(self, condition):
        """Helper that returns True if condition is satisfied/doesn't exist.
        """
        if not condition:
            return True
        for key, val, op in \
            zip(condition.keys(), condition.vals(), condition.operators()):
            if not Condition.get_operator(op)(val, self.choices[key]):
                return False
        return True

    def run(self):
        """Prompt the user to choose one or more options for each question
        in the questionnaire, and return the choices.
        """
        self.choices = OrderedDict() # reset choices
        while True:
            if not self.ask_questions():
                continue
            return dict(self.choices)

    def ask_questions(self):
        """Helper that asks questions in questionnaire, and returns
        False if user "goes back".
        """
        for key in self.questions.keys():
            question = self.which_question(key)
            if question is not None and key not in self.choices:
                if not self.prompt(key, question.options(),
                        multiple=question.multiple()):
                    return False
        return True