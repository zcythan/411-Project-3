#System libraries
import sys
import math
import copy

class Fold:
    def __init__(self):
        self.__senses = {}  # Contains a dictionary with sense as a key and value of dict containing keys of count and bag.
        # Bag is a dict that has every word as a key and a dict value containing freq of word with tag.
        self.__count = 0
        self.__data = []  # list of dictionaries containing id, context, and head keys for each sentence.

    @property
    def getSen(self):
        return self.__senses

    @property
    def getData(self):
        return self.__data

    @property
    def getCount(self):
        return self.__count

    def addInfo(self, sense, insId, context):
        if sense in self.__senses:
            self.__senses[sense]["count"] += 1
        else:
            self.__senses[sense] = {"count": 1, "bag": {}}
        # Update sense bag
        for word in context.split():
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
        self.__folds = self.__buildFolds()  # MAKE PRIVATE

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
                    combSens[sense] = {"count": self.__folds[i].getSen[sense]["count"], "bag": copy.deepcopy(self.__folds[i].getSen[sense]["bag"])}  # was getting shallow copied by default
        for sense in combSens:
            combCount += combSens[sense]["count"]

        return combSens, combCount

    @staticmethod
    def __getProbs(countSens):
        featCounts = {}
        probSens = copy.deepcopy(countSens)
        for sense in countSens:
            if sense in featCounts:
                featCounts[sense] += sum(countSens[sense]["bag"].values())
            else:
                featCounts[sense] = sum(countSens[sense]["bag"].values())
        v = sum(featCounts.values())
        #V is the total number of all features across all senses
        for sense in countSens:
            for word in countSens[sense]["bag"]:
                probSens[sense]["bag"][word] = ((countSens[sense]["bag"][word]+1)/(featCounts[sense]+v))  # Smoothed

        return probSens, v

    def predict(self):
        with open("WSD.test.out", 'w') as outp:
            for i in range(len(self.__folds)):
                outp.write("Fold " + str(i+1) + '\n')
                testSet = self.__folds[i].getData
                combSens, senseCount = self.__combineSets(i)
                combSens, v = self.__getProbs(combSens)  # set equal to function call to getProbs function that replaces all counts with probabilities.
                #Naive Bayes Implementation
                for item in testSet:
                    prob = 1
                    probs = {}
                    for testWord in item["cont"].split():  # For a context in test set
                        if "<head>" not in testWord:
                            for sense in combSens:  # Log space to avoid underflow as per instructions.
                                if testWord in combSens[sense]["bag"]:
                                    prob *= math.log(combSens[sense]["bag"][testWord])
                                else:
                                    prob *= (1/v)
                                probs[sense] = math.exp(prob * (combSens[sense]["count"]/senseCount))
                                prob = 1

                    outp.write(item["id"] + " " + max(probs, key=probs.get) + '\n')

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
            with open("WSD.test.out", 'r') as pred:
                origLines = orig.readlines()
                for line in pred:
                    if ("Fold " + str(curFold)) in line:
                        if correct > 0 and wrong > 0:
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
                    print("Train ID: " + trainId)
                    print("Train Sense: " + trainSen)
                    print("Test ID: " + testIds[0])
                    print("Test Sense: " + testIds[1])
                    if testIds[0] == trainId and testIds[1] == trainSen:
                        correct += 1
                    else:
                        wrong += 1

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

