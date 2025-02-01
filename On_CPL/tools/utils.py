
# 切片
def chunk_sentence( texts:list ):
    ret = []
    for line in texts:
        temps = line.split("。")
        for temp in temps:
            if temp.strip() != "":
                ret.append( temp.strip()+"。" )
    return ret



def get_all_evidence_name( label_test_table ):
    new_list = []
    names = []
    for index in range(len(label_test_table)):
        for item in label_test_table[index]:
            if "借款凭证的名称" in item[1] and item[2] not in names:
                if '2012-10-07 00:00:00' == item[2]:
                    print(index)
                names.append( item[2] )
    return names


# 返回所有没有该对象、该字段的文档编号
def get_no_value_field( label_test_table, entity, field):
    no_evidence = []
    for i in range( len(label_test_table)):
        flag = 0
        for item in label_test_table[i]:
            if item[0]==entity and field in item[1]:
                flag = 1
                break

        if flag == 0:
            no_evidence.append( i )
        label_test_table[ 146 ]
    return no_evidence