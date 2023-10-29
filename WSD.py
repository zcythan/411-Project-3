#System libraries
import sys
import math
import copy

class Fold:
    def __init__(self):
        self.__senses = {}  # Contains a dictionary with sense as a key and value of dict containing keys of count and bag.
        # Bag is a dict that has every word as a key and a dict value containing freq of word with tag.
        self.__count = 0
        self.__data = []  # list of dictionaries containing id, context, and head keys for each sentence. Used for test data.

    @property
    def getSen(self):
        return self.__senses

    @property
    def getData(self):
        return self.__data

    @property
    def getCount(self):
        return self.__count

    #Add data to a fold.
    def addInfo(self, sense, insId, context):
        if sense in self.__senses:
            self.__senses[sense]["count"] += 1
        else:
            self.__senses[sense] = {"count": 1, "bag": {}}
        # Update sense bag
        for word in context.split():
            if word == ".":
                continue
            if "<head>" not in word and word not in self.__senses[sense]["bag"]:
                self.__senses[sense]["bag"][word] = 1
            elif "<head>" not in word and word in self.__senses[sense]["bag"]:
                self.__senses[sense]["bag"][word] += 1
        # Update data used in testing
        self.__data.append({"id": insId, "head": context[context.rfind("<head>") + 6:context.rfind("</head>")], "cont": context})
        self.__count += 1

