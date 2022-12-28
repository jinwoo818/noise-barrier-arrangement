from math import *
import numpy as np
import random
import pickle
from collections import Counter
import time
from obfunc_noise_copy import *
from astar import *
from constraint import *
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import sys
from copy import copy # for prevent the duplication error
from csv_import import *
np.set_printoptions(threshold=sys.maxsize)
np.set_printoptions(linewidth=np.inf)
input_day = 1
input_barr_no = 2
######################################################################################################################################

# 초기 변수 선언
start = time.time()
Width = int(62)
Length = int(42)
init_layout = np.zeros(Width*Length, dtype=np.int16)
layout = init_layout.reshape(-1, Width) #[[파이썬의 좌표 순서는 (y,x) 인데, 일반적인 좌표축으로 계산될 수 있게 순서 바꿔서 설정]]
b1 = 6 # barrier_length
total = [] # 연산을 위해 필요한 전체 그리드 번호 함수
for i in range(Width*Length):
    total.append(i+1)

######################################################################################################################################

# 그냥 case별로 입력하는 부분 다 변경하고 데이터도 다 따로 만들기. (case 1은 hour8까지, case2는 hourset4까지, case3는 hourset2까지, case4는 입력 하나 들어감.)

# 데이터 입력하기 (case_2 * 4)
day1 = date_import('./210901_project/case4','case4_time1.csv')

# dayx = ([Faclist], [Sorlist], [Reslist])
######################################################################################################################################

# 방음벽 배치 이전에 시설물 고정배치하는 함수 (할당좌표를 출력함)
def init_alloc(dayx, sor_buffer, fac_buffer): # dayx에 day1, ... day10을 넣음
    # constraint_border(dayx) # 배치할때 제대로 된게 맞는지 아닌지 검사하기.
    grid_no = []
    for s in range(len(dayx[0])): # Allocate Facility (Grid Number)
        for i in range(int(dayx[0][s][5]-dayx[0][s][3]+2*fac_buffer+1)):
            for j in range(int(dayx[0][s][6]-dayx[0][s][4]+2*fac_buffer+1)):
                grid_no.append(int(dayx[0][s][3] - fac_buffer + i + 1 + Width * (dayx[0][s][4] - fac_buffer + j)))
                grid_no.sort()

    if overlap_check(grid_no) == False: # Allocate Facility <Overlapping Check>
        pass
    else:
        overlap_facility_coo = list((Counter(grid_no)-Counter(list(set(grid_no)))).elements())
        print("[시설물] 배치 과정에서 중복 좌표가 발생함. (번호: {})".format(overlap_facility_coo))
        raise ValueError 

    for s in range(len(dayx[1])): # Allocate Noise Source (Grid Number)   
        for i in range(2 * sor_buffer + 1):
            for j in range(2 * sor_buffer + 1):
                grid_no.append(int(dayx[1][s][1] - sor_buffer + i + 1 + Width * (dayx[1][s][2] - sor_buffer + j)))
                grid_no.sort()

    if overlap_check(grid_no) == False: # Allocate Noise Source <Overlapping Check>
        pass

# 이 아래 부분 (소음원 중복 좌표 예외 조건) case 2부터 주석처리 해도 되는지 확실하게 근거를 확인하고 진행할 것. 결과가 아예 다르게 나올수도 있음. 꼭.
    
    # else:
    #     overlap_source_coo = list((Counter(grid_no)-Counter(list(set(grid_no)))).elements()) # Counter: 중복 요소 고려해서 리스트 차집합 구하는 클래스
    #     print("[소음원] 배치 과정에서 중복 좌표가 발생함. (번호: {})".format(overlap_source_coo))
    #     raise ValueError 

    return grid_no

# x일차의 버퍼 포함 좌표, 버퍼 미포함 좌표, 버퍼만의 좌표(레이아웃 visualization에 필요)를 리턴
def system_coord(dayx):   # grid_buffer의 숫자를 바꿔주면 buffer distance를 조절할 수 있음
    grid_start = init_alloc(dayx, 0, 0)                            # 버퍼 미적용 공간정보
    grid_buffer = sorted (list (set(total) & set(init_alloc(dayx, 5, 3))))       # 211123 추가함 (레이아웃 바깥의 버퍼를 리턴하는 경우 방지)
    grid_border = [x for x in grid_buffer if x not in grid_start] # '버퍼' 자체 공간정보
    return grid_buffer, grid_start, grid_border                 

