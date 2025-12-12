import os
import shutil
import re

def get_user_input(prompt, default=None, input_type=str):
    """获取用户输入，支持默认值和类型转换"""
    while True:
        user_input = input(prompt).strip()
        if not user_input and default is not None:
            return default
        try:
            return input_type(user_input)
        except ValueError:
            print(f"输入格式错误，请输入{input_type.__name__}类型！")

def extract_current_params(content):
    """从原文件内容中提取当前参数值（取第一个车轮的参数作为默认值）"""
    current_params = {}

    # ========== 关键修改：匹配新的车轮Gazebo参数结构（包含kp/kd） ==========
    gazebo_pattern = re.compile(
        r'<gazebo>\s*<mu1>(.*?)</mu1>\s*<mu2>(.*?)</mu2>\s*<fdir1>(.*?)</fdir1>\s*<kp>(.*?)</kp>\s*<!--.*?-->\s*<kd>(.*?)</kd>\s*<!--.*?-->\s*<min_depth>(.*?)</min_depth>\s*<rolling_friction>(.*?)</rolling_friction>\s*<!--.*?-->\s*<rotational_friction>(.*?)</rotational_friction>\s*</gazebo>',
        re.DOTALL
    )
    gazebo_matches = gazebo_pattern.findall(content)
    if gazebo_matches:
        # 提取新参数：mu1, mu2, fdir1, kp, kd, min_depth, rolling_friction, rotational_friction
        mu1, mu2, fdir1, kp, kd, min_depth, rolling_friction, rotational_friction = gazebo_matches[0]
        current_params["mu1"] = mu1.strip()
        current_params["mu2"] = mu2.strip()
        current_params["fdir1"] = fdir1.strip()
        current_params["kp"] = kp.strip()
        current_params["kd"] = kd.strip()
        current_params["min_depth"] = min_depth.strip()
        current_params["rolling_friction"] = rolling_friction.strip()
        current_params["rotational_friction"] = rotational_friction.strip()
        print(f"\n【调试】提取到原文件Gazebo参数：{current_params}")
    else:
        print("【警告】未匹配到车轮Gazebo参数块，将使用硬编码默认值")

    # 提取关节动力学参数（damping/friction）
    dynamics_pattern = re.compile(r'<dynamics damping="(.*?)" friction="(.*?)" />')
    dynamics_matches = dynamics_pattern.findall(content)
    if dynamics_matches:
        damping, friction = dynamics_matches[0]  # 取第一个车轮的参数
        current_params["damping"] = damping.strip()
        current_params["friction"] = friction.strip()
        print(f"【调试】提取到原文件动力学参数：damping={damping}, friction={friction}")
    else:
        print("【警告】未匹配到动力学参数块，将使用硬编码默认值")

    return current_params