class WSD:
    def __init__(self, file):
        self.__file = file
        self.__folds = self.__buildFolds()

    #For combining the data of multiple fold objects.
    def __combineSets(self, index):
        combSens = {}
        combCount = 0
        for i in range(len(self.__folds)):
            if i == index:
                continue
            for sense in self.__folds[i].getSen:
                if sense in combSens:
                    combSens[sense]["count"] += self.__folds[i].getSen[sense]["count"]
                    for word in self.__folds[i].getSen[sense]["bag"]:
                        if word in combSens[sense]["bag"]:
                            combSens[sense]["bag"][word] += self.__folds[i].getSen[sense]["bag"][word]
                        else:
                            combSens[sense]["bag"][word] = self.__folds[i].getSen[sense]["bag"][word]
                else:
                    # was getting shallow copied by default
                    combSens[sense] = {"count": self.__folds[i].getSen[sense]["count"], "bag": copy.deepcopy(self.__folds[i].getSen[sense]["bag"])}
        for sense in combSens:
            combCount += combSens[sense]["count"]

        #dictionary with all combined data, occurrence count of all senses in combined data.
        return combSens, combCount

    @staticmethod
    def __getProbs(countSens):
        featCounts = {}
        probSens = copy.deepcopy(countSens)
        # stores every word used in the bag of all senses once. No duplicates.
        bagWords = {}
        for sense in countSens:
            for word in countSens[sense]["bag"]:
                if word not in bagWords:
                    bagWords[word] = 1
        # number of these is v
        v = len(bagWords)

        #Make dictionary storing P(Fn|S) values instead of counts.
        for sense in countSens:
            for word in countSens[sense]["bag"]:
                #P(Fn|S) = frequency of word in bag for sense + 1 / frequency of sense + v
                #Derived from c(Wi-1, Wi)+1/c(Wi-1)+v for bigram la place and the logic shown on the Naive Bayes example slides.
                probSens[sense]["bag"][word] = ((countSens[sense]["bag"][word]+1)/(countSens[sense]["count"]+v))  # Smoothed

        return probSens, v

    def predict(self):
        with open(self.__folds[0].getData[0]["head"] + ".wsd.out", 'w') as outp:  # Probably the most complicated way I could have done this.
            for i in range(len(self.__folds)):
                outp.write("Fold " + str(i+1) + '\n')
                #getData is a list of dicts, it only contains the context, id and head word. The sense is NOT included here.
                testSet = self.__folds[i].getData
                combSens, senseCount = self.__combineSets(i)  # Combine all data from current training folds (all folds but i)
                #print("Current fold " + str(i+1))
                combSens, v = self.__getProbs(combSens)  # get the smoothed probabilities for each feature given sense.
                #Naive Bayes Implementation in log space.
                for item in testSet:
                    probs = {}
                    # doing P(S) for all first
                    for sense in combSens:
                        #Since every occurrence of word is tagged with sense, senseCount = word count.
                        probs[sense] = math.log(combSens[sense]["count"] / senseCount)
                    #See if test set word was observed, else smooth 0.
                    for testWord in item["cont"].split():
                        if "<head>" not in testWord:
                            for sense in combSens:
                                if testWord in combSens[sense]["bag"]:
                                    probs[sense] += math.log(combSens[sense]["bag"][testWord])  # add because log space
                                else:
                                    if testWord == ".":
                                        continue
                                    probs[sense] += math.log(1 / (combSens[sense]["count"] + v))  # same

                    outp.write(item["id"] + " " + max(probs, key=probs.get) + '\n')  # Grab key with max value as the best tag.

    def __buildFolds(self):
        with open(self.__file, 'r') as data:
            size = math.ceil(data.read().count("</instance>")/5)
            folds = [Fold(), Fold(), Fold(), Fold(), Fold()]
            curSense = ""
            curId = ""
            curCont = ""
            index = 0
            data.seek(0)
            for line in data:
                if "</instance>" in line:
                    folds[index].addInfo(curSense, curId, curCont)
                    if folds[index].getCount >= size and index < 4:
                        index += 1
                    curSense = ""
                    curId = ""
                    curCont = ""

                if "<instance id=" in line:
                    curId = line[line.rfind("<instance id=") + 14:line.rfind("\" d")]
                if "senseid=" in line:
                    curSense = line[line.rfind("senseid=") + 9:line.rfind('/') - 1]
                if "<head>" in line:
                    curCont = line.replace('\n', '')
        return folds

    def getAccuracy(self):
        correct = 0
        wrong = 0
        curFold = 1
        offset = 0
        accs = []
        with open(self.__file, 'r') as orig:
            with open(self.__folds[0].getData[0]["head"] + ".wsd.out", 'r') as pred:
                origLines = orig.readlines()
                for line in pred:
                    if ("Fold " + str(curFold)) in line:
                        if correct > 0 or wrong > 0:
                            accs.append(round((correct / (correct + wrong)) * 100, 2))
                            correct = 0
                            wrong = 0
                        curFold += 1
                        continue
                    testIds = line.split()
                    trainId = ""
                    trainSen = ""
                    while "</instance>" not in origLines[offset]:
                        if "<instance id=" in origLines[offset]:
                            trainId = origLines[offset][origLines[offset].rfind("<instance id=") + 14:origLines[offset].rfind("\" d")]
                        if "senseid=" in origLines[offset]:
                            trainSen = origLines[offset][origLines[offset].rfind("senseid=") + 9:origLines[offset].rfind('/') - 1]
                        if (offset + 1) < len(origLines):
                            offset += 1
                        else:
                            break

                    while "<instance id=" not in origLines[offset]:
                        if (offset+1) < len(origLines):
                            offset += 1
                        else:
                            break
                    if testIds[0] == trainId and testIds[1] == trainSen:
                        correct += 1
                    else:
                        wrong += 1

        if correct > 0 or wrong > 0:
            accs.append(round((correct / (correct + wrong)) * 100, 2))
        return accs

def main():
    if len(sys.argv) < 2:
        print("Too few input arguments")
        return
    AI = WSD(sys.argv[1])
    AI.predict()
    accs = AI.getAccuracy()
    for i in range(len(accs)):
        print("Fold " + str(i+1) + ": " + str(accs[i]))
    print("Average: " + format(sum(accs)/len(accs), '.2f'))


if __name__ == '__main__':
    main()

