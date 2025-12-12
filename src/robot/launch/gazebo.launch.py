import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import (
    IncludeLaunchDescription,
    DeclareLaunchArgument,
    SetEnvironmentVariable
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution

def generate_launch_description():
    # 获取功能包共享目录路径，用于拼接各类配置/模型文件路径
    robot_package_dir = get_package_share_directory('robot')
    # 拼接URDF文件路径，定义机器人模型结构与关节信息
    urdf_path = os.path.join(robot_package_dir, 'urdf', 'robot.urdf')
    # 拼接Gazebo仿真世界文件路径，加载自定义仿真环境
    world_path = os.path.join(robot_package_dir, 'config', 'world.world')
    # 拼接控制器管理器配置文件（仅声明控制器类型，由Gazebo插件内置加载）
    controller_manager_config = os.path.join(robot_package_dir, 'config', 'controller_manager.yaml')
    # 拼接前向控制器参数文件（关节列表、接口类型等参数）
    forward_controller_config = os.path.join(robot_package_dir, 'config', 'forward_controller_params.yaml')
    # 拼接机器人meshes目录路径，确保Gazebo加载模型网格文件
    meshes_dir = os.path.join(robot_package_dir, 'meshes')

    # 声明仿真时钟参数，默认使用Gazebo仿真时间
    use_sim_time_arg = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation clock instead of system clock'
    )

    # 设置GZ_SIM_SYSTEM_PLUGIN_PATH，确保Gazebo找到ros_gz_control插件
    set_gazebo_plugin_path = SetEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_PATH',
        value=[
            os.pathsep,
            '/opt/ros/humble/lib',
            os.environ.get('GZ_SIM_SYSTEM_PLUGIN_PATH', '')
        ]
    )

    # 设置GZ_SIM_RESOURCE_PATH，确保Gazebo找到机器人模型资源
    set_gazebo_resource_path = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH',
        value=[
            os.pathsep,
            meshes_dir,
            robot_package_dir,
            os.environ.get('GZ_SIM_RESOURCE_PATH', '')
        ]
    )

    # 启动Gazebo仿真环境（加载自定义世界或空世界）
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            ])
        ]),
        launch_arguments={
            'gz_args': f'-r {world_path}' if os.path.exists(world_path) else '-r empty.sdf',
            'verbose': 'true'  # 开启详细日志，便于调试
        }.items()
    )

    # 发布机器人URDF模型与状态信息（Gazebo插件依赖此节点获取模型描述）
    robot_description = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {'use_sim_time': LaunchConfiguration('use_sim_time')},
            {'robot_description': open(urdf_path).read()}  # 读取URDF文件内容
        ],
        output='screen'
    )

    # 在Gazebo中生成机器人模型（z轴偏移0.05避免物理穿透）
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description',  # 从话题获取模型描述
            '-name', 'robot',               # 模型名称
            '-z', '0.05'                    # z轴微小偏移
        ],
        output='screen'
    )

    # 启动关节状态广播器（由Gazebo内置控制器管理器管理）
    joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',  # 指向Gazebo内置的控制器管理器
            '--controller-manager-timeout', '10'            # 超时保护，避免启动时序错误
        ],
        output='screen'
    )

    # 启动前向控制器（显式加载独立参数文件，适配Humble参数读取逻辑）
    forward_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'forward_controller',
            '--controller-manager', '/controller_manager',
            '--param-file', forward_controller_config,  # 加载控制器专属参数
            '--controller-manager-timeout', '10'
        ],
        output='screen'
    )

    # 节点启动顺序：先配置环境→启动仿真→加载模型→启动控制器
    return LaunchDescription([
        set_gazebo_plugin_path,
        set_gazebo_resource_path,
        use_sim_time_arg,
        gazebo_launch,
        robot_description,
        spawn_robot,
        joint_state_broadcaster,
        forward_controller
    ])
