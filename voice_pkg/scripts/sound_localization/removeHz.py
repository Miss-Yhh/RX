'''采样降噪'''
from collections import Counter
# import librosa


def test2(n, y, sr):
 
    indexs = librosa.effects.split(y, top_db=25-n)
 
    noicefrequencies = []
    for i in indexs:
        frequencies, D = librosa.ifgram(y[i[0]:i[1]], sr=sr, n_fft=22000)
        frequencies = frequencies.astype(int)
        noicefrequencies += frequencies.flatten().tolist()
    
    c = Counter(noicefrequencies)
    noicefrequencies = set(map(lambda x: x[0] // 2 * 2, c.most_common(400)))
 
    frequencies, D = librosa.ifgram(y, sr=sr)
 
 
    tempD = D.copy().astype(int)
    tempD = tempD // 2 * 2
 
    count = 0
    for i in range(D.shape[0]):
        for j in range(D.shape[1]):
            if tempD[i][j] in noicefrequencies:
                count += 1
                D[i][j] = 0
    print(count)
    return librosa.istft(D)