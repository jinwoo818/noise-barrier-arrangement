import math
import numpy as np

# 선분 교차 알고리즘 

case_daly = 8760   # (365 *24)

def divide_check(pathx1,pathy1, pathx2,pathy2, nodex1,nodey1, nodex2,nodey2):   # 보기 편하게 바꿈
    f1= (pathx2-pathx1)*(nodey1-pathy1) - (pathy2-pathy1)*(nodex1-pathx1)
    f2= (pathx2-pathx1)*(nodey2-pathy1) - (pathy2-pathy1)*(nodex2-pathx1)
    if f1 * f2 < 0 :
        return True
    else:
        return False

def cross_check(x11,y11, x12,y12, x21,y21, x22,y22):
    b1 = divide_check(x11,y11, x12,y12, x21,y21, x22,y22)
    b2 = divide_check(x21,y21, x22,y22, x11,y11, x12,y12)
    if b1 and b2:
        return True
    else:
        return False

# 1 = x , 2 = y , 3= pwl
def spl_init(dayx):
    r = 0
    s = 0
    spl_list = []
    dist_list = []
  
    for s in range(len(dayx[1])):
        for r in range(len(dayx[2])):
            spl_list.append(dayx[1][s][3] - 20 * math.log10(math.hypot(dayx[1][s][1] - dayx[2][r][1], dayx[1][s][2] - dayx[2][r][2])) - 8)
    spl_list = np.array(spl_list)
    spl_matrix = spl_list.reshape(-1, len(dayx[2]))

    for s in range(len(dayx[1])):
        for r in range(len(dayx[2])):
            dist_list.append(math.hypot(dayx[1][s][1] - dayx[2][r][1], dayx[1][s][2] - dayx[2][r][2]))
    dist_list = np.array(dist_list)
    # dist_matrix = dist_list.reshape(-1, len(dayx[2]))        
    sen_matrix = 10**(0.1*(spl_matrix))  
    sum_spl = 10*np.log10(sen_matrix.sum(axis=0))
    lden = 10.0* np.log10((8.0*10.0**(0.1*sum_spl)+4.0*10.0**0.5+80.0)/24.0)
    daly_list = []
    for r in range(len(dayx[2])):   
        if lden[r] <= 40:
            daly_list.append(0)
        elif lden[r] > 40 and lden[r] <=85:
            daly_list.append((78.927 - 3.1162 * lden[r] + 0.0342 * lden[r]**2) * 0.0002 + ((1.08**(0.1*(lden[r]-40)) - 1) / 1.08**(0.1*(lden[r]-40))) * 0.0099225) 
        elif lden[r] > 85 and lden[r] <=90:
            daly_list.append(0.002801466 + (78.927 - 3.1162 * lden[r] + 0.0342 * lden[r]**2) * 0.0002 + ((1.08**(0.1*(lden[r]-40)) - 1) / 1.08**(0.1*(lden[r]-40))) * 0.0099225)
        else:
            daly_list.append(0.004344752 + (78.927 - 3.1162 * lden[r] + 0.0342 * lden[r]**2) * 0.0002 + ((1.08**(0.1*(lden[r]-40)) - 1) / 1.08**(0.1*(lden[r]-40))) * 0.0099225)
    
    vsly = 152465.8                                           
    hcost_list = []
    for r in range(len(dayx[2])): 
        hcost_list.append(round(daly_list[r]*vsly*dayx[2][r][3] / case_daly, 2))  # /8760 한 이유: Duration 1년 기준으로 daly가 산정된다는 WHO 레퍼런스
    # print("[ #Obj 2. Health impact by noise exposure ]")
    # print ("Initial total Health damage cost(방음벽 미설치/최초상태): {} USD".format(round(sum(hcost_list),2)))
    return round(sum(hcost_list),2)

def x_coo(a,width=62):
    k = (a-1)%width
    return k

def y_coo(a,width=62):
    k = (a-1)//width
    return k