# 시작 노드와, 방향(0,1)을 받아서, 방음벽의 번호를 뽑아주는 함수: 일반적으로 쓸 수 있는 함수임.
def barrier_info(node,direction): 
    assert direction == 0 or 1
    barr_list = []
    # Horizontal
    if direction == 0: 
        for i in range(b1):
            barr_list.append(node + i)
    # Vertical 
    else:              
        for i in range(b1):
            barr_list.append(node + i * Width) # width 가 맞을건데 length 인지 다시 확인

    return barr_list

######################################################################################################################################

# 데이터 리스트 생성 [dayk: 소음 계산을 위해 별도로 저장한 초기 데이터셋 //main_dayk: 일반적으로 계속 쓰게 되는 데이터셋]
dayk = []
dayk.append(day1)

# 10일치 grid_data - format: (grid_no1, grid_init, grid_buffer)") => [([a], [b], [c]), ([a], [b], [c]), ... ] 
main_dayk = []
for i in range(len(dayk)):
    main_dayk.append(system_coord(dayk[i]))

######################################################################################################################################
# pickle로 저장해둔 acc_hor, acc_ver 불러오기 + 초기 필요한 정보들 전부 리스트로 저장
with open('case4_time1_hor_ver.p','rb') as file:
    day1_horver_saved = pickle.load(file)

# tenday_hor[i] = i일차, 소음원+시설 배치 기준 [수평]적용[가능] 좌표
tenday_hor = []
tenday_hor.append(day1_horver_saved[0])

# tenday_ver[i] = i일차, 소음원+시설 배치 기준 [수직]적용[가능] 좌표
tenday_ver = []
tenday_ver.append(day1_horver_saved[1])

# tenday_horx[i] = i일차, 소음원+시설 배치 기준 [수평]적용[불가능] 좌표
tenday_horx = []
tenday_horx.append(sorted(list(set(total)-set(day1_horver_saved[0]))))

# tenday_verx[i] = i일차, 소음원+시설 배치 기준 [수직]적용[불가능] 좌표
tenday_verx = []
tenday_verx.append(sorted(list(set(total)-set(day1_horver_saved[1]))))

# pickle로 저장해둔 ob3 -> initial productivity
with open('case4_time1_productivity.p','rb') as file:
    day1_proc = pickle.load(file)

proc_dayx = []
proc_dayx.append(day1_proc)

print(proc_dayx)

"""
# 메인 입력변수(1): fullspat[i] = i+1일차 공간정보 세트 = spatlist = (barrlist, grid_no, acc_hor, acc_ver, no)
"""
fullspat = []
for i in range(len(main_dayk)):
    fullspat.append( ([] , main_dayk[i][0], tenday_hor[i], tenday_ver[i], i ) ) # << 마지막에 번호를 넣기.

