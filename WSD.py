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
        self.folds = self.__buildFolds()  # MAKE PRIVATE

    def __combineSets(self, index):
        combSens = {}
        combCount = 0
        for i in range(len(self.folds)):
            if i == index:
                continue
            for sense in self.folds[i].getSen:
                if sense in combSens:
                    combSens[sense]["count"] += self.folds[i].getSen[sense]["count"]
                    for word in self.folds[i].getSen[sense]["bag"]:
                        if word in combSens[sense]["bag"]:
                            combSens[sense]["bag"][word] += self.folds[i].getSen[sense]["bag"][word]
                        else:
                            combSens[sense]["bag"][word] = self.folds[i].getSen[sense]["bag"][word]
                else:
                    combSens[sense] = {"count": self.folds[i].getSen[sense]["count"], "bag": copy.deepcopy(self.folds[i].getSen[sense]["bag"])}  # was getting shallow copied by default
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
        for sense in countSens:
            for word in countSens[sense]["bag"]:
                probSens[sense]["bag"][word] = ((countSens[sense]["bag"][word]+1)/(featCounts[sense]+v))  # Smoothed

        return probSens, v

    def predict(self):
        with open("WSD.test.out", 'w') as outp:
            for i in range(len(self.folds)):
                outp.write("Fold " + str(i+1) + '\n')
                testSet = self.folds[i].getData
                combSens, senseCount= self.__combineSets(i)
                combSens, v = self.__getProbs(combSens)  # set equal to function call to getProbs function that replaces all counts with probabilities.
                #Naive Bayes Implementation
                for item in testSet:
                    prob = 1
                    probs = {}
                    for testWord in item["cont"].split():  # For a context in test set
                        if "<head>" not in testWord:
                            for sense in combSens:
                                if testWord in combSens[sense]["bag"]:
                                    prob *= combSens[sense]["bag"][testWord]
                                else:
                                    prob *= (1/v)
                                probs[sense] = prob
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
                    curId = line[line.rfind("<answer instance=") + 15:line.rfind("\" d")]
                if "senseid=" in line:
                    curSense = line[line.rfind("senseid=") + 9:line.rfind('/') - 1]
                if "<head>" in line:
                    curCont = line.replace('\n', '')
        return folds


def main():
    if len(sys.argv) < 2:
        print("Too few input arguments")
        return
    AI = WSD(sys.argv[1])
    AI.predict()

    #with open("WSD.test.out", 'w') as outp:
        #for key, val in AI.predict().items():
           # outp.write("key: " + key + '\n')
           # outp.write(str(val) + '\n')



if __name__ == '__main__':
    main()

