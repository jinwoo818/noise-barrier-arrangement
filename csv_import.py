import pandas as pd
from collections import Counter

# csv 파일 정보 불러오기: 출력값 = (Faclist, Sorlist, Reslist)
def date_import(location, file):
    
    # 일차별로 입력되어야 하는 요소들: 시설, 소음원, 거주자 
    Faclist = []
    Sorlist = []
    Reslist = []
    data_pd = pd.read_csv('{}/{}'.format(location, file), header=0, index_col=None, names=None)

    for i in range(len(data_pd)): # [0,1,2,3,, ... , 10]
        data = data_pd.loc[[i]]

        if data.loc[i,'Type'] == 'Facility': 
            # facilitylist.append(list(data.loc[i,['x','y']]))
            # inputValue = list(data.loc[i,['name','x','y','left']])
            Faclist.append(list(data.loc[i,['name','x','y','left', 'up', 'right', 'down']]))
        
        elif data.loc[i,'Type'] == 'Noise_source': 
            Sorlist.append(list(data.loc[i,['name','x','y','pwl','freq']]))
        
        elif data.loc[i,'Type'] == 'Resident': 
            Reslist.append(list(data.loc[i,['name','x','y', 'res_pop']]))
        
        else: 
            print(data.loc[i,'Type'])

    return Faclist, Sorlist, Reslist # 이 부분에서 이제 indexing 두번 해도 되는게, 각 리스트별로 들어가는 형태는 고정돼있음.