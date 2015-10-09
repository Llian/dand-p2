import pandas
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cm
import matplotlib.lines as lines
import pandasql

def prepare_data(filename):
    df = pandas.read_csv(filename)
    query = '''
            SELECT station, latitude, longitude, hour,
                sum(EXITSn_hourly) as exits, sum(ENTRIESn_hourly) as entries
            FROM df
            WHERE weekday == 1
            GROUP BY station, hour
            '''
    sht = pandasql.sqldf(query.lower(), locals())
    # traffic describes total traffic at a turnstile by adding up exits and entries
    traffic = sht.exits + sht.entries
    # net_flow is the difference between exits and entries, normalized by traffic
    net_flow = (sht.exits - sht.entries) / traffic
    # clip bottom and top .03 quantile to remove outliers
    traffic = traffic.clip(traffic.quantile(.03), traffic.quantile(.97))
    net_flow = net_flow.clip(net_flow.quantile(.03), net_flow.quantile(.97))
    # normalize values (0 to 1 for net_flow, 20 to 480 for traffic)
    norm = colors.Normalize(net_flow.min(), net_flow.max())
    sht['net_flow'] = norm(net_flow)
    norm = colors.Normalize(traffic.min(), traffic.max())
    sht['traffic'] = norm(traffic) * 480 + 20
    return sht

def transform_coordinates(series, old_origin, old_width, new_origin, new_width):
    old_origin = float(old_origin)
    old_width = float(old_width)
    new_origin = float(new_origin)
    new_width = float(new_width)
    return new_origin + (series - old_origin) / old_width * new_width

def save_plot(df, hour, time):
    # load map image and calculate dimensions
    img = plt.imread('new-york.png')
    ypixels, xpixels, bands = img.shape
    dpi = 72.
    xinch = xpixels / dpi
    yinch = ypixels / dpi
    fig = plt.figure(figsize=(xinch, yinch * 1. / .9))
    plt.axes([0., 0., 1., .9], frameon=False, xticks=[], yticks=[])
    # plot background image with map
    plt.imshow(img, interpolation='none')
    # transform lat/lon to pixel coordinates
    xpos = transform_coordinates(df.longitude, -74.1, .35, 0, xpixels)
    ypos = transform_coordinates(df.latitude, 40.55, .35, ypixels, -ypixels)
    # draw scatter plot and make sure it's limited to the map dimensions
    plt.scatter(x = xpos, y = ypos, s = df.traffic, c = df.net_flow, 
            cmap = 'RdYlGn', linewidths= 0, alpha=0.7)
    plt.xlim(0, xpixels)
    plt.ylim(ypixels, 0)
    # add title and legend to plot
    fig.suptitle('New York Subway Usage (' + time + ')', fontsize=25)
    fig.text(s='Passengers arriving at or leaving from subway stations',
            x=.5, y=.94, fontsize=15, ha='center', va='top')
    dot1 = lines.Line2D([0], [0], c='white', marker='o', mfc='gray', ms=6.0, mew=0)
    dot2 = lines.Line2D([0], [0], c='white', marker='o', mfc='gray', ms=22, mew=0)
    dot3 = lines.Line2D([0], [0], c='white', marker='o', mfc='green', ms=16, mew=0)
    dot4 = lines.Line2D([0], [0], c='white', marker='o', mfc='red', ms=16, mew=0)
    plt.legend([dot1, dot2, dot3, dot4],
            ['Few people arriving/leaving',
             'Many people arriving/levaing',
             'More people arriving than leaving',
             'More people leaving than arriving'],
            numpoints=1, loc='upper left')
    # save plot
    plt.savefig('turnstile_map_' + str(hour) + '.png', dpi=dpi)

df = prepare_data('turnstile_weather_v2.csv')
for hour in [0, 4, 8, 12, 16, 20]:
    timeframe = str((hour + 20) % 24) + ':00 - ' + str(hour) + ':00'
    save_plot(df[df.hour == hour].reset_index(), hour, timeframe)
