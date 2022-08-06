from optparse import OptionParser
import pandas as pd
import csv

class SpeedTestCsvData:
    def __init__(self, options):
        self.df = None
        self.options = options
        self.providers = ['wakwak', 'plala', 'sonet', 'asahi', 'ocn', 'wakwak-ipoe']

    def load(self, file):   
        df = pd.read_csv(file, parse_dates=[1],
        date_parser=lambda date: pd.to_datetime(date, format='%Y/%m/%dT%H:%M'))
        #df = df.drop(df.columns[0], axis=1)
        #df.set_index('timestamp', inplace = False)

        for column in self.providers:
            df[column + '(Download)'] = df[column + '(Download)'].astype('float')
            df[column + '(Upload)'] = df[column + '(Upload)'].astype('float')
        
        self.df = df

    def getData(self, provider):
        pdf = self.df[['timestamp', provider + '(Download)',provider + '(Upload)']]
        print(pdf.describe())
        pdf = pdf.rename(columns={
                provider + '(Download)': 'download.bandwidth',
                provider + '(Upload)': 'upload.bandwidth',
                })
        pdf['download.bandwidth'] = pdf['download.bandwidth'].map(lambda x: x * 1024 *1024)
        pdf['upload.bandwidth'] = pdf['upload.bandwidth'].map(lambda x: x * 1024 *1024)
        pdf['timestamp'] = pdf['timestamp'].map(lambda x:x.strftime("%Y-%m-%d %H:%M:%S+9:00"))
        # print(pdf['timestamp'])
        # print(pdf.describe())
        return SpeedTestData(pdf, provider, self.options)

    def dump(self):
        print(self.df.describe())
        print(self.df.dtypes)

class SpeedTestData:
    def __init__(self, df, provider, options):
        self.df = df
        self.provider = provider
        self.options = options
    
    def toJson(self):
        return self.df.to_json(orient='records',lines=True)
    
    def dump(self):
        print(self.df.describe())
        

def main():
    # parse options
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      default=False, help="verbose mode")
    (options, args) = parser.parse_args()
    
    if (len(args)!= 1):
        parser.print_usage()
    else:
        csv = SpeedTestCsvData(options)
        csv.load(args[0])
        csv.dump()
        for provider in ['wakwak', 'plala', 'sonet', 'asahi', 'ocn', 'wakwak-ipoe',]:
            print('Extracting', provider)
            data = csv.getData(provider)
            #data.dump()
            print('Writing ', provider + ".jsonl")
            with open(provider + ".jsonl", mode='w') as f:
                f.write(data.toJson())
    
if __name__ == "__main__":
    main()