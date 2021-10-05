import pandas as pd

def main():
    df = pd.read_csv('./data/experiment_0/resulaj_0.csv')
    print('Size of data =', df.shape)
    X1 = df[['Unnamed: 1']]
    data = X1[1:2]
    print(data.iloc[0])

if __name__=='__main__':
    main()