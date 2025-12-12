import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, LogInfo

def generate_launch_description():
    # 获取包路径（ROS2 标准方法）
    robot_package_dir = get_package_share_directory('robot')
    urdf_path = os.path.join(robot_package_dir, 'urdf', 'robot.urdf')
    rviz_config_path = os.path.join(robot_package_dir, 'urdf.rviz')  # 配置文件路径

    # 打印配置文件路径（用于调试：确认是否找到文件）
    print(f"RViz config path: {rviz_config_path}")
    print(f"RViz config exists: {os.path.exists(rviz_config_path)}")

    # 声明参数（ROS2 推荐显式声明）
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='false',
        description='Use simulation clock if true'
    )

    # 关节状态发布器 GUI（ROS2 包名不变，启动方式调整）
    joint_state_publisher = Node(
        package='joint_state_publisher_gui',
        executable='joint_state_publisher_gui',
        name='joint_state_publisher_gui',
        parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
        output='screen'
    )

    # 机器人状态发布器（解析 URDF）
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'robot_description': open(urdf_path).read()}  # 直接加载 URDF 内容
        ],
        output='screen'
    )

    # RViz2 配置：强制加载配置文件（已保存则自动应用，未保存则提示）
    rviz_args = ['-d', rviz_config_path] if os.path.exists(rviz_config_path) else []
    rviz_actions = [
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=rviz_args,
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            output='screen'
        )
    ]

    # 若配置文件不存在，添加日志提示（终端可见）
    if not os.path.exists(rviz_config_path):
        rviz_actions.insert(0, LogInfo(
            msg=f"\n[WARNING] RViz config file not found at: {rviz_config_path}\n"
                "Please configure RViz manually and save to this path!\n"
                "Steps: File → Save Config As → Select src/robot/urdf.rviz\n"
        ))
    else:
        # 配置文件存在，添加日志确认
        rviz_actions.insert(0, LogInfo(
            msg=f"[INFO] Loading RViz config from: {rviz_config_path}"
        ))

    # 关键修复：静态 TF 发布节点（ROS2 Humble 新参数格式）
    # 依据：https://docs.ros.org/en/humble/Tutorials/Intermediate/TF2/Static-Frame-Publisher.html
    static_tf_publisher = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='map_to_base',
        # 新格式：显式命名参数（支持欧拉角 roll/pitch/yaw 或四元数）
        arguments=[
            '--x', '0.0',          # x 平移（米）
            '--y', '0.0',          # y 平移（米）
            '--z', '0.0',          # z 平移（米）
            '--roll', '0.0',       # 滚转角（弧度）
            '--pitch', '0.0',      # 俯仰角（弧度）
            '--yaw', '0.0',        # 偏航角（弧度）
            '--frame-id', 'map',   # 父坐标系
            '--child-frame-id', 'base_Link'  # 子坐标系
        ],
        output='screen'
    )

    return LaunchDescription([
        use_sim_time_arg,
        joint_state_publisher,
        robot_state_publisher,
        static_tf_publisher,
        *rviz_actions  # 加载 RViz（含日志提示）
    ])

