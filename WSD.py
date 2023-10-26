import sys

class WSD:
    def __init__(self, file):
        self.__file = file
        #Has 5 keys for each fold numbered 1-5, each value is a tuple containing fold word count in index 0 and a sense dictionary in index 1.
        # The sense dictionary contains a key for each sense the word has been seen with. The values at each key is also a dictionary
        # containing a key called "count" storing the number of times the sense is seen and a key called "bag" with a value
        # of a string containing the bag of words data.

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
                    #mWord = line[line.rfind("<head>") + 6:line.rfind("</head>")]
                    if curSense in senseDict:
                        for word in line.split():
                            if "<head>" not in word and word not in senseDict[curSense]["bag"]:
                                senseDict[curSense]["bag"] += word + " "
                                #senseDict[curSense]["bag"] += line[:line.rfind("<head>")] + line[line.rfind("</head>")+7:]
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


    with open ("WSD.test.out", 'w') as outp:
        #outp.write("Fold: " + AI.folds[1][1]["plant%factory"]["bag"] + '\n')
        for key, value in AI.folds.items():
            outp.write("Fold: " + str(key) + '\n')
            count = value[0]
            for ke, val in value[1].items():
                outp.write("Key: " + ke + '\n' + " val: " + str(val) + '\n')
            outp.write("Total Count: " + str(count) + '\n')





if __name__ == '__main__':
    main()

