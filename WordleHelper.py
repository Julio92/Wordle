from os import system               # Just for clearing console.
import re                           # Regular expressions
import unicodedata                  # Deleting accents from the dictionary
from itertools import permutations  # Permutations for yellow letters
from typing import List, Pattern    # For typing variables

class View(object):
    """
    View class. Responsible of the console output.
    """
    @staticmethod
    def showDictionary(dictionary:List) -> None:
        if len(dictionary) > 0:
            print("\nCurrent dictionary:")
            for word in dictionary:
                print(f"    * {word}")
            return
        
        print("\nThe dictionary is empty")

    @staticmethod
    def showLastAttemp(lastAttemp:str) -> None:
        print(f"\nLast attemp: {lastAttemp.upper()}.")

    @staticmethod
    def welcomeMessage() -> None:
        system('cls')
        print(f"\n\t\t... Initiating game ...\n\n")

class Model(object):
    """
    Model class. Responsible for filtering the dictionary from the user input.
    """
    yellowLetters : List = [] # It will include all yellow letters found during the game.
    greyLetters   : List = [] # It will include all grey letters found during the game.
    dictionary    : List = [] # Our dictionary.

    regularExpressionGreyLetters    : Pattern[str] = re.compile('') # This Reg. Expr. will delete all words containing any of the grey letters.       
    regularExpressionYellowLetters  : Pattern[str] = re.compile('') # This Reg. Expr. will delete all words not containing all the yellow letters. 
    regularExpressionLastAttemp     : Pattern[str] = re.compile('') # This Reg. Expr. will find possible matches. 

    # Each position of the word is defined with a dictionary {}. 
    word = [ {'green': [], 'yellow': [], 'grey': [], 'history':[]},
             {'green': [], 'yellow': [], 'grey': [], 'history':[]},
             {'green': [], 'yellow': [], 'grey': [], 'history':[]},
             {'green': [], 'yellow': [], 'grey': [], 'history':[]},
             {'green': [], 'yellow': [], 'grey': [], 'history':[]}
           ]

    def addLetterGreen(self, position, letter) -> None:
        self.word[position]['green'].append(letter)
        self.word[position]['yellow'] = []

    def addLetterYellow(self, position, letter) -> None:
        self.word[position]['yellow'].append(letter)

    def addLetterGrey(self, position, letter) -> None:
        self.word[position]['grey'].append(letter)

    def addLetter(self, position, color, letter) -> None:
        self.word[position][color].append(letter)
        # Save the word in history, independant of its color, so you know the word of each turn. 
        self.word[position]['history'].append(letter)

    def getLastAttemp(self) -> str:
        lastAttemp : str = ''
        for position in self.word:
            lastAttemp += position['history'].pop()
        return lastAttemp

    def updateYellowLetters(self) -> None:
        # In each turn, the yellow letters can be different. It has to be updated accordingly.
        self.yellowLetters = []
        for position in self.word:
            if position['yellow']:
                self.yellowLetters += position['yellow']

        # Remove duplicates
        self.yellowLetters = list(dict.fromkeys(self.yellowLetters))
    
    def addGreyLetters(self) -> None:
        # Grey letters are added to the list in each turn.
        self.greyLetters = []
        for position in self.word:
            if position['grey']:
                self.greyLetters += position['grey']

        # Remove duplicates
        self.greyLetters = list(dict.fromkeys(self.greyLetters))

    def setLastAttemp(self, attemp) -> None:
        # Update with the last word used in the game.
        self.last_attemp = attemp

    def updateRegularExpressions(self) -> None:
        self.updateREGreyLetters()
        self.updateREYellowLetters()
        self.updateRELastAttemp()

    def updateREGreyLetters(self) -> None:
        if len(self.greyLetters) > 0:
            self.regularExpressionGreyLetters = re.compile(f'[{"".join(sorted(set(self.greyLetters)))}]')

    def updateREYellowLetters(self) -> None:
        """
        Update the regular expression for the yellow letters.
        """
        regularExpression : str = r''
        
        if len(self.yellowLetters) < 1:
            return

        # Get all possible combinations (permutations) of the yellow letters (using list comprehension).
        # For example:
        #   - 'a' and 'b':      ab & ba
        #   - 'a', 'b' and 'c': abc & acb & bac & bca & cab & cba 
        # It returns a list of lists with all the permutations: [['a','b','c']['b','a','c'],...]
        permutations_list = [ list(combinacion) for combinacion in permutations(self.yellowLetters, len(self.yellowLetters)) ]
        
        for permutation in permutations_list:
            regularExpression += '(\w*)'
            for word in permutation:
                regularExpression += f'({word}\w*)'
            regularExpression +=  '|'

        self.regularExpressionYellowLetters = re.compile(regularExpression[:-1]) # Deletes the last "|".

    def updateRELastAttemp(self) -> None:
        """
        This method builds the regular expression for the last attemp.
        """
        regularExpression : str = r""

        for letter in self.word:            
            if letter['green']:
                # If the position is green, just add the letter to the RE and jump to next position. 
                regularExpression += f"{letter['green'].pop()}"
                continue
            # At this point, the position is grey or yellow. Add the yellow letters of the current position, and ALL the grey letters to the RE.
            regularExpression += f"[^{''.join([item for item in letter['yellow']])}{''.join([item for item in self.greyLetters])}]"
        
        self.regularExpressionLastAttemp = re.compile(regularExpression)

    def applyRegularExpressions(self) -> None:
        # Delete words containing a grey letter.
        if self.regularExpressionGreyLetters.pattern != '':
            self.dictionary = [ word for word in self.dictionary if not re.search(self.regularExpressionGreyLetters, word) ]

        # Delete words without all yellow letters.
        self.dictionary = list(filter(self.regularExpressionYellowLetters.search, self.dictionary))

        # Delete words that doesn't match the last attemp
        self.dictionary = list(filter(self.regularExpressionLastAttemp.match, self.dictionary))

    def updateDictionary(self) -> None:
        self.applyRegularExpressions()

    def getDictionary(self) -> List[str]:
        return self.dictionary

    def setDictionary(self, dictionary) -> None:
        self.dictionary = dictionary

