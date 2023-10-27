import sys
import math

class Fold:
    def __init__(self):
        self.__senses = {}  # Contains a dictionary with sense as a key and value of dict containing keys of count and bag.
        #Bag is a dict that has every word as a key and a dict value containing freq of word with tag and probability.
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
                self.__senses[sense]["bag"][word] = {"count": 1, "prob": -1}
            elif "<head>" not in word and word in self.__senses[sense]["bag"]:
                self.__senses[sense]["bag"][word]["count"] += 1
        # Update data used in testing
        self.__data.append({"id": insId, "head": context[context.rfind("<head>") + 6:context.rfind("</head>")], "cont": context})
        self.__count += 1


class WSD:
    def __init__(self, file):
        self.__file = file
        self.folds = self.__buildFolds()

    #def predict(self):
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

    with open("WSD.test.out", 'w') as outp:
        for data in AI.folds[0].getData:
            outp.write(str(data) + '\n')


if __name__ == '__main__':
    main()

