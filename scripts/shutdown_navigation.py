#!/usr/bin/env python3
# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
"""Request an orderly lifecycle shutdown while the simulator clock is alive."""
import json
import rclpy
from nav2_msgs.srv import ManageLifecycleNodes

rclpy.init()
node=rclpy.create_node('turtlebot4_shutdown_navigation')
try:
    client=node.create_client(ManageLifecycleNodes,'lifecycle_manager_nav2/manage_nodes')
    if not client.wait_for_service(timeout_sec=8.):
        raise RuntimeError('Nav2 lifecycle manager unavailable')
    request=ManageLifecycleNodes.Request();request.command=ManageLifecycleNodes.Request.SHUTDOWN
    future=client.call_async(request)
    rclpy.spin_until_future_complete(node,future,timeout_sec=15.)
    if not future.done() or future.result() is None or not future.result().success:
        raise RuntimeError('Nav2 lifecycle shutdown failed or timed out')
    print(json.dumps({'success':True,'command':'SHUTDOWN'}))
finally:
    node.destroy_node();rclpy.shutdown()
