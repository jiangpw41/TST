import argparse
import json
import os
from io import StringIO

import numpy as np
import pandas as pd

columns = [
    "Team",
    "Goals",
    "Shots",
    "Fouls",
    "Yellow Cards",
    "Red Cards",
    "Corner Kicks",
    "Free Kicks",
    "Offsides",
]

difficulty = {
    "Goals": 0,
    "Red Cards": 0,
    "Yellow Cards": 1,
    "Corner Kicks": 1,
    "Free Kicks": 1,
    "Offsides": 1,
    "Shots": 2,
    "Fouls": 2,
}

cnt0 = [0, 0, 0, 0]                     # 统计各个难度分别有多少
for i in difficulty.keys():
    cnt0[difficulty[i]] += 1


def Evaluate(data_dir, output_dir):
    with open(os.path.join(data_dir, "test.json"), "r") as f:                   # 加载标签数据
        test_file = json.load(f)
    all_ground_truth = {}
    for inst in test_file:                                                      # 加载目录下所有csv预测文件
        all_ground_truth[inst["id"]] = pd.read_csv(
            StringIO(inst["table"].replace("<NEWLINE>", "\n"))
        )
    result = []
    qq = os.listdir(output_dir)                                                 # qq所有代表所有文件名（id为文件名）
    qq.sort()
    error_count = [ 0, 0, 0]                                                    # 三个档次的错误统计
    for file_name in qq:
        if ".csv" in file_name:
            idx = int(file_name.split(".")[0])
            try:
                output = pd.read_csv(os.path.join(output_dir, file_name))           # 读取预测数据CSV
                ground_truth = all_ground_truth[idx]                                # 读取label数据
                res = []
                correct_col = 0
                mses = [0, 0, 0, 0]
                maes = [0, 0, 0, 0]
                accs = [0, 0, 0, 0]
                flag=0
                for column in columns[1:]:                                                  #遍历八个字段
                    output_col = list(output[column])                                           # 获取输出中该字段主客队数据
                    output_col = np.array(output_col)
                    output_col = [o if type(o) != np.str_ else 0 for o in output_col]
                    output_col = np.array(output_col)
                    output_col = np.nan_to_num(output_col)
                    ground_truth_col = list(ground_truth[column])                               # 获取标签中该字段主客队数据
                    ground_truth_col = np.array(ground_truth_col)
                    ground_truth_col = [
                        o if type(o) != np.str_ else 0 for o in ground_truth_col
                    ]
                    ground_truth_col = np.array(ground_truth_col)
                    ground_truth_col = np.nan_to_num(ground_truth_col)

                    eid = difficulty[column]                                                    # 获取该字段难度等级并填表
                    mses[eid] += np.square(output_col - ground_truth_col).sum()
                    maes[eid] += np.abs(output_col - ground_truth_col).sum()
                    accs[eid] += (output_col == ground_truth_col).sum()
                    mses[3] += np.square(output_col - ground_truth_col).sum()
                    maes[3] += np.abs(output_col - ground_truth_col).sum()
                    accs[3] += (output_col == ground_truth_col).sum()
                    if output_col[0] != ground_truth_col[0]:                                    # 分别查看主客队分数是否一致，否则在该难度上+1错误数
                        error_count[ difficulty[column] ] +=1
                    if output_col[1] != ground_truth_col[1]:
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
                        (mses[3] / 16) ** 0.5,
                        (maes[3] / 16),
                        100 - (accs[3] / 16) * 100,
                    ]
                )
            except Exception as e:
                print(line)
                raise ValueError(e)
            result.append(res)
    print("test {} tables for {}".format(len(result), output_dir))

    
    easy_er = error_count[0]*100/(len(qq)*4)        # 4和8的来源：首先每个文件都有主客队数据，因此总比较对数为数据集大小的2倍；此外，三个难度的字段数分别为2：4：2，因此三个难度在整个数据集中的数量需要分别乘以2后乘以总长度
    med_er = error_count[1]*100/(len(qq)*8)
    hard_er = error_count[2]*100/(len(qq)*4)
    ave_er = ( error_count[0] + error_count[1] + error_count[2] ) * 100 /( len(qq)*16 )
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
    result = Evaluate( "workspaceCounter_Agent/data/LiveSum/data", 
                      "workspaceCounter_Agent/data/LiveSum/data/predicts")
    print(result.describe().loc["mean"])
    pass
