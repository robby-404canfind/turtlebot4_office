#!/usr/bin/env python3
# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
"""Display the controller's trajectory as a standard RViz Path."""
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Path, Trajectory


class TrajectoryPath(Node):
    def __init__(self):
        super().__init__('trajectory_path')
        self.publisher = self.create_publisher(Path, 'local_plan', 10)
        self.subscription = self.create_subscription(
            Trajectory, 'controller_server/optimal_trajectory', self.callback, 10)

    def callback(self, trajectory):
        path = Path()
        path.header = trajectory.header
        for point in trajectory.points:
            pose = PoseStamped()
            pose.header = trajectory.header
            pose.pose = point.pose
            path.poses.append(pose)
        self.publisher.publish(path)


def main():
    rclpy.init()
    node = TrajectoryPath()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
