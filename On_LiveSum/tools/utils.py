import pandas as pd

points_dict = {
    'shot': [ 'shot', "missed", "header", "hits the bar", "goes high", "goal", "blocked", "saved"], 
    'foul':  [ 'foul', "dangerous play", "handball"], 
    'yellow card':  ['yellow card'], 
    'red card': [ "red card", "sent off"], 
    'corner kick' : [ "corner "], 
    'free kick': [ "free ", "penalty"], 
    'offside':  [ 'offside' ],
}

# 分割文本为最小单元
def get_chunk( text, gra = "sentence"):
    if gra == "sentence":
        ret = []
        text_chunk = text.split(". ")
        for item in text_chunk:
            temp = item.strip()
            if temp != "":
                ret.append( temp )
        return ret
    elif gra == "sub_sentence":
        ret_list = []
        text_chunk = text.split(". ")
        for sub_chunk in text_chunk:
            ret_list.extend( sub_chunk.split(", ") )
        ret = []
        for item in ret_list:
            temp = item.strip()
            if temp != "":
                ret.append( temp )
        return ret
    
# 查找所有最小子串
def find_substr( text_, substring):
    positions = []
    start = 0
    while True:
        # 查找子字符串的索引
        pos = text_.find(substring, start)
        if pos == -1:
            break  # 没找到时结束循环
        positions.append(pos)
        start = pos + 1  # 更新起始位置，继续查找下一个位置
    return positions

# 找到文本中距离目标值最近的代码
def find_nearst_team( start_index, line, item ):
    """
    start_index: item的起始位置
    line: 小写
    item：8个field之一
    """
    _left_context = line[ :start_index ].strip().split(" ")
    _right_context = line[ (start_index + len(item)) : ].strip().split(" ")
    _old = [ _left_context, _right_context]
    # 将两个word的队伍名字段作为一起
    _new = [ [], []]
    for i, list_ in enumerate(_old):
        j = 0
        while j<len(list_):
            word = list_[j].lower()
            if "away" in word  and "team" in list_[j+1].lower() :
                _new[i].append( word + " " + list_[j+1])
                
                j += 2
            elif "home" in word and "team" in list_[j+1].lower():
                _new[i].append( word + " " + list_[j+1])
                j += 2
            else:
                _new[i].append( word )
                j+=1
    # 最近的队伍名
    ret = None
    for i in range( min( len(_new[0]), len(_new[1])) ):
        
        left_word, right_word = _new[0][ len(_new[0])-i-1],  _new[1][ i ]
        if " team" in left_word:
            ret = left_word.strip()
            return ret
        elif " team" in right_word:
            ret = right_word.strip()
            return ret

    rest_list = _new[0][i:] if i!=len(_new[0]) else _new[1][i:]
    for i in range(len(rest_list)):
        if " team" in rest_list[i]:
            ret = rest_list[i].strip()
            return ret
    return ret

# 将字典转换为csv保存格式
def to_csv( points_count ):
    data = pd.DataFrame({
        'Team': ['Away Team', 'Home Team'],
        'Goals': [ None, None],
        'Shots': [None, None],
        'Fouls': [None, None],
        'Yellow Cards': [None, None],
        'Red Cards': [None, None],
        'Corner Kicks': [None, None],
        'Free Kicks': [None, None],
        'Offsides': [None, None]
    })
    list_ = "Goals,Shots,Fouls,Yellow Cards,Red Cards,Corner Kicks,Free Kicks,Offsides".split(",")
    for i in range( 8 ):
        data[ list_[i]][0] = points_count['away'][i]
        data[ list_[i]][1] = points_count['home'][i]
    return data