def main():
    # 原文件和目标文件名称
    original_file = "robot.urdf"
    target_file = "robot.urdf"

    # 检查原文件是否存在
    if not os.path.exists(original_file):
        print(f"错误：当前目录下未找到{original_file}文件！")
        return

    # 读取原文件内容
    try:
        with open(original_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"读取文件失败：{e}")
        return

    # 提取原文件当前参数（作为默认值）
    current_params = extract_current_params(content)
    
    # ========== 更新默认值字典：移除旧参数，添加kp/kd默认值 ==========
    default_hardcode = {
        "mu1": "1.5", "mu2": "0.001", "fdir1": "1 0 0", 
        "kp": "1000000.0", "kd": "10.0", "min_depth": "0.001",
        "rolling_friction": "0", "rotational_friction": "0",
        "damping": "1.0", "friction": "0.0"
    }
    # 仅补充提取失败的参数，已提取的保留原文件值
    for key, val in default_hardcode.items():
        if key not in current_params:
            current_params[key] = val

    print(f"\n【最终默认值】：{current_params}")

    # 处理原文件（重命名/舍弃/保留）
    print("\n=== 原文件处理 ===")
    print("请选择对原robot.urdf的操作：")
    print("1. 重命名（输入新文件名，如old_robot.urdf）")
    print("2. 舍弃（直接删除原文件）")
    print("3. 保留（直接覆盖）")
    choice = get_user_input("输入选项（1/2/3）：", "3", str)

    if choice == "1":
        new_name = get_user_input("输入新文件名：", "old_robot.urdf", str)
        shutil.move(original_file, new_name)
        print(f"原文件已重命名为：{new_name}")
    elif choice == "2":
        os.remove(original_file)
        print("原文件已删除")
    elif choice == "3":
        print("保留原文件（将被新内容覆盖）")
    else:
        print("无效选项，保留原文件")

    # 询问是否修改参数
    print("\n=== 参数修改设置 ===")
    modify_gazebo = get_user_input("是否修改车轮Gazebo物理参数？(y/n)：", "n", str).lower() == "y"
    modify_dynamics = get_user_input("是否修改车轮关节动力学参数？(y/n)：", "n", str).lower() == "y"

    # 存储新参数值（默认值为原文件当前值）
    new_params = {}
    if modify_gazebo:
        print("\n输入Gazebo物理参数（回车保留原文件当前值）：")
        # ========== 仅保留新的Gazebo参数输入 ==========
        new_params["mu1"] = get_user_input(f"mu1（当前值：{current_params['mu1']}）：", current_params["mu1"], str)
        new_params["mu2"] = get_user_input(f"mu2（当前值：{current_params['mu2']}）：", current_params["mu2"], str)
        new_params["fdir1"] = get_user_input(f"fdir1（当前值：{current_params['fdir1']}）：", current_params["fdir1"], str)
        new_params["kp"] = get_user_input(f"kp（刚度，当前值：{current_params['kp']}）：", current_params["kp"], str)
        new_params["kd"] = get_user_input(f"kd（阻尼，当前值：{current_params['kd']}）：", current_params["kd"], str)
        new_params["min_depth"] = get_user_input(f"min_depth（当前值：{current_params['min_depth']}）：", current_params["min_depth"], str)
        new_params["rolling_friction"] = get_user_input(f"rolling_friction（当前值：{current_params['rolling_friction']}）：", current_params["rolling_friction"], str)
        new_params["rotational_friction"] = get_user_input(f"rotational_friction（当前值：{current_params['rotational_friction']}）：", current_params["rotational_friction"], str)

    if modify_dynamics:
        print("\n输入关节动力学参数（回车保留原文件当前值）：")
        new_params["damping"] = get_user_input(f"damping（关节阻尼，当前值：{current_params['damping']}）：", current_params["damping"], str)
        new_params["friction"] = get_user_input(f"friction（关节摩擦，当前值：{current_params['friction']}）：", current_params["friction"], str)

    # ========== 替换文件内容 ==========
    # 替换Gazebo物理参数块（所有车轮统一修改）
    if modify_gazebo:
        # 匹配新的Gazebo参数结构，用于替换
        gazebo_pattern = re.compile(
            r'(<gazebo>\s*<mu1>).*?(</mu1>\s*<mu2>).*?(</mu2>\s*<fdir1>).*?(</fdir1>\s*<kp>).*?(</kp>\s*<!--.*?-->\s*<kd>).*?(</kd>\s*<!--.*?-->\s*<min_depth>).*?(</min_depth>\s*<rolling_friction>).*?(</rolling_friction>\s*<!--.*?-->\s*<rotational_friction>).*?(</rotational_friction>\s*</gazebo>)',
            re.DOTALL
        )
        # 构造替换字符串，按新参数顺序填充
        replace_str = (
            r'\g<1>{mu1}\g<2>{mu2}\g<3>{fdir1}\g<4>{kp}\g<5>{kd}\g<6>{min_depth}\g<7>{rolling_friction}\g<8>{rotational_friction}\g<9>'
        ).format(**new_params)
        content = gazebo_pattern.sub(replace_str, content)

    # 替换关节动力学参数（所有车轮统一修改）
    if modify_dynamics:
        dynamics_pattern = re.compile(
            r'(<dynamics damping=").*?(" friction=").*?(" />)'
        )
        replace_str = r'\g<1>{damping}\g<2>{friction}\g<3>'.format(**new_params)
        content = dynamics_pattern.sub(replace_str, content)

    # 生成新文件
    try:
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n成功生成新的{target_file}文件！")
    except Exception as e:
        print(f"写入文件失败：{e}")
        return

if __name__ == "__main__":
    print("=== URDF文件参数修改工具（适配ROS2+Gazebo Fortress） ===")
    main()
    input("\n按Enter键退出...")

