cmake_minimum_required(VERSION 3.5)
project(robot)

# 设置C++17标准
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 查找ROS 2依赖包
find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(ros_gz_sim REQUIRED)

# 配置头文件目录
include_directories(${PROJECT_SOURCE_DIR}/control)

# 编译gazebo_relay_node节点
add_executable(gazebo_relay_node
  ${PROJECT_SOURCE_DIR}/control/reply.cpp
)

# 链接依赖包
ament_target_dependencies(gazebo_relay_node
  rclcpp
  std_msgs
  ros_gz_sim
)

# 安装节点
install(TARGETS
  gazebo_relay_node
  DESTINATION lib/${PROJECT_NAME}
  PERMISSIONS OWNER_EXECUTE GROUP_EXECUTE WORLD_EXECUTE
)

# 安装功能目录
foreach(dir config launch meshes urdf)
  install(DIRECTORY ${dir}/
    DESTINATION share/${PROJECT_NAME}/${dir}
    PATTERN "CMakeCache.txt;*.git*;*.swp" EXCLUDE
  )
endforeach(dir)

# 编译测试
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()

