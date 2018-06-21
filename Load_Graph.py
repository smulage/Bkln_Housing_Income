# import standard libraries
import pandas as pd
import numpy as np
import time as tm
import sys

print(sys.version)

# import libraries to read zipped files off the web
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen

# import libraries for visualization
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats.stats import pearsonr
% matplotlib notebook


# Download Construction stats for Brooklyn
# ----------------------------------------
file_ind = list(pd.date_range('01-2005', periods=132, freq='M')
                .strftime('%m%y'))  # time period covered
r = []
c = 0
start = tm.time()
for i in file_ind:
    # download and unzip each file, extracting only relevant columns
    url = urlopen('https://www1.nyc.gov/assets/buildings/foil/per'+ i +'excel.zip')
    z = ZipFile(BytesIO(url.read()))
    df = pd.read_excel(z.open(z.infolist()[0].filename)
                       , skiprows=2, parse_cols='A,E,G,H,M:V,Y:AB')
    # filter for Brooklyn's new construction permit requests only
    dff = df[(df['Borough']=='Brooklyn') & (df['Filing Status']=='INITIAL')]
    r.append(dff)
    c+=len(dff)
    print ('File: %s, Length=%d, Filtered=%d' %('per'+i+'.xls', len(df), len(dff)))
end = tm.time()
print('Filtered file size: %d' %c)
print('Time taken: %.2f seconds' %(end-start))

# concatenate all records into one data frame
dfr = pd.concat(r, keys=['df'+i for i in file_ind])
dfr.reset_index(inplace=True)
dfr.rename(columns={'level_0': 'file', 'level_1': 'fileRow'}, inplace=True)


# Import Brooklyn's Income stats
# ----------------------------------------
IncStats = pd.read_table('Bkln_Income.txt', sep=',')
IncStats['Year'] = IncStats['Year'].apply(lambda x: str(x))
IncStats.set_index('Year', inplace=True)


# Aggregate Construction data and join with IncStats
# --------------------------------------------------
dfr['Year'] = dfr['file'].apply(lambda x: '20'+x[-2:])
dfr_tot = pd.DataFrame({'Total': dfr.groupby('Year').size()})
dfr_res = pd.DataFrame({'Residential': dfr[dfr['Residential'] == 'YES'].groupby('Year').size()})
dfr_com = pd.DataFrame({'Commercial': dfr[dfr['Residential'] != 'YES'].groupby('Year').size()})
dfr_agg = (dfr_tot.merge(dfr_res, how='inner', left_index=True, right_index=True)
                  .merge(dfr_com, how='inner', left_index=True, right_index=True)
                  .merge(IncStats, how='inner', left_index=True, right_index=True))

# Visualize stats on two grids
# --------------------------------------------------
plt.style.use('seaborn-darkgrid')
plt.figure()

plt.subplot(211)  # highlight the increase in residential construction permits
plt.plot(dfr_agg['Total'], label='All', alpha=0.25)
plt.plot(dfr_agg['Residential'], label='Residential', alpha=0.75)
plt.plot(dfr_agg['Commercial'], label='Commercial', alpha=0.25)
plt.legend(ncol=3, fontsize='small', loc='upper left')
plt.xlabel('Year', size=9)
plt.ylabel('New Construction Permits', size=9)
plt.title('Comparison of new Residential Construction Permits against Household Income in Brooklyn NY, USA', size=9)

plt.subplot(212)  # confirm that the construction and household income are correlated
p = pearsonr(dfr_agg['Income'], dfr_agg['Residential'])[0]
plt.scatter(dfr_agg['Income'], dfr_agg['Residential'], alpha=0.5)
plt.yticks(np.arange(0, dfr_agg['Residential'].max()+dfr_agg['Residential'].max()/4, 5000).round(-3))
plt.xlabel('Median Household Income (adj. for Inflation)', size=9)
plt.ylabel('Residential Permits', size=9)
xmin, xmax = plt.xlim()
ymin, ymax = plt.ylim()
_ = plt.text(xmin+((xmax-xmin)/50), ymax-(ymax/10), 'Pearson: {:.2f}'.format(p), size=8)

