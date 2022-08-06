#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
from pandas import json_normalize
import json
from pytz import timezone
import pytz
from dateutil import parser
import dateutil.tz
from optparse import OptionParser


graph_property = {
    'download.bandwidth': {
        'title':'Download Speed',
        'unit':'Mbps',
   #     'lines':{'fps':30, 'movie':25, 'video conference':15,'mail':10}
        },
    'upload.bandwidth': {
        'title':'Upload Speed',
        'unit':'Mbps',
  #      'lines':{'video conference':15}
        },
    'ping.latency': {
        'title': 'Ping',
        'unit':'ms',
     #   'lines':{'fps':50}
        },
    'ping.jitter': {
        'title': 'Jitter',
        'unit':'ms',
    #    'lines':{'fps':10}
        },
    'packetLoss': {
        'title':'PacketLoss',
        'unit':'%',
    #    'lines':{'fps':2}
        },
}

class SpeedTestData:
    def __init__(self, file, options):
        self.file = file
        self.df = self.load(file, options)
        self.label = 'Unknown'
        self.origin = self.get_origin()

        if not self.df.empty:
            self.label = file # 'isp=' + self.df['isp'][0]
            
    @staticmethod 
    def bps_to_mbps(bit):
        # bps (bit per second) -> Mbps (mega) 
        return bit / (1024 * 1024)
        
    def load(self, file, options):
        with open(file) as f:
            lines = f.readlines()
        df = pd.json_normalize(json.loads('['+ ','.join(lines) + ']'))
        # bps -> Mbps
        df['download.bandwidth'] = df['download.bandwidth'].map(lambda x: x / (1024 * 1024))
        df['upload.bandwidth'] = df['upload.bandwidth'].map(lambda x: x / (1024 * 1024))
        # convert string to TimeStamp in local time
        df['timestamp'] = pd.to_datetime(df['timestamp']).map(lambda x: x.tz_convert(dateutil.tz.tzlocal()))
        df.set_index('timestamp', drop=False)
        if options.verbose:
            print(df['isp'])
            print(df['server.host'])
        return df

    def get_origin(self):
        for t in self.df['timestamp']:
            if (t.dayofweek == 2 and t.hour == 1):
                return t
        return None

    def dump(self):
        print("file name: " + self.file)
        # print(self.df.dtypes)
        print(self.df.describe(exclude=['O'],datetime_is_numeric=True))

        
class SpeedTestGraph:
    axes_props = {
        'download': {
            'layout': 110, 
            'figs': {'download.bandwidth'}
            },
        'upload': {
            'layout': 110, 
            'figs': {'upload.bandwidth'}
            },
        'ping': {
            'layout': 110,
             'figs': {'ping.latency'}
             },
        'jitter': {
            'layout': 110, 
            'figs': {'ping.jitter'}
            },
        'packetloss': {
            'layout': 110, 
            'figs': {'packetLoss'}
            },

        # simple: Only Download / Upload speed (2x1 graph)
        'simple': {
            'layout': 210, 
            'figs': {'download.bandwidth', 'upload.bandwidth'}
        },
        # all: Download / Upload speed / Latency / Jitter / Packet Loss (3 x 2 graph)
        'all': {
            'layout': 320, 
            'figs': graph_property.keys()
        },
    }
    
    def __init__(self, options):
        self.all_in_one = options.all_in_one
        self.options = options
        self.title = 'SpeedTest'
        self.props = SpeedTestGraph.axes_props[options.profile]
        self.fig = {}
        self.ax = {}

        index = 0  
        for key in graph_property.keys():
                if key in self.props['figs']:
                    if self.all_in_one:
                        if not 'all' in self.fig:
                            self.fig['all'] = plt.figure(options.title)
                        index += 1
                        self.ax[key] = self.fig['all'].add_subplot(self.props['layout'] + index)
                    else:
                        self.fig[key] = plt.figure(options.title + '(' + key  + ')')
                        self.ax[key] = self.fig[key].add_subplot(111)
                    self.ax[key].set_title(graph_property[key]['title'])
                    self.ax[key].set_ylabel(graph_property[key]['unit'])
                   
                    if not 'lines' in graph_property[key].keys():
                        continue

                    for label in graph_property[key]['lines'].keys():
                        self.ax[key].axhline(y=graph_property[key]['lines'][label], color='blue', ls='dashed', label=label)
        return
                
    def draw_graph(self, data):
        if self.options.align:
            min_origin = None
            for df in data:
                min_origin = df.origin if min_origin == None else min(df.origin, min_origin)
                       
            for df in data:
                df.df['timestamp'] = df.df['timestamp'].map(lambda x: x - (df.origin - min_origin));
          
        for df in data:
            df.dump()
            # df.df = df.df.loc[df.df["timestamp"].between('2022-07-11', '2022-07-12')]              
            for key in graph_property:
                if key in self.props['figs'] and key in df.df.columns:  
                    df.df.plot(x='timestamp', y=key, ax=self.ax[key], label=df.label)
        plt.show()

    
def main():
    # parse options
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      default=False, help="verbose mode")
    parser.add_option("-1", "--all_in_one", action="store_true", dest="all_in_one",
                      default=False, help="draw all in one figure.")      
    parser.add_option("-p", "--profile", dest="profile",
                      default='simple', help="graph profile (simple: simple, all: all")
    parser.add_option("-a", "--align", action="store_true", dest="align",
                      default=False, help="align day of the week")
    parser.add_option("-t", "--title", dest="title", default=None, help="graph title")    

    (options, args) = parser.parse_args()
    data = []
    if len(args) == 0:
        args.append('/var/log/speedtest.log')   # default log file

    for file in args:
        data.append(SpeedTestData(file, options))

    if options.title == None:
        options.title = ' vs. '.join(args) # graph title
        
    if options.verbose:
        print('# of log files: ', len(data))

    # draw graph    
    graph = SpeedTestGraph(options)
    graph.draw_graph(data)
    
if __name__ == "__main__":
    main()