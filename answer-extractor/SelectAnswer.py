import math
import re
import json
import time
import jieba.posseg as pseg

def score(question, evidence, candidateAnswer):

    #weights of various scores
    TermDistanceScoreWeight = 0.5
    MiniTermDistanceScoreWeight = 1.0
    TermFrequencyScoreWeight = 0.5
    TextualAlignmentScoreWeight = 2.0

    #SCORE using term distance
    TermDistanceScore = 0.0

    #first, check if words in evidence appear in question
    evidenceFlag = []
    for i in range(len(evidence)):

        evidenceFlag.append(list())
        for j in range(len(evidence[i])):
            if evidence[i][j] in question:
                evidenceFlag[i].append(1)
            else:
                evidenceFlag[i].append(0)

    #second, calculate the distance between candidate answer and question terms in evidence
    #score = sum(1.0 / term distance)
    for i in range(len(evidence)):
        for j in range(len(evidence[i])):
            if evidence[i][j] == candidateAnswer:
                for k in range(len(evidence[i])):
                    if evidenceFlag[i][k] == 1:
                        TermDistanceScore += 1.0 / math.fabs(k - j)

    TermDistanceScore *= TermDistanceScoreWeight


    #SCORE using mini term distance
    MiniTermDistanceScore = 0.0

    #calculate the distance between candidate answer and question terms in evidence
    #score = sum(1.0 / minimum term distance)
    for i in range(len(evidence)):

        miniDistance = 10000.0
        for j in range(len(evidence[i])):
            if evidence[i][j] == candidateAnswer:
                for k in range(len(evidence[i])):
                    if evidenceFlag[i][k] == 1 and math.fabs(k - j) < miniDistance:
                        miniDistance = math.fabs(k - j)

        MiniTermDistanceScore += 1.0 / miniDistance

    MiniTermDistanceScore *= MiniTermDistanceScoreWeight


    #SCORE using term frequency
    TermFrequencyScore = 0.0

    #count the frequency of candidate answer
    for i in range(len(evidence)):
        if candidateAnswer in evidence[i]:
            TermFrequencyScore += 1

    TermFrequencyScore *= TermFrequencyScoreWeight


    #SCORE using textual alignment
    TextualAlignmentScore = 0.0

    #first, generate candidate pattern
    candidateAlignmentPattern = []

    for i in range(len(question) + 1):
        candidateAlignmentPattern.append(list())

        answerAdded = 0
        for j in range(len(question) + 1):
            if i == j:
                candidateAlignmentPattern[i].append(candidateAnswer)
                answerAdded = 1
            else:
                candidateAlignmentPattern[i].append(question[j - answerAdded])

    candidateAlignmentRegPattern = []

    #second, translate the patterns into regular expressions
    for i in range(len(candidateAlignmentPattern)):
        regPattern = ''

        for j in range(len(candidateAlignmentPattern[i])):
            if len(set(candidateAlignmentPattern[i][j]).intersection(set('. $ ^ { [ ( | ) * + ?\\'))) == 0:
                regPattern += '' + candidateAlignmentPattern[i][j] + '' + '.*'

        candidateAlignmentRegPattern.append(regPattern)

    matchCounter = 0

    for p in candidateAlignmentRegPattern:
        compiledPattern = re.compile(p)

        for e in evidence:
            evidenceSentence = ''.join(e)
            matcher = compiledPattern.match(evidenceSentence)

            if matcher:
                TextualAlignmentScore += len(''.join(question) + candidateAnswer) / float(len(matcher.group()))
                matchCounter += 1


    if matchCounter > 0:
        TextualAlignmentScore /= matchCounter

    TextualAlignmentScore *= TextualAlignmentScoreWeight

    return [TermDistanceScore, MiniTermDistanceScore, TermFrequencyScore, TextualAlignmentScore, TermDistanceScore + MiniTermDistanceScore + TermFrequencyScore + TextualAlignmentScore]

queryf = open('test-query.json')
contextf = open('relevant_sentence.txt')
answerf = open('answer.txt', 'w')

contextf.readline()

for line in queryf:
    startTime = time.time()
    query = json.loads(line.strip())

    #find out question type
    questionType = set()
    lat = set()

    if len(query['lat']) > 0:
        for type in query['lat']:
            lat.add(type[0])

        for type in lat:
            if type == 'WHICH' or type == 'WHAT' or type == 'LIST':
                questionType.update(['n', 'nr', 'ns', 'nt', 'nz', 't'])
            elif type == 'WHO':
                questionType.update(['nr'])
            elif type == 'WHEN':
                questionType.update(['m', 't'])
            elif type == 'WHERE':
                questionType.update(['ns'])
            elif type == 'HOWMANY' or type == 'HOWMUCH' or type == 'RANK':
                questionType.update(['m'])
            elif type == 'YES/NO':
                pass

    else:
        questionType.update(['n', 'nr', 'ns', 'nt', 'nz', 't'])

    evidence = []
    candidateAnswers = []
    question = []

    for i in range(1):
        oneLine = contextf.readline().strip()
        words = oneLine.split(' ')

        for w in words:
            if '/' in w:
                wordAndPOS = w.split('/')
                POS = wordAndPOS[-1]
                word = ''.join(wordAndPOS[:-1])

                if word != '' and POS != 'x' and POS != 'r':
                    question.append(word)

    while 1:
        oneLine = contextf.readline().strip()

        if oneLine.find('#qID') == -1 and oneLine != '':
            evidence.append(list())

            words = oneLine.split(' ')

            for w in words:
                if '/' in w:
                    wordAndPOS = w.split('/')
                    POS = wordAndPOS[-1]
                    word = ''.join(wordAndPOS[:-1])

                    if word != '':
                        evidence[i].append(word)

                        if POS in questionType and word not in question:
                            candidateAnswers.append(word)
        else:
            break

    maxScore = [0,0,0,0,0]
    bestAnswer = ''
    for answer in candidateAnswers:
        currentScore = score(question, evidence, answer)

        if currentScore[4] > maxScore[4]:
            maxScore = currentScore
            bestAnswer = answer

    print bestAnswer, currentScore, time.time() - startTime

    answerf.write(bestAnswer + '\n')


queryf.close()
contextf.close()
answerf.close()