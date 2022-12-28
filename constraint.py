############################################################################################################################
# Borderline constraint: 레이아웃 경계조건
def constraint_border(date_data):
# Facilities
    width = 62
    length = 42
        
    for s in range(len(date_data[0])):
        if date_data[0][s][5] > width-1:                                 #[0][s][5]: facility-number-right coordinate
            print("입력된 [설비] 좌표가 레이아웃 범위를 초과했음: [우측] 경계")
            raise ValueError 
        elif date_data[0][s][3] < 0:                                           #[0][s][3]: facility-number-left coordinate
            print("입력된 [설비] 좌표가 레이아웃 범위를 초과했음: [좌측] 경계")
            raise ValueError
        elif date_data[0][s][6] > length-1:
            print("입력된 [설비] 좌표가 레이아웃 범위를 초과했음: [하단] 경계")
            raise ValueError
        elif date_data[0][s][4] < 0:
            print("입력된 [설비] 좌표가 레이아웃 범위를 초과했음: [상단] 경계")
            raise ValueError
        else:
            pass

# Noise sources
    for s in range(len(date_data[1])):
        if date_data[1][s][1] > width-1:   #1: x // 2: y
            print("입력된 [소음원] 좌표가 레이아웃 범위를 초과했음: [우측] 경계") 
            raise ValueError
        elif date_data[1][s][1] < 0:
            print("입력된 [소음원] 좌표가 레이아웃 범위를 초과했음: [좌측] 경계") 
            raise ValueError    
        elif date_data[1][s][2] > length-1:
            print("입력된 [소음원] 좌표가 레이아웃 범위를 초과했음: [하단] 경계") 
            raise ValueError
        elif date_data[1][s][2] < 0:                         
            print("입력된 [소음원] 좌표가 레이아웃 범위를 초과했음: [상단] 경계") 
            raise ValueError            
        else:
            pass
        
############################################################################################################################
# Function : Check if coordinates are overlapped (bool)
def overlap_check(a):
    return len(a) != len(set(a))

############################################################################################################################