class Controller(object):
    """
    Responsible for loading dictionary, get user input and send it to model class.
    """
    view = View()
    model = Model()

    def __init__(self, dictionaryPath = '', dictionary = [], word_length = 0, success = False):
        self.dictionaryPath = dictionaryPath
        self.dictionary = dictionary
        self.word_length = word_length
        self.success = success
        self.loadDictionary()
        self.model.setDictionary(self.dictionary)

    def getWords(self, words_list) -> List[str]:
        return [word for word in words_list if len(word) == self.word_length]

    def loadDictionary(self) -> None:
        dictionaryFile = open(self.dictionaryPath, "r")
        # Load the dictionary.
        for word in self.getWords( dictionaryFile.read().splitlines() ):
            # Delete the accents and extrange characters and stores in dictionary member.
            unicode_word = unicodedata.normalize("NFD", word).encode('ascii', 'ignore').decode('utf-8')
            self.dictionary.append(unicode_word)

    def readLetter(self) -> str:        
        while True:
            letter = input("Enter the letter: ").lower()
            
            if not letter.isalpha():
                print("Enter a correct letter. ")
                continue

            if len(letter) > 1:
                print("Enter a single letter")
                continue
            
            return letter

    def readColor(self, position: int) -> str:
        while True:
            match input(f"Enter the letter {position + 1} color (Grey/Yellow/Green): ").lower():
                case 'green':
                    return 'green'
                case 'yellow':
                    return 'yellow'
                case 'grey':
                    return 'grey'
                case _:             
                    print("The chosen color it's not correct. Try again. ")                  

    def getUserInput(self) -> None:
        input_letter = 0
        while input_letter < 5:            
            self.model.addLetter(input_letter, self.readColor(input_letter), self.readLetter())
            input_letter += 1    

        self.model.addGreyLetters() 
        self.model.updateYellowLetters()

    def updateDictionary(self) -> None:
        self.model.updateRegularExpressions()
        self.model.applyRegularExpressions()
        self.dictionary = self.model.getDictionary()

    def showLasAttemp(self) -> None:
        self.view.showLastAttemp(self.model.getLastAttemp())

    def showDictionary(self) -> None:
        self.view.showDictionary(self.dictionary)

    def askUserIfSuccess(self) -> None:
        self.success = input("\nHave you won? (Y/N)").lower() == 'y'

    def printWelcomeMessage(self) -> None:
        self.view.welcomeMessage()

def main() -> None:

    controller = Controller(dictionaryPath = r"", word_length = 5)
    controller.printWelcomeMessage()

    while (not controller.success) and len(controller.dictionary) > 0:
        controller.getUserInput()
        controller.showLasAttemp()
        controller.updateDictionary()
        controller.showDictionary()
        controller.askUserIfSuccess()

main()