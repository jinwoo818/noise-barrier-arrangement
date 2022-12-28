import numpy as np
import pandas as pd
from collections import Counter
from constraint import *
import sys
import pickle
from astar import *
import math
from copy import copy # for prevent the duplication error
np.set_printoptions(threshold=sys.maxsize)
np.set_printoptions(linewidth=np.inf)

######################################################################################################################################

# Initial variables
Width = int(62)
Length = int(42)   # 레이아웃 변 길이
Barrier_length = 6 # Length of barrier

init_layout = np.zeros(Width*Length, dtype=np.int16)
layout = init_layout.reshape(-1, Width) # 20 * 20 형태 [[파이썬의 좌표 순서는 (y,x) 인데, 일반적인 좌표축으로 계산될 수 있게 순서 바꿔서 설정]]

total_gridset = [] # 연산을 위해 필요한 전체 그리드 번호 함수
for i in range(Width*Length):
    total_gridset.append(i+1)

######################################################################################################################################

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

# 데이터 입력하기 (timex = ([Faclist], [Sorlist], [Reslist])
case4_time1 = date_import('./210901_project/case4','case4_time1.csv')

######################################################################################################################################

# 방음벽 배치 이전에 시설물 고정배치하는 함수 (할당좌표를 출력함)
def init_alloc(timex, sor_buffer, fac_buffer): # timex에 time1, ... time10을 넣음
    constraint_border(timex) # 배치할때 제대로 된게 맞는지 아닌지 검사하기.
    grid_no = []
    for s in range(len(timex[0])): # Allocate Facility (Grid Number)
        for i in range(int(timex[0][s][5]-timex[0][s][3]+2*fac_buffer+1)):
            for j in range(int(timex[0][s][6]-timex[0][s][4]+2*fac_buffer+1)):
                grid_no.append(int(timex[0][s][3] - fac_buffer + i + 1 + Width * (timex[0][s][4] - fac_buffer + j)))
                grid_no.sort()
                
    # if overlap_check(grid_no) == False: # Allocate Facility <Overlapping Check>
    #     pass
    # else:
    #     overlap_facility_coo = list((Counter(grid_no)-Counter(list(set(grid_no)))).elements())
    #     print("[시설물] 배치 과정에서 중복 좌표가 발생함. (번호: {})".format(overlap_facility_coo))
    #     raise ValueError 

# 소음원 예외 조건은 없애두는 거도 방법인데, 대신에 숫자가 겹치는 것들이 많이 나올수도 있으니까 중복 숫자들은 다 없애야함
    for s in range(len(timex[1])): # Allocate Noise Source (Grid Number)   
        for i in range(2 * sor_buffer + 1):
            for j in range(2 * sor_buffer + 1):
                grid_no.append(int(timex[1][s][1] - sor_buffer + i + 1 + Width * (timex[1][s][2] - sor_buffer + j)))
                grid_no.sort()

    # if overlap_check(grid_no) == False: # Allocate Noise Source <Overlapping Check>
    #     pass
    # else:
    #     overlap_source_coo = list((Counter(grid_no)-Counter(list(set(grid_no)))).elements()) # Counter: 중복 요소 고려해서 리스트 차집합 구하는 클래스
    #     print("[소음원] 배치 과정에서 중복 좌표가 발생함. (번호: {})".format(overlap_source_coo))
    #     raise ValueError 
    return list(set(grid_no))

# TIMESTEP X에서 배치기물의 버퍼 포함 좌표, 버퍼 미포함 좌표, 버퍼만의 좌표를 리턴
def system_coord(timex):   
    grid_start = init_alloc(timex, 0, 0)                      # 버퍼 미적용 공간정보
    grid_buffer = sorted (list (set(total_gridset) & set(init_alloc(timex, 5, 3))))              # grid_buffer의 숫자를 바꿔주면 buffer distance를 조절할 수 있음 (소음원, 설비)
    grid_border = [x for x in grid_buffer if x not in grid_start] # 버퍼 자체의 공간정보
    return grid_buffer, grid_start, grid_border                   # 이 출력값은 grid_no_timex로 하자 tuple(list, list, list)