# 2.소음 Cost 산정 함수 전체 
def spl(dayx, spatlist, width=62): # 여기서 grid_no는 공간정보 산출을 위해 그리드 한개의 번호를 받는거임 (리스트 x)
    r = 0
    s = 0
    barr_info = spatlist[0]
    
    stedpoint = []         # stedpoint[i][0] = start. [i][1] = end, [i][2] = mid
    for i in range(len(barr_info)):
        if barr_info[i][1] == 0:
            stedpoint.append((barr_info[i][0],barr_info[i][0]+5,barr_info[i][0]+3))
        else:
            stedpoint.append((barr_info[i][0],barr_info[i][0]+5*width,barr_info[i][0]+3*width))

    spl_list = []
    dist_list = []
    barr_list = []

    # 2-1 SPL (방음벽 일괄 적용 전)
    for s in range(len(dayx[1])):
        for r in range(len(dayx[2])):
            spl_list.append(dayx[1][s][3] - 20 * math.log10(math.hypot(dayx[1][s][1] - dayx[2][r][1], dayx[1][s][2] - dayx[2][r][2])) - 8)
    spl_list = np.array(spl_list)
    spl_matrix = spl_list.reshape(-1, len(dayx[2])) # matrix
    print("[dBA]")
    print(spl_matrix)

    # 2-2 Propagation path
    for s in range(len(dayx[1])):
        for r in range(len(dayx[2])):
            dist_list.append(math.hypot(dayx[1][s][1] - dayx[2][r][1], dayx[1][s][2] - dayx[2][r][2]))
    dist_list = np.array(dist_list)
    # dist_matrix = dist_list.reshape(-1, len(dayx[2])) # matrix
    # print("/ resident 1 / resident 1 / resident 3 / resident 4 / [소음원-거주자 간 거리 (m)]")
    # print (dist_matrix)

    # 2-3 Barrier attenuation
    cross_point = []
    for s in range(len(dayx[1])):
        for r in range(len(dayx[2])):
            cross_point_list = []
            for b in range(len(stedpoint)):
                if cross_check(dayx[2][r][1],dayx[2][r][2], dayx[1][s][1],dayx[1][s][2], x_coo(stedpoint[b][0]),y_coo(stedpoint[b][0]), x_coo(stedpoint[b][1]),y_coo(stedpoint[b][1])) == True:
                   cross_point_list.append(stedpoint[b][2])
            if len(cross_point_list)!=0:
                cross_point.append(cross_point_list)
            else: 
                cross_point.append([])

    for t in range(len(cross_point)):
        if len(cross_point[t])==0:
            barr_list.append(0)
        else:        
            barr_atten = 10 * math.log10(3 + (10000 / 343) * (math.hypot(math.hypot(dayx[1][s][1] - x_coo(cross_point[t][0]), dayx[1][s][2] - y_coo(cross_point[t][0])), 6) + \
            math.hypot(math.hypot(dayx[2][r][1] - x_coo(cross_point[t][0]), dayx[2][r][2] - y_coo(cross_point[t][0])), 6) - math.hypot(dayx[1][s][1] - dayx[2][r][1], dayx[1][s][2] - dayx[2][r][2])))
            
            if  barr_atten <= 25:
                barr_list.append(barr_atten)
            else:
                barr_list.append(25)     # 최대감쇠 제한(ISO 표준)

            
    # print("a")
    # print(stedpoint)
    # print(cross_point_list)
    # print(cross_point)
    # print(barr_list)
    barr_list = np.array(barr_list)
    barr_matrix = barr_list.reshape(-1, len(dayx[2]))
    # print("/ resident 1 / resident 2 / resident 3 / resident 4 / [그리드 에 적용 시 방음벽 감쇠량 (dBA)]")
    # print(barr_matrix)


    # 2-4 방음벽 적용 이후 spl 재산정    
    sen_matrix = 10**(0.1*(spl_matrix-barr_matrix))  # 방음벽 적용 이후 sound energy magnitude
    sum_spl = 10*np.log10(sen_matrix.sum(axis=0))
    # print("/ resident 1 / resident 2 / resident 3 / resident 4 / [방음벽 적용 후 최종 spl (dBA)]")
    # print (sum_spl)  

    # 2-5 lden 변환
    lden = 10.0* np.log10((8.0*10.0**(0.1*sum_spl)+4.0*10.0**0.5+80.0)/24.0)

    # 2-6 Daly 산정
    daly_list = []
    for r in range(len(dayx[2])):   
        if lden[r] <= 40:
            daly_list.append(0)
        elif lden[r] > 40 and lden[r] <=85:
            daly_list.append((78.927 - 3.1162 * lden[r] + 0.0342 * lden[r]**2) * 0.0002 + ((1.08**(0.1*(lden[r]-40)) - 1) / 1.08**(0.1*(lden[r]-40))) * 0.0099225) 
        elif lden[r] > 85 and lden[r] <=90:
            daly_list.append(0.002801466 + (78.927 - 3.1162 * lden[r] + 0.0342 * lden[r]**2) * 0.0002 + ((1.08**(0.1*(lden[r]-40)) - 1) / 1.08**(0.1*(lden[r]-40))) * 0.0099225)
        else:
            daly_list.append(0.004344752 + (78.927 - 3.1162 * lden[r] + 0.0342 * lden[r]**2) * 0.0002 + ((1.08**(0.1*(lden[r]-40)) - 1) / 1.08**(0.1*(lden[r]-40))) * 0.0099225)
    # print("/ resident 1 / resident 2 / resident 3 / resident 4 / resident 5 / resident 6 [Daly (years)]")
    # print(daly_list)
    # 2-7 Vsly 산정 (나중에 최신 레퍼런스로 수정하기)
    vsly = 152465.8                              # 최신화              

    # 2-8 Health damage cost (VSLY는 수명 1년의 가치를 정량화한 금액이므로, daly와 곱해야 최종 금액이 산정됨)
    hcost_list = []
    for r in range(len(dayx[2])): 
        hcost_list.append(round(daly_list[r]*vsly*dayx[2][r][3] / case_daly, 2))  # /case 1: 8760 (365 *24) / Case 2: 52560(365*12*12)

    # print("/ resident 1 / resident 2 / resident 3 / resident 4 / [Health damage cost (USD)]")
    # print(hcost_list)
    # print ("Total Health damage cost: {} USD".format(round(sum(hcost_list),2)))
    return round(sum(hcost_list),2)
    # print("최종 cost")
    # print(round(sum(daly_list)*vsly / case_daly,2))
    # return round(sum(daly_list)*vsly / case_daly,2)

def obj2(spatlist, dayx):
    print("[ #Obj 2. Health impact by noise exposure ]")
    print ("Initial total Health damage cost(방음벽 미설치/최초상태): {} USD".format(spl_init(dayx)))
    k = spl_init(dayx) -spl(dayx, spatlist)
       
    # print("<방음벽 번호 [{}]의 health damage cost 감소량: {} USD>".format(grid_no1[a], round(spl_init(dayx) -spl(dayx, grid_no1[a]),2)))
        
    print("최종 Health damage cost = [{}] - [{}] = [{}] USD".format(round(spl_init(dayx),2), round(k,2), round(spl_init(dayx) - k, 2))) 
    return k
