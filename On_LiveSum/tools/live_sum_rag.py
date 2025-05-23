import os
import sys
from wayne_utils import save_data, load_data
from .utils import to_csv, find_substr, get_chunk, find_nearst_team, points_dict
from tqdm import tqdm
import re

score_instruction = """You are an information extraction expert, please extract the football game final scores from context.
"""
score_input = """You should only return the scores of home team vs away team in format like "1-2" without other word.
Context: {Context}
Question: What is the final scores?
Answer:
"""

other_instruction = """You are an information extraction expert, please judge whether the home or away team has scored at a certain technical point according to the context.
You should only return 'yes' or 'no'.
"""
other_input = """Context: {Context}
Question: Does the {Team} have a {Field}?
Answer:
"""

# 处理单个文本: RAG
def single_count_RAG_v1( text ):
    prompt_list = {}
    #（1）抽取goal的context
    text_chunk_sentence = get_chunk( text )
    final_score_context = text_chunk_sentence[-2:]
    prompt_list["final score"] = [score_instruction + score_input.format( Context = final_score_context)]

    #（2）抽取其他7个field的context
    text_chunk = get_chunk( text, gra = "sub_sentence")
    points = ['goal', 'shot', 'foul', 'yellow card', 'red card', 'corner kick', 'free kick', 'offside']
    for chunk in text_chunk:
        # 遍历每个子句
        line = chunk.lower()
        for item in points[1:]:
            # 遍历每个字段
            positions = find_substr( line, item)            # 找到该字段在该字句中的所有位置
            """v2
            if len( positions ) > 0:
                if item in ["corner", "free"]:
                    item = item + " kick"
                for team_name in [ "away team", "home team"]:
                    if team_name in line:                           # 只要该句话中有队名和字段就问
                        key = f"{team_name},{item}"
                        if key not in prompt_list:
                            prompt_list[key] = []
                        prompt_list[key].append( other_instruction + other_input.format( Context=chunk, Team=team_name, Field=item))
            """

            """v1"""
            for start_index in positions:                                        # 对找到的所有位置进行遍历
                team_str = find_nearst_team( start_index, line, item )                  #  找到离这个字段位置最近的Team名，为其构建Prompt
                if team_str == None:
                    continue
                for team_name in [ "away team", "home team"]:
                    if team_name in team_str:
                        key = f"{team_name},{item}"
                        if key not in prompt_list:
                            prompt_list[key] = []
                        prompt_list[key].append( other_instruction + other_input.format( Context=chunk, Team=team_name, Field=item))
                    
    final_list_key = []
    final_list_prompt = []
    for key in prompt_list.keys():
        for prompt in prompt_list[key]:
            final_list_key.append( key )
            final_list_prompt.append( prompt )
    

    return {
        "key": final_list_key,
        "prompt": final_list_prompt
    }

teams = ["home team", "away team"]
def single_count_RAG( text ):
    prompt_list = {}
    #（1）抽取goal的context
    text_chunk = get_chunk( text )
    final_score_context = text_chunk[-2:]
    prompt_list["final score"] = [score_instruction + score_input.format( Context = final_score_context)]

    #（2）抽取其他7个field的context
    text_chunk = get_chunk( text )
    for sub_index in range(len(text_chunk)):
        line = text_chunk[sub_index].lower()
        for team_name in teams:
            if team_name in line:
                for key in points_dict.keys():
                    for point in points_dict[key]:
                        if point in line:
                            _key = f"{team_name},{key}"
                            if _key not in prompt_list:
                                prompt_list[_key] = []
                            prompt_list[_key].append( other_instruction + other_input.format( Context=text_chunk[sub_index], Team=team_name, Field=key))
                            break
    final_list_key = []
    final_list_prompt = []
    for key in prompt_list.keys():
        for prompt in prompt_list[key]:
            final_list_key.append( key )
            final_list_prompt.append( prompt )
    

    return {
        "key": final_list_key,
        "prompt": final_list_prompt
    }

def get_prompt( test_list, save_path):
    prompt_list = []
    for i in tqdm( range( len(test_list) ), desc="Processing texts", unit="file"):
        text = test_list[i]["text"]
        id = test_list[i]["id"]
        prompt_list.append( single_count_RAG( text ) )

    save_data( prompt_list, os.path.join(save_path, "prompt_list.pickle") )
    only_prompt = []
    for i in range( len(prompt_list)):
        only_prompt.append( prompt_list[i]['prompt'])
    save_data( only_prompt, os.path.join(save_path, "prompt_list_only.pickle"))



# 后处理
points = ['goal', 'shot', 'foul', 'yellow card', 'red card', 'corner kick', 'free kick', 'offside']
map_ = {}
for i, key in enumerate(points):
    map_[key] = i
    
def judge_bool( key ):
    if "yes" in key.lower():
        return True
    elif "no" in key.lower():
        return False
    return False

    
def parse_scores( line ):
    score_pattern = re.compile(r'\d+-\d+')
    match = score_pattern.search(line)
    if match:
        return match.group().split("-")
    else:
        return None


def single_doc_postprocess( predicts, key_list, index):
    points_count = {
        "home": [ 0 for _ in range(8) ],
        "away": [ 0 for _ in range(8) ],
    }
    if len(key_list) != len(predicts):
        raise Exception( f"文档{index}的key和预测长度不一致 {len(key_list)}, {len(predicts)}" )
    
    for j in range( len(key_list)):
        key = key_list[j]
        predict = predicts[j]
        # 先单独处理score
        if key == "final score":
            scores = parse_scores( predict )
            if scores!=None:
                home_score, away_score = scores[0], scores[1]
                points_count[ "home" ][0] = int(home_score)
                points_count[ "away" ][0] = int(away_score)
        # 再一起处理其他7个
        else:
            if judge_bool( predict ):
                # 如果是肯定回答
                team_name, item = key.split(",")
                if team_name == "away team":
                    points_count["away"][ map_[item]] += 1
                elif team_name == "home team":
                    points_count["home"][ map_[item]] += 1
    return points_count



def post_process( save_path, test_data_path):
    prompt_path = os.path.join(save_path, "prompt_list.pickle")
    predict_path = os.path.join(save_path, "predict_lists_rule.pickle")
    prompt_list = load_data( prompt_path, "pickle")
    predict_list = load_data( predict_path, "pickle")
    data_list = load_data( test_data_path, "json")

    points = ['goal', 'shot', 'foul', 'yellow card', 'red card', 'corner kick', 'free kick', 'offside']
    map_ = {}
    for i, key in enumerate(points):
        map_[key] = i
    
    # 遍历处理每份文档的预测结果
    for i in range( len(prompt_list)):
        points_count = single_doc_postprocess( predict_list[i], prompt_list[i]['key'], i)
        _save_path = os.path.join( save_path, f"predict/{data_list[i]['id']}.csv")
        csv_format = to_csv( points_count )
        save_data( csv_format, _save_path )




if __name__ == "__main__":
    
    _ROOT_PATH = "workspace/TKGT"
    test_path = os.path.join( _ROOT_PATH, "data/LiveSum/test.json")
    save_path = 'workspace/TKGT/test/LiveSum/v2'
    test_list = load_data( test_path, "json")           # 754
    get_prompt( test_list, save_path )
    '''
    save_path = "workspace/TKGT/test/LiveSum/v1"
    test_data_path = "workspace/TKGT/data/LiveSum/test.json"
    post_process( save_path, test_data_path)'''