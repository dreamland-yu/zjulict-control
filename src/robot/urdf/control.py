import os
import sys
import signal
import subprocess

def get_user_input(prompt, default=None, input_type=float):
    """获取用户输入，支持默认值和类型转换"""
    while True:
        try:
            user_input = input(prompt).strip()
            if not user_input and default is not None:
                return default
            return input_type(user_input)
        except ValueError:
            print(f"输入错误！请输入{input_type.__name__}类型数值（如 0.1、1.0）")

def generate_command_data(mode, speed):
    """根据运动模式生成data数组（严格匹配你的麦轮控制逻辑）"""
    # ========== 核心修正：按你的逻辑映射车轮数值 ==========
    mode_mapping = {
        1: [speed, -speed, -speed, speed, 0, 0],    # 前进 (+ - - +)
        2: [-speed, speed, speed, -speed, 0, 0],    # 后退 (- + + -)
        3: [speed, speed, speed, speed, 0, 0],      # 原地正转 (++++）
        4: [-speed, -speed, -speed, -speed, 0, 0],  # 原地反转 (----)
        5: [-speed, -speed, speed, speed, 0, 0],    # 左移 (--++)
        6: [speed, speed, -speed, -speed, 0, 0],    # 右移 (++--)
        7: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]          # 停止
    }
    return mode_mapping.get(mode, [0.0, 0.0, 0.0, 0.0, 0.0, 0.0])

def run_ros2_command(data_list):
    """执行ros2 topic pub命令，屏蔽所有输出"""
    # 正确的f-string写法：join操作完整包裹在{}中
    cmd = (
        f"ros2 topic pub -r 1 /forward_controller/commands std_msgs/msg/Float64MultiArray "
        f'"data: [{", ".join(map(str, data_list))}]" 2>/dev/null | grep "xxx_never_exist_xxx"'
    )
    print(f"\n=== 执行命令（按 Ctrl+C 停止发布）===")
    print(f"命令（已屏蔽输出）：{cmd.split(' 2>/dev/null')[0]}")
    
    # 执行命令（check=False避免grep返回1触发错误）
    try:
        subprocess.run(cmd, shell=True, check=False)
    except KeyboardInterrupt:
        print("\n\n=== 已停止发布控制指令 ===")
    except Exception as e:
        print(f"\n命令执行异常：{e}")

def main():
    print("=== ROS2 麦轮快捷控制工具（匹配你的控制逻辑）===")
    print("==== 预设运动模式（车轮数值对应）====")
    print("1. 前进    (+ - - +)    2. 后退    (- + + -)")
    print("3. 原地正转 (++++）    4. 原地反转 (----)")
    print("5. 左移     (--++)      6. 右移     (++--)")
    print("7. 停止     (0 0 0 0)   8. 自定义车轮参数")
    
    # 选择模式
    mode = get_user_input("\n请选择模式（1-8）：", 1, int)
    while mode not in range(1, 9):
        mode = get_user_input("无效选项！请输入1-8：", 1, int)
    
    # 生成data数组
    if mode in range(1, 8):
        # 预设模式：输入1个速度值
        speed = get_user_input(f"\n输入运动速度（如0.1、1.0）：", 0.1, float)
        data_list = generate_command_data(mode, speed)
    else:
        # 自定义模式：输入4个车轮数值
        print("\n输入4个车轮的控制数值（回车使用默认值0.0）：")
        w1 = get_user_input("车轮1：", 0.0, float)
        w2 = get_user_input("车轮2：", 0.0, float)
        w3 = get_user_input("车轮3：", 0.0, float)
        w4 = get_user_input("车轮4：", 0.0, float)
        data_list = [w1, w2, w3, w4, 0.0, 0.0]
    
    # 执行ROS2命令
    run_ros2_command(data_list)

if __name__ == "__main__":
    # 捕获Ctrl+C信号，优雅退出
    signal.signal(signal.SIGINT, lambda sig, frame: print("\n=== 程序已退出 ===") or sys.exit(0))
    main()

