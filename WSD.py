import sys

class WSD:
    def __init__(self, file):
        self.__file = file
        #Has 5 keys for each fold, each value is a tuple containing word count in index 0 and
        # a dictionary containing a key of the sense and a value of the count in index 1.
        self.folds = self.__buildFolds()

    def __buildFolds(self):
        with open(self.__file, 'r') as file:
            data = file.readlines()
            size = len(data)/5
            folds = {}
            senseDict = {}
            wCount = 0
            fCount = 1
            fid = 1
            curSense = ""

            for line in data:
                if fCount > size:
                    folds[fid] = (wCount, senseDict)
                    fCount = 1
                    fid += 1
                    wCount = 0
                    senseDict = {}

                if "senseid=" in line:
                    curSense = line[line.rfind("senseid=")+9:line.rfind('/')-1]
                    if curSense in senseDict:
                        senseDict[curSense]["count"] += 1
                    else:
                        senseDict[curSense] = {"count": 1, "bag": ""}
                if "<head>" in line:
                    if curSense in senseDict:
                        senseDict[curSense]["bag"] += line[:line.rfind("<head>")] + line[line.rfind("</head>")+7:]
                    wCount += 1

                fCount += 1

                #Use if multiple words ever occur/we need a reference to the word in a training set.
                '''
                if "<head>" in line:
                    curHead = line[line.rfind("<head>")+6:line.rfind("</head>")]
                    if curHead in countDict:
                        countDict[curHead] += 1
                    else:
                        countDict[curHead] = 1
                '''
        return folds


def main():
    if len(sys.argv) < 2:
        print("Too few input arguments")
        return
    AI = WSD(sys.argv[1])

    for key, value in AI.folds.items():
        print("Fold: " + str(key))
        count = value[0]
        for ke, val in value[1].items():
            print("Key: " + ke + " val: " + str(val))
        print("Total Count: " + str(count))
        print()


if __name__ == '__main__':
    main()

