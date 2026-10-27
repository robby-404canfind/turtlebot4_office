# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = get_package_share_directory('turtlebot4_office')
    slam_share = get_package_share_directory('slam_toolbox')
    use_sim_time = LaunchConfiguration('use_sim_time')
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('open_rviz', default_value='true'),
        DeclareLaunchArgument('slam_params_file',
                              default_value=os.path.join(share, 'config', 'slam.yaml')),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(slam_share, 'launch', 'online_async_launch.py')),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'slam_params_file': LaunchConfiguration('slam_params_file'),
            }.items(),
        ),
        Node(
            condition=IfCondition(LaunchConfiguration('open_rviz')),
            package='rviz2', executable='rviz2', name='rviz2',
            arguments=['-d', os.path.join(share, 'rviz', 'slam.rviz')],
            parameters=[{'use_sim_time': use_sim_time}], output='screen',
        ),
    ])
