# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    share = get_package_share_directory('turtlebot4_office')
    return LaunchDescription([
        DeclareLaunchArgument('params_file', default_value=os.path.join(share, 'config', 'costmap.yaml')),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(share, 'launch', 'navigation.launch.py')),
            launch_arguments={
                'params_file': LaunchConfiguration('params_file'),
                'use_rviz': LaunchConfiguration('use_rviz'),
                'rviz_config': os.path.join(share, 'rviz', 'costmap.rviz'),
            }.items()),
    ])
