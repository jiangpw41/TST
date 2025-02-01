import argparse
import json
import os
from io import StringIO

import numpy as np
import pandas as pd

import numpy as np
import pandas as pd

columns = [
    "法院",
    "原告",
    "被告",

    "法院裁定_借款凭证",
    "法院裁定_约定的借款金额",
    "法院裁定_约定的还款日期或借款期限",
    "法院裁定_约定的利息",
    "法院裁定_约定的逾期利息",
    "法院裁定_约定的违约金",

    "原告诉称_借款凭证",
    "原告诉称_约定的借款金额",
    "原告诉称_约定的还款日期或借款期限",
    "原告诉称_约定的利息",
    "原告诉称_约定的逾期利息",
    "原告诉称_约定的违约金",
]

difficulty = {
    "法院": 0,
    "原告": 0,
    "被告": 0,

    "法院裁定_借款凭证": 2,
    "法院裁定_约定的借款金额": 2,
    "法院裁定_约定的还款日期或借款期限": 2,
    "法院裁定_约定的利息": 1,
    "法院裁定_约定的逾期利息": 1,
    "法院裁定_约定的违约金": 1,

    "原告诉称_借款凭证": 2,
    "原告诉称_约定的借款金额": 2,
    "原告诉称_约定的还款日期或借款期限": 2,
    "原告诉称_约定的利息": 1,
    "原告诉称_约定的逾期利息": 1,
    "原告诉称_约定的违约金": 1,
}

cnt0 = [0, 0, 0, 0]                     # 统计各个难度分别有多少
for i in difficulty.keys():
    cnt0[difficulty[i]] += 1
    cnt0[3] += 1

def Eval( predict_count_list, label_count_list ):
    error_count = [ 0, 0, 0]                                                    # 三个档次的错误统计
    result = []
    for i in range( len(predict_count_list)):
        _predict = predict_count_list[i]
        _label = label_count_list[i]

        mses = [0, 0, 0, 0]
        maes = [0, 0, 0, 0]
        accs = [0, 0, 0, 0]

        res = []
        for column in columns:
            predict_value = _predict[column]
            label_value = _label[column]
            eid = difficulty[column]

            _mse = np.square(predict_value - label_value)
            _mae = np.abs(predict_value - label_value)
            _acc = (predict_value == label_value)
            mses[eid] += _mse
            maes[eid] += _mae
            accs[eid] += _acc
            mses[3] += _mse
            maes[3] += _mae
            accs[3] += _acc
            if predict_value != label_value:
                error_count[ difficulty[column] ] +=1
            
        res.extend(
            [
                (mses[0] / (cnt0[0] * 2)) ** 0.5,
                (maes[0] / (cnt0[0] * 2)),
                100 - (accs[0] / (cnt0[0] * 2)) * 100,
                (mses[1] / (cnt0[1] * 2)) ** 0.5,
                (maes[1] / (cnt0[1] * 2)),
                100 - (accs[1] / (cnt0[1] * 2)) * 100,
                (mses[2] / (cnt0[2] * 2)) ** 0.5,
                (maes[2] / (cnt0[2] * 2)),
                100 - (accs[2] / (cnt0[2] * 2)) * 100,
                (mses[3] / (cnt0[3] * 2)) ** 0.5,
                (maes[3] / (cnt0[3] * 2)),
                100 - (accs[3] / (cnt0[3] * 2)) * 100,
            ]
        )

        result.append(res)
    print("test {} tables for {}".format(len(result), "sss"))

        
    easy_er = error_count[0]*100/(len(label_count_list)*3)        # 4和8的来源：首先每个文件都有主客队数据，因此总比较对数为数据集大小的2倍；此外，三个难度的字段数分别为2：4：2，因此三个难度在整个数据集中的数量需要分别乘以2后乘以总长度
    med_er = error_count[1]*100/(len(label_count_list)*6)
    hard_er = error_count[2]*100/(len(label_count_list)*6)
    ave_er = ( error_count[0] + error_count[1] + error_count[2] ) * 100 /( len(label_count_list)*15 )
    error_rate = {
        "Easy_ER": easy_er,
        "Med_ER": med_er,
        "Hard_ER": hard_er,
        "Ave_ER": ave_er,
    }

    print( f"Error rate = {easy_er} {med_er} {hard_er} {ave_er}")
    return pd.DataFrame(
        result,
        columns=[
            "Easy-RMSE",
            "Easy-MAE",
            "Easy-EM",
            "Medium-RMSE",
            "Medium-MAE",
            "Medium-EM",
            "Hard-RMSE",
            "Hard-MAE",
            "Hard-EM",
            "AVG-RMSE",
            "AVG-MAE",
            "AVG-EM",
        ],
    ), error_rate


if __name__ == "__main__":
    """
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data", type=str, required=True, help="Path to the data folder"
    )
    parser.add_argument(
        "--output", type=str, required=True, help="Path to the output folder"
    )
    args = parser.parse_args()

    result = evaluate(args.data, args.output)
    """
    prefix_list = []
    for entity in [ "法院", "原告", "被告"]:
        for field in [ "姓名名称", "借款凭证", "约定的借款金额", "约定的还款日期或借款期限", "约定的利息", "约定的逾期利息", "约定的违约金"]:
            if entity == "被告" and field != "姓名名称":
                continue
            if field == "姓名名称":
                prefix_list.append( entity )
            else:
                pre = "法院裁定_" if entity == "法院" else "原告诉称_"
                prefix_list.append( pre+ field)
    prefix_list
    from wayne_utils import load_data, save_data
    version_dir = "/home/jiangpeiwen2/jiangpeiwen2/projects/TKGT/test/CPL_dynamic/v1"
    _ROOT_PATH = "/home/jiangpeiwen2/jiangpeiwen2/projects/TKGT"

    def get_number( line, prompt):
        if "：[]" in prompt:
            return 0
        for i in range( 6):
            if str(i) in line:
                return i
        return 0
    model_name = 'CPL_dynamic_counter_Chinese-Mistral-7B-Instruct-v0.1-3epoch_hybrid_rag'
    predict_list = load_data( os.path.join( version_dir, f"counter_predict_list_{model_name}.pickle"), "pickle")
    prompt_list = load_data( os.path.join( version_dir, "counter_prompt_list.pickle"), "pickle")    # 111
    label_count_list = load_data( os.path.join( _ROOT_PATH, "evaluation/CountCPL/label_count_list_test.json"), "json")
    predict_count_list = []
    for i in range(len(predict_list)):
        temp_dict = {}
        predicts = predict_list[i]
        prompts = prompt_list[i]
        if len(predicts) != len(prefix_list):
            raise Exception( f"预测结果长度不对{len(predicts)}")
        for j in range( len(predicts)):
            temp_dict[prefix_list[j]] = get_number( predicts[j], prompts[j] )
        predict_count_list.append( temp_dict )
    save_data( predict_count_list, os.path.join( version_dir, f"counter_predict_list_final_{model_name}.pickle"))
    
    aadf, error_rate = Eval( predict_count_list, label_count_list )
    pass
