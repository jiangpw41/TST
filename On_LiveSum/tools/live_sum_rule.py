from wayne_utils import load_data, save_data
import os
import pandas as pd
from tqdm import tqdm
from .utils import to_csv, find_substr, get_chunk, find_nearst_team, points_dict



# 处理单个文本
def single_count_v1( text ):
    text_chunk = get_chunk( text )
    points = ['goal', 'shot', 'foul', 'yellow card', 'red card', 'corner kick', 'free kick', 'offside']
    map_ = {}
    for i, key in enumerate(points):
        map_[key] = i
    points_count = {
        "home": [ 0 for _ in range(8) ],
        "away": [ 0 for _ in range(8) ],
    }
    # 遍历每个子串并小写化
    for chunk in text_chunk:
        line = chunk.lower()
        # 遍历8个字段
        for item in points:
            positions = find_substr( line, item)                                 # 在子串中查找该字段的所有位置
            """find_nearst_team可以被替换"""
            for start_index in positions:                                        # 对找到的所有位置进行遍历
                team_str = find_nearst_team( start_index, line, item )                  #  找到离这个字段位置最近的Team名，为其+1
                if team_str == None:
                    continue
                if "away team" in team_str:
                    points_count["away"][ map_[item]] += 1
                elif "home team" in team_str:
                    points_count["home"][ map_[item]] += 1
    
    return points_count

def single_count( text ):
    text_chunk = get_chunk( text )
    
    map_ = {}

    key_list = list( points_dict.keys( ))
    for i, key in enumerate(key_list):
        map_[key] = i
    points_count = {
        "home": [ 0 for _ in range(8) ],
        "away": [ 0 for _ in range(8) ],
    }
    # 遍历每个子串并小写化
    for chunk in text_chunk:
        line = chunk.lower()
        # 遍历8个字段
        for key in points_dict:
            for item in points_dict[key]:
                positions = find_substr( line, item)                                 # 在子串中查找该字段的所有位置
                """find_nearst_team可以被替换"""
                '''for start_index in positions:                                        # 对找到的所有位置进行遍历
                    team_str = find_nearst_team( start_index, line, item )                  #  找到离这个字段位置最近的Team名，为其+1
                    if team_str == None:
                        continue
                    if "away team" in team_str:
                        points_count["away"][ map_[key]] += 1
                    elif "home team" in team_str:
                        points_count["home"][ map_[key]] += 1'''
                if len( positions )>0:
                    for team_name in [ "away team", "home team"]:
                        if team_name in line:
                            _name = "away" if "away" in team_name else "home"
                            points_count[_name][ map_[key]] += 1
    
    return points_count

# 主文件
def main_rule( test_list, _OUTPUT_PATH):
    for i in tqdm( range( len(test_list) ), desc="Processing texts", unit="file"):
        text = test_list[i]["text"]
        id = test_list[i]["id"]
        save_path = os.path.join( _OUTPUT_PATH, f"predict/{id}.csv")
        points_count = single_count( text )
        csv_format = to_csv( points_count )
        save_data( csv_format, save_path )

"""
Error rate = 42.738726790450926 37.78183023872679 84.88063660477454
Easy-RMSE       1.616042
Easy-MAE        1.007958
Easy-EM        42.738727
Medium-RMSE     1.109628
Medium-MAE      0.626824
Medium-EM      37.781830
Hard-RMSE       3.419160
Hard-MAE        2.724469
Hard-EM        84.880637
AVG-RMSE        2.122795
AVG-MAE         1.246519
AVG-EM         50.795756
Name: mean, dtype: float64
"""