# 시작 노드와, 방향(0,1)을 받아서, 방음벽의 번호를 뽑아주는 함수
def barrier_info(node,direction): 
    assert direction == 0 or 1
    barr_list = []
    # Horizontal
    if direction == 0: 
        for i in range(Barrier_length):
            barr_list.append(node +i)
    # Vertical 
    else:              
        for i in range(Barrier_length):
            barr_list.append(node + i * Width) # width 가 맞을건데 length 인지 다시 확인
    return barr_list
    
# input: grid_no, output: acc_hor, acc_ver [최초 1회만 실행하고, 전체 돌리기 전에 결과값을 따로 받음]
def allocation(grid_no=list, W=Width, L=Length, B=Barrier_length): # default 
    accept_horizontal = []
    accept_vertical = []

    for i in range(1,W*L):
        accept_horizontal.append(i)
        accept_vertical.append(i)

    for a in range(1,W*L):
        for i in range(B):
            if [(a-1)% W + i, (a-1)//W] in list(map(lambda x: [(x-1)% W, (x-1)//W], grid_no)) and a in accept_horizontal:  # 검토사항: 방음벽 통과 사례
                accept_horizontal.remove(a)
            if (a-1)% W + i > W-1 and a in accept_horizontal:
                accept_horizontal.remove(a) 

    for a in range(1,W*L):
        for i in range(B):
            if [(a-1)%W, (a-1)//W + i] in list(map(lambda x: [(x-1)%W, (x-1)//W], grid_no)) and a in accept_vertical:  
                accept_vertical.remove(a)
            if (a-1)//W + i > L-1 and a in accept_vertical:
                accept_vertical.remove(a)  

    return accept_horizontal, accept_vertical

case4_time1_hor_ver = allocation(system_coord(case4_time1)[0])

with open('case4_time1_hor_ver.p','wb') as file:
    pickle.dump(case4_time1_hor_ver,file)


# 레이아웃 프린트 (사이즈가 커서 csv 형태로 저장함)
def layout_print(timex):
    for a in range(len(init_layout)):
        layout[(a-1)//Width, (a-1)%Width] = 0 # 초기화 #210915 이 부분 추가
    for a in system_coord(timex)[0]:
        layout[(a-1)//Width, (a-1)%Width] = 1 # 할당된 구역을 1로 처리 
    # for a in system_coord(timex)[2]:
    #     layout[(a-1)//Width, (a-1)%Width] = 0 # 외각 경계 부분을 다시 0으로 처리   
    for a in range(len(timex[0])):
        layout[timex[0][a][2]+3, timex[0][a][1]+3] = 0 # 2= .y 1 = .x 입구

    layout_array = np.array(layout)
    return layout_array

layout_case4_time1 = pd.DataFrame(layout_print(case4_time1))



layout_case4_time1.to_csv('./210901_project/case4/layout/layout_case4_time1.csv', header = False, index = False)



######################################################################################################################

# 데이터 리스트 생성 [timek: 소음 계산을 위해 별도로 저장한 초기 데이터셋 //main_timek: 일반적으로 계속 쓰게 되는 데이터셋]
timek = []
timek.append(case4_time1)


# timestep X dataset 그룹:  grid_data - format: (grid_no1, grid_init, grid_buffer)") => [([a], [b], [c]), ([a], [b], [c]), ... ] 
main_timek = []
for i in range(len(timek)):
    main_timek.append(system_coord(timek[i]))

# pickle로 저장해둔 acc_hor, acc_ver 불러오기 + 초기 필요한 정보들 전부 리스트로 저장
with open('case4_time1_hor_ver.p','rb') as file:
    case4_time1_horver_saved = pickle.load(file)



# tenday_hor[i] = i일차, 소음원+시설 배치 기준 [수평]적용[가능] 좌표
tenday_hor = []
tenday_hor.append(case4_time1_horver_saved[0])


# tenday_ver[i] = i일차, 소음원+시설 배치 기준 [수직]적용[가능] 좌표
tenday_ver = []
tenday_ver.append(case4_time1_horver_saved[1])


# tenday_horx[i] = i일차, 소음원+시설 배치 기준 [수평]적용[불가능] 좌표
tenday_horx = []
tenday_horx.append(sorted(list(set(total_gridset)-set(case4_time1_horver_saved[0]))))


# tenday_verx[i] = i일차, 소음원+시설 배치 기준 [수직]적용[불가능] 좌표
tenday_verx = []
tenday_verx.append(sorted(list(set(total_gridset)-set(case4_time1_horver_saved[1]))))


"""
# 메인 입력변수(1): fullspat[i] = i+1일차 공간정보 세트 = spatlist = (barrlist, grid_no, acc_hor, acc_ver, no)
"""
fullspat = []
for i in range(len(main_timek)):
    fullspat.append( ([] , main_timek[i][0], tenday_hor[i], tenday_ver[i], i ) ) # << 마지막에 번호를 넣기.

# 메인 입력변수(2) : 방음벽 빼기를 위해 필요한 좌표들
fullbarx = []
for i in range(len(main_timek)):
    fullbarx.append( (tenday_horx[i] , tenday_verx[i]) )

def layout_print(dayx, spatlist):    
    allocated = system_coord(dayx)
    for a in range(len(init_layout)):
        layout[(a-1)//Width, (a-1)%Width] = 0 # 초기화 
    for a in spatlist[1]:           
        layout[(a-1)//Width, (a-1)%Width] = 1 # 할당된 구역을 1로 처리 
    # for a in allocated[2]:
    #     layout[(a-1)//Width, (a-1)%Width] = 0 # 외각 경계 부분을 다시 0으로 처리   
    for a in range(len(dayx[0])):
        layout[int(dayx[0][a][2])+3, int(dayx[0][a][1])+3] = 0 
        # 설비 입구를 다시 0으로 처리 << 좌표를 뒤집어야 레이아웃에서 정확하게 적용됨>>
    layout_array = np.array(layout)
    return layout_array

def pathss(layout, dayx):
    # dist_list = []
    dlist = []
    new = []
    # 0-4-2: entrance-y 0-4-1: entrance-x // 0-6-2: soil1-y 0-6-1: soil1-x
    new = astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1]))) # iteration마다의 path에 대한 node list
    if new == None: # None값이 빠지는 경우 레이아웃 출력 (이 문제는 해결 완료되었음)
        print(layout)

    dlist = []
    for a in range(len(list(astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))-1):
        # print(len(list(astar(layout, (dayx[0][1][2],dayx[0][1][1]), (dayx[0][2][2],dayx[0][2][1]))))-1) # 추적을 위한 출력코드
        # print('a',a)
        x0 = list(map(list,astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))[a+1][0]
        x1 = list(map(list,astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))[a][0]
        y0 = list(map(list,astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))[a+1][1]
        y1 = list(map(list,astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))[a][1]
        dlist.append(math.hypot( x0 - x1, y0 - y1))
    # dist_list.append(round(sum(dlist),2))
    # print("Distance between the facilities <{}> and <{}>: {}m".format(fa+1, fb+1,round(sum(dlist),2)))
    # print("Distance list : {}".format(dist_list)) 
    return round(sum(dlist),2)
    
case4_time1_productivity = pathss(layout_print(case4_time1, fullspat[0]),case4_time1)


with open('case4_time1_productivity.p','wb') as file:
    pickle.dump(case4_time1_productivity,file)

# # 레이아웃을 리스트로 변환하는 함수
# def convert_layout(location, file):
#     df = pd.read_csv('{}/{}'.format(location, file), header=None, index_col=None, names=None)
#     return df
# x = convert_layout('./210901_project','init_test10.csv')
# print(x)
# print()