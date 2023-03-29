import json

# タスク定義


def define_task(task_type):

    # パラメータ
    with open("param.json") as f:
        param = json.load(f)

    rest_keep_time = param["monitor"]["do_task"]["pre_task"]["rest_keep_time"]
    repaet_num = param["monitor"]["do_task"]["pre_task"]["repeat_num"]
    pre_task = [
        ["rest", rest_keep_time]
    ]*repaet_num

    if task_type == "fing_stretch":
        paper_keep_time = param["monitor"]["do_task"][task_type]["paper_keep_time"]
        rest_keep_time = param["monitor"]["do_task"][task_type]["rest_keep_time"]
        repeat_num = param["monitor"]["do_task"][task_type]["repeat_num"]
        task = [
            ["paper", paper_keep_time],
            ["rest", rest_keep_time]
        ]*repeat_num

    elif task_type == "fing_flexion":
        rock_keep_time = param["monitor"]["do_task"][task_type]["rock_keep_time"]
        rest_keep_time = param["monitor"]["do_task"][task_type]["rest_keep_time"]
        repeat_num = param["monitor"]["do_task"][task_type]["repeat_num"]
        task = [
            ["rock", rock_keep_time],
            ["rest", rest_keep_time]
        ]*repeat_num

    elif task_type == "bbt":
        paper_keep_time = param["monitor"]["do_task"][task_type]["paper_keep_time"]
        rock_keep_time = param["monitor"]["do_task"][task_type]["rock_keep_time"]
        rest_keep_time = param["monitor"]["do_task"][task_type]["rest_keep_time"]
        repeat_num = param["monitor"]["do_task"][task_type]["repeat_num"]
        task = [
            ["rock", rock_keep_time],
            ["paper", paper_keep_time],
            ["rest", rest_keep_time]
        ]*repeat_num

    elif task_type == "test":
        paper_keep_time = param["monitor"]["do_task"][task_type]["paper_keep_time"]
        rock_keep_time = param["monitor"]["do_task"][task_type]["rock_keep_time"]
        repeat_num = param["monitor"]["do_task"][task_type]["repeat_num"]
        task = [
            ["rock", paper_keep_time],
            ["paper", rock_keep_time]
        ]*repeat_num

    else:
        task_type_list = param["monitor"]["do_task"].keys()
        task_type_txt = ', '.join(task_type_list)
        raise KeyError(f"taskType must be [ {task_type_txt} ]")

    return pre_task, task