def layout_print(dayx, spatlist):    
    # allocated = system_coord(dayx)
    for a in range(len(init_layout)):
        layout[(a-1)//Width, (a-1)%Width] = 0 # 초기화 
    for a in spatlist[1]:           
        layout[(a-1)//Width, (a-1)%Width] = 1 # 할당된 구역을 1로 처리 
    # for a in allocated[2]:
    #     layout[(a-1)//Width, (a-1)%Width] = 0 # 외각 경계 부분을 다시 0으로 처리   
    for a in range(len(dayx[0])):
        layout[int(dayx[0][a][2])+3, int(dayx[0][a][1])+3] = 0      # +3은 버퍼 사이즈만큼 더 쓴거임.
        # 설비 입구를 다시 0으로 처리 << 좌표를 뒤집어야 레이아웃에서 정확하게 적용됨>>
    layout_array = np.array(layout)
    # print("layout_array")
    # print(layout_array)
    return layout_array
    
# 메인 입력변수(2) : 방음벽 빼기를 위해 필요한 좌표들
fullbarx = []
for i in range(len(main_dayk)):
    fullbarx.append( (tenday_horx[i] , tenday_verx[i]) )

######################################################################################################################################

# 방음벽 추가 함수 [기존 정보를 반영하여 랜덤하게 추가]
def add_barr(spatlist):
    spat_info = spatlist #(barrlist, grid_no, acc_hor, acc_ver, no)
    no = spat_info[4]
    width = 62 # 옆길이
    Barr = 6 # Barrier length   # 이거를 잘 수정해야 하는게 처음 배치랑 Barr가 다르면 오답 나와.
    del_hor_spat = []
    del_ver_spat = []
    prob = random.randint(0,1)     # 수평/수직 고르기 

    if prob == 0:    # 수평
        horchoice = random.choice(spat_info[2])
        # info = (horchoice, prob)
        # print("1. 수평배치 - 선택된 좌상단 좌표: <{}>".format(horchoice))
    # 1-1 수평으로 넣는 경우 빠지는 수평 좌표 = del_hor_spat
        for i in range(horchoice-Barr+1,horchoice+Barr):
            del_hor_spat.append(i)
    # 1-2 수평으로 넣는 경우 빠지는 수직 좌표 << 수정 완료함. 이렇게 짜이는 논리를 잘 생각하기 >>
        for k in range(Barr):             # k = 좌표 하나당 
            for i in range(-Barr+1,1): # i = 선택된 좌상단 지점을 0으로 놓고, 방음벽 길이만큼 후퇴한 리스트를 받음 (-2,-1, 0) 이거 진짜 논리 잘 생각해야 함.
                del_ver_spat.append(i*width+horchoice+k)
    # 기존꺼에서 새로 설정되는 공간정보 연산 // 되는 애랑 안 되는 애를 따로 받을 것.   
        calc_hor_a = sorted(list(set(spat_info[2])-set(del_hor_spat)))
        calc_ver_a = sorted(list(set(spat_info[3])-set(del_ver_spat)))
    # 방음벽 정보 갱신
        barr_fixed = spat_info[0]
        barr_fixed.append((horchoice, prob))
    # 그리드 정보 갱신
        grid_fixed = sorted(spat_info[1] + barrier_info(horchoice, prob))
        return barr_fixed, grid_fixed, calc_hor_a, calc_ver_a, no  # << 몇번째인지 넘버링

    else:    # 수직
        verchoice = random.choice(spat_info[3])        
        # info = (verchoice, prob)
        # print("2. 수직배치 - 선택된 좌상단 좌표: <{}>".format(verchoice))
    # 2-1 수직으로 넣는 경우 빠지는 수평 좌표 << 헷갈릴수 있는데 잘 확인해.
        for k in range(Barr):
            for i in range(-Barr+1, 1):
                del_hor_spat.append(k*width+verchoice+i)
    # 2-2 수직으로 넣는 경우 빠지는 수직 좌표
        for i in range(-Barr+1,Barr): # 얘는 줄이고. 
            del_ver_spat.append(i*width+verchoice)
        calc_hor_b = sorted(list(set(spatlist[2])-set(del_hor_spat)))
        calc_ver_b = sorted(list(set(spatlist[3])-set(del_ver_spat)))
    # 방음벽 정보 갱신
        barr_fixed = spat_info[0]
        barr_fixed.append((verchoice, prob))
    # 그리드 정보 갱신
        grid_fixed = sorted(spat_info[1] + barrier_info(verchoice, prob))
        return barr_fixed, grid_fixed, calc_hor_b, calc_ver_b, no  

# 방음벽 제거 함수 [기존 정보에 기반하여 있는 방음벽 중 하나를 제거]
def rem_barr(spatlist):
    spat_info = spatlist #(barrlist, grid_no, acc_hor, acc_ver, no)
    no = spat_info[4]
    width = 62 # 옆길이
    Barr = 6 # Barrier length   # 이거를 잘 수정해야 하는게 처음 배치랑 Barr가 다르면 오답 나와.
    del_hor_spat = []
    del_ver_spat = [] 
    barr_sel = random.choice(spat_info[0])
    prob = barr_sel[1]

    if prob == 0:    # 수평
        horchoice = barr_sel[0]
        # print("1. 수평배치 - 빠지는 방음벽 좌표:<{}>".format(horchoice))
    # 1-1 수평으로 넣는 경우 빠지는 수평 좌표 = del_hor_spat
        for i in range(horchoice-Barr+1,horchoice+Barr):
            del_hor_spat.append(i)
    # 1-2 수평으로 넣는 경우 빠지는 수직 좌표 << 수정 완료함. 이렇게 짜이는 논리를 잘 생각하기 >>
        for k in range(Barr):             # k = 좌표 하나당 
            for i in range(-Barr+1,1): # i = 선택된 좌상단 지점을 0으로 놓고, 방음벽 길이만큼 후퇴한 리스트를 받음 (-2,-1, 0) 이거 진짜 논리 잘 생각해야 함.
                del_ver_spat.append(i*width+horchoice+k)
    # 연산은 같게 하되, 기존의 안되는 위치 정보를 같이 불러와서 교집합만 빼줘야 함.     
        real_no_hor = set(del_hor_spat) - set(fullbarx[no][0])
        real_no_ver = set(del_ver_spat) - set(fullbarx[no][1]) 
        calc_hor_a = sorted(list((set(spatlist[2])|real_no_hor)&set(total)))
        calc_ver_a = sorted(list((set(spatlist[3])|real_no_ver)&set(total)))
    # 방음벽 정보 갱신
        barr_fixed = spat_info[0].copy()
        barr_fixed.remove((horchoice, prob))
    # 그리드 정보 갱신
        grid_fixed = sorted( list( set(spat_info[1]) - set(barrier_info(horchoice, prob)) ) )
        return barr_fixed, grid_fixed, calc_hor_a, calc_ver_a, no 

    else:    # 수직
        verchoice = barr_sel[0]
        # print("2. 수직배치 - 빠지는 방음벽 좌표: <{}>".format(verchoice))
    # 2-1 수직으로 넣는 경우 빠지는 수평 좌표 << 헷갈릴수 있는데 잘 확인해.
        for k in range(Barr):
            for i in range(-Barr+1, 1):
                del_hor_spat.append(k*width+verchoice+i)
    # 2-2 수직으로 넣는 경우 빠지는 수직 좌표
        for i in range(-Barr+1,Barr): # 얘는 줄이고. 
            del_ver_spat.append(i*width+verchoice)
        # 연산은 같게 하되, 기존의 안되는 위치 정보를 같이 불러와서 교집합만 빼줘야 함.     
        real_no_hor = set(del_hor_spat) - set(fullbarx[no][0])                         
        real_no_ver = set(del_ver_spat) - set(fullbarx[no][1])
        calc_hor_b = sorted(list((set(spatlist[2])|real_no_hor)&set(total)))
        calc_ver_b = sorted(list((set(spatlist[3])|real_no_ver)&set(total)))
    # 방음벽 정보 갱신
        barr_fixed = spat_info[0].copy()
        barr_fixed.remove((verchoice, prob))
    # 그리드 정보 갱신
        grid_fixed = sorted( list( set(spat_info[1]) - set(barrier_info(verchoice, prob)) ) )
        return barr_fixed, grid_fixed, calc_hor_b, calc_ver_b, no

"""
입력변수 세팅: dayx_barrk = gen(fullspat[x-1], k) x일차 + 방음벽 y개일때 << 바꿔주면서 반복하기.
"""
# 배치함수 [list, 반복횟수]
def gen(spatlist):
    first = spatlist
    for i in range(input_barr_no):
        iteration = add_barr(first)
        first = iteration
    return first

setup_sol = gen(fullspat[input_day-1])

######################################################################################################################################

# 방음벽 그리드 좌표 전체 뽑아주기 : sol[0] 리스트를 인수로 받음 [ [133,0] [200,1] ]
def barrier_coo(sol_list):  
    coo_list = []
    for i in range(len(sol_list)): 
        coo_list.extend(barrier_info(sol_list[i][0],sol_list[i][1]))     
    coo_list.sort()
    return coo_list

# 이웃해
def neighbor(spatlist):
    remove = rem_barr(spatlist)
    addd = add_barr(remove)
    return addd

# print(fullspat[0])
# print("")
# print(neighbor(fullspat[0]))
# neighbor(setup_sol)

######################################################################################################################################
######################################################################################################################################
# Astar: Distance (토사-입구 1번) 
def totalpath(layout, dayx):
    # dist_list = []
    dlist = []
    # new = []
    # # 0-4-2: entrance-y 0-4-1: entrance-x // 0-6-2: soil1-y 0-6-1: soil1-x
    # new = astar(layout, (3,8), (23,56)) # iteration마다의 path에 대한 node list (start: 5,3 end: 56,20)
    # if new == None: # None값이 빠지는 경우 레이아웃 출력 (이 문제는 해결 완료되었음)
    #     print(layout)
    try:
        for a in range(len(list(astar(layout, (3,8), (23,56))))-1): #start 랑 end는 buffer 5 3 기준으로 상수값 넣음. 나중에 바꾸기
        # for a in range(len(list(astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))-1): #start 랑 end는 buffer 5 3 기준으로 상수값 넣음. 나중에 바꾸기
            # print(len(list(astar(layout, (dayx[0][1][2],dayx[0][1][1]), (dayx[0][2][2],dayx[0][2][1]))))-1) # 추적을 위한 출력코드
            # print('a',a)
            x0 = list(map(list,astar(layout, (3,8), (23,56))))[a+1][0]
            x1 = list(map(list,astar(layout, (3,8), (23,56))))[a][0]
            y0 = list(map(list,astar(layout, (3,8), (23,56))))[a+1][1]
            y1 = list(map(list,astar(layout, (3,8), (23,56))))[a][1]
            # x0 = list(map(list,astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))[a+1][0]
            # x1 = list(map(list,astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))[a][0]
            # y0 = list(map(list,astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))[a+1][1]
            # y1 = list(map(list,astar(layout, (int(dayx[0][1][2]),int(dayx[0][1][1])), (int(dayx[0][2][2]),int(dayx[0][2][1])))))[a][1]
            dlist.append(math.hypot( x0 - x1, y0 - y1))
    except TypeError:
        pass
    # dist_list.append(round(sum(dlist),2))
    # print("Distance between the facilities <{}> and <{}>: {}m".format(fa+1, fb+1,round(sum(dlist),2)))
    # print("Distance list : {}".format(dist_list)) 
    return 2*round(sum(dlist),2)

# def totalpath(layout):
#     # dist_list = []
#     dlist = []
#     new = []
#     # 0-4-2: entrance-y 0-4-1: entrance-x // 0-6-2: soil1-y 0-6-1: soil1-x
#     new = astar(layout, (0,5), (20,53)) # iteration마다의 path에 대한 node list
#     if new == None: # None값이 빠지는 경우 레이아웃 출력 (이 문제는 해결 완료되었음)
#         print(layout)

#     dlist = []
#     for a in range(len(list(astar(layout, (0,5), (20,53))))-1):
#         # print(len(list(astar(layout, (dayx[0][1][2],dayx[0][1][1]), (dayx[0][2][2],dayx[0][2][1]))))-1) # 추적을 위한 출력코드
#         print('a',a)
#         x0 = list(map(list,astar(layout, (0,5), (20,53))))[a+1][0]
#         x1 = list(map(list,astar(layout, (0,5), (20,53))))[a][0]
#         y0 = list(map(list,astar(layout, (0,5), (20,53))))[a+1][1]
#         y1 = list(map(list,astar(layout, (0,5), (20,53))))[a][1]
#         dlist.append(math.hypot( x0 - x1, y0 - y1))
#     # dist_list.append(round(sum(dlist),2))
#     # print("Distance between the facilities <{}> and <{}>: {}m".format(fa+1, fb+1,round(sum(dlist),2)))
#     # print("Distance list : {}".format(dist_list)) 
#     return 2*round(sum(dlist),2)


# 최종 거리계산 함수 (토사-입구 왕복)
# def totalpath(layout, dayx):
#     a11 = path_ent_soil1(layout, dayx)
#     return 2*a11

######################################################################################################################################

# def ob_func1(dateset=list):
#     barrier_cost = 212.3 # 150만원의 USD 환산: 1273.84 나누기 6m = 212.30 // 너무 크다 싶으면 65만원: 552.00/6 = 92 USD로 수정
#     # 1-2. 설치/해체 비용
#     inst_unit = 7.38 # 1m^3당 1.23 USD // 6m 높이 기준 1 그리드 당 7.38 USD
#     dist_unit = 2.88 # 1m^3당 0.48 USD // 6m 높이 기준 1 그리드 당 2.88 USD
#     mob_cost = 0
#     # barr_list 내의 원소를 튜플로 만들어야 오류가 안날거 같은데? Typeerror: unhashable type: list <<
#     for i in range(len(dateset)-1):
#         install = len(list(set(dateset[i+1][0]) - set(dateset[i][0]))) * inst_unit # future timestep 방향 차집합
#         dismantle = len(list(set(dateset[i][0]) - set(dateset[i+1][0]))) * dist_unit    # past timestep 방향 차집합     
#         mob_cost += install + dismantle
#     ob1 = -round((max(max_barrier) * b1 * barrier_cost + mob_cost),2)
#     print("[ob1]10_setup_solrier_cost: {} USD".format(ob1))
#     return ob1    
# def ob_func2(spatlist):
"""
dayk[input_day-1]을 안해서 안바뀐게 맞고 noise function에는 문제가 없음.

"""
def ob_func2(spatlist):
    # barr_coo = barrier_coo(spatlist[0]) # 일자별(i) 방음벽 번호 출력
    ob2_dayx = obj2(spatlist, dayk[input_day-1]) 
    ob2 = round(ob2_dayx, 2)
    print("[ob2]10_day_health_impact: {} USD".format(ob2))
    return ob2

def hour_productivity(distance):
    bucket_cap1 = 1.56   # 백호 380 버킷용량(m3)
    bucket_cap2 = 1.27   # 백호 300 버킷용량(m3)
    bucket_co = 0.55     # 버킷 계수
    dump_cap = 18        # 덤프 15톤 적재토량(15t)
    
    dump_cycle_N1 = dump_cap / (bucket_cap1*bucket_co) # 덤프 1대 분량 적재를 위한 백호 380 사이클수
    dump_cycle_N2 = dump_cap / (bucket_cap2*bucket_co) # 덤프 1대 분량 적재를 위한 백호 300 사이클수 
    
    exc_workeff = 0.75  # 굴삭기 작업 효율
    cms = 21  #굴삭기 1회 사이클 시간
    cmt1 = cms*dump_cycle_N1/(60*exc_workeff)
    cmt2 = cms*dump_cycle_N2/(60*exc_workeff)
    
        
    t2 = (distance/7 +distance/8) * 60/1000
    t3 = 1.1 + 0.42 + 3.77+ 1.5    
    
    cycleT1 = cmt1+t2+t3
    cycleT2 = cmt2+t2+t3
    workeff = 0.9                                     # 작업효율 (고정값)
    loadcap = 15                                      # 덤프트럭 적재용량(덤프규격: t) 
    unitW = 2.4                                       # 자연 상태에서 토석의 단위중량 
    excload = loadcap/unitW                           # 흐트러진 상태의 1회 적재량

    q1 = 60*excload*workeff/cycleT1
    q2 = 60*excload*workeff/cycleT2 
    
    return round(2 * q1 + q2, 3)   

def ob_func3(spatlist): # 얘만 결과 값이 아니라 리스트 자체로 리턴함. 변환 일자를 기억시켜야 하기 때문에 조정해야됨.

    proc = totalpath(layout_print(dayk[input_day-1], spatlist),dayk[input_day-1])
    if proc == 0 or None:
        return None
    print("이동거리: {}m".format(proc))
    print("원래 최단거리: 122.72m - > 68m") 
    
    ob3 = round(8*( hour_productivity(proc)- hour_productivity(68)) * 0.00084 * 10019 , 2 ) # usd 0.02/m
    print("[ob3]8 hour_productivity: {} USD".format(ob3))
    print("68m 기준치")
    print(round(8*hour_productivity(68) * 0.00084 * 10019 , 2 ))
    return ob3

def fitness(spatlist):

    a = ob_func2(spatlist)
    b = ob_func3(spatlist)
    if b == None:
        return None    
    return a+b

# Ob3: Productivity // 급하니까 직접 수정하기
# dayk[i]의 i를 해당일자 번호에 맞게 바꿔줘야 함 1일일때 0 이런식으로 
# """    
# def ob_func3(spatlist): # 얘만 결과 값이 아니라 리스트 자체로 리턴함. 변환 일자를 기억시켜야 하기 때문에 조정해야됨.


# simulated annealing
def simulated_annealing(spatlist):

    # 온도 매커니즘
    init_temp = 1
    fin_temp = 0.05
    alpha = 0.99 # 감률 (최적치 구현을 위해 직접 조정 필요.) (init_temp = 100 / alpha 0995에서 iteration 약 919회 / 999에서 iteration 약 4603회)
    curr_temp = init_temp
    current = spatlist
    solution = current
    # 임계 온도 도달까지 반복 수행
    
    #211018 추가
    iteration = 0
    graphlist = []
    fitlist = []
    sollist = []
    graphlist.append(fitness(current))
    fitlist.append(fitness(current))
    sollist.append(current)
  
    while curr_temp > fin_temp:
        # # 반복 횟수 추적 (주석처리 해도 됨)
        iteration +=1
        print("\n\n")
        print("iteration : <{}>".format(iteration))
        
        neighbors = neighbor(solution)
        if fitness(neighbors) == None:
            continue
        
        fit_diff = fitness(neighbors) - fitness(solution)
        
        # fitness가 좋아지면 반드시 이동 (fitness가 극대화되는 방향으로)
        if fit_diff >= 0:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
            print(fit_diff)
            print("1. fitness 증가로 인해 이동")
            solution = neighbors
            fitlist.append(fitness(solution))

            if graphlist[-1] < fitness(solution):    
                graphlist.append(fitness(solution))
                sollist.pop()
                sollist.append(solution)
            else:
                graphlist.append(graphlist[-1])

        # fitness가 나빠지더라도 확률적으로 이동(local 수렴 방지)
        else:
            if random.uniform(0,1) < math.exp(fit_diff/curr_temp):
                solution = neighbors
                fitlist.append(fitness(solution))
                print("2-1. fitness가 나쁘지만 이동")

                if graphlist[-1] < fitness(solution):    
                    graphlist.append(fitness(solution))
                    sollist.pop()
                    sollist.append(solution)
                else:
                    graphlist.append(graphlist[-1])
        
            # 확률적으로 기존 해 유지
            else:
                print("2-2. fitness가 나빠서 안 이동")
                
                fitlist.append(fitness(solution))
                if graphlist[-1] < fitness(solution):    
                    graphlist.append(fitness(solution))
                    sollist = sollist
                else:
                    graphlist.append(graphlist[-1])
                    sollist = sollist
        curr_temp *= alpha
    
    # 211018 추가
    # print("fitlist")
    # print(fitlist)
    # print("sollist")
    # print(sollist)
    # print("graphlist")
    # print(graphlist)
    # print("Optimal Layout -day1")
    # print(layout_print(dayk[input_day-1], solution)) # sollist[0][0]
    # print("Optimal fitness value") # sollist[0]은 맞는데 // sollist 자체가 잘못 뽑히고 있음.
    # print(fitness(sollist[0])) # 이거 맞나 확인

    return solution, fitlist, sollist, graphlist

######################################################################################################################################

# # 문제 실행

sim_an = simulated_annealing(setup_sol)
print(sim_an)
now = datetime.datetime.now()
nowDatetime = now.strftime('%y%m%d_%H%M')
print("time :", time.time() - start, "sec")
plt.plot(sim_an[1])
plt.savefig(f'{nowDatetime} case 4 {input_day}step {input_barr_no}barr solutionimg.png')

solutiondf = pd.DataFrame(sim_an[1])
solutiondf.to_csv(f'{nowDatetime} case 4 {input_day}step {input_barr_no}barr solutiondf.csv')

# print("레이아웃 출력")
solday1 = pd.DataFrame(layout_print(dayk[input_day-1], sim_an[0]))
solday1.to_csv(f'{nowDatetime} case 4 {input_day}step {input_barr_no}barr layout.csv')

######################################################################################################################################