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
    nav2 = get_package_share_directory('nav2_bringup')
    return LaunchDescription([
        DeclareLaunchArgument('map', default_value=os.path.join(share, 'maps', 'office.yaml')),
        DeclareLaunchArgument('params_file', default_value=os.path.join(share, 'config', 'nav2.yaml')),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_composition', default_value='true'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(nav2, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': LaunchConfiguration('map'), 'params_file': LaunchConfiguration('params_file'),
                'use_sim_time': 'true', 'use_composition': LaunchConfiguration('use_composition'), 'autostart': 'true',
                'use_keepout_zones': 'false', 'use_speed_zones': 'false',
            }.items()),
        Node(package='turtlebot4_office', executable='trajectory_path',
             parameters=[{'use_sim_time': True}]),
        Node(package='rviz2', executable='rviz2', name='rviz2',
             arguments=['-d', os.path.join(share, 'rviz', 'navigation.rviz')],
             parameters=[{'use_sim_time': True}], condition=IfCondition(LaunchConfiguration('use_rviz'))),
    ])
