#!/usr/bin/env python3
# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
"""Compare actual Nav2 action results in the Office teaching environment."""
import argparse
import json
import math
import signal
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path
from nav2_msgs.action import ComputePathToPose, FollowPath, NavigateToPose, SmoothPath
from rcl_interfaces.srv import GetParameters, SetParametersAtomically
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, QoSProfile, qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener
from visualization_msgs.msg import Marker, MarkerArray

HOME = (5.4, 0.7, -0.56)
GOAL = (6.0, 4.0, 0.0)


def angle(q):
    return math.atan2(2 * (q.w*q.z + q.x*q.y), 1 - 2 * (q.y*q.y + q.z*q.z))


def geometry(path):
    points = [(p.pose.position.x, p.pose.position.y) for p in path.poses]
    vectors = [(b[0]-a[0], b[1]-a[1]) for a, b in zip(points, points[1:])]
    vectors = [v for v in vectors if math.hypot(*v) > 1e-6]
    headings = [math.atan2(y, x) for x, y in vectors]
    turns = [abs(math.atan2(math.sin(b-a), math.cos(b-a)))
             for a, b in zip(headings, headings[1:])]
    return {'length_m': sum(math.hypot(*v) for v in vectors),
            'max_turn_deg': math.degrees(max(turns, default=0.0)),
            'points': len(points)}


class Tuning(Node):
    def __init__(self):
        super().__init__('office_parameter_tuning')
        self.set_parameters([Parameter('use_sim_time', value=True)])
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)
        self.action_clients = {name: ActionClient(self, kind, '/' + name) for name, kind in [
            ('compute_path_to_pose', ComputePathToPose), ('smooth_path', SmoothPath),
            ('follow_path', FollowPath), ('navigate_to_pose', NavigateToPose)]}
        qos = QoSProfile(depth=1, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.paths = {name: self.create_publisher(Path, '/tuning/' + name, qos)
                      for name in ['input', 'before', 'after']}
        self.markers = self.create_publisher(MarkerArray, '/tuning/labels', qos)
        self.velocity = 0.0
        self.samples = []
        self.recording = False
        self.create_subscription(Odometry, '/odom', self.odom, qos_profile_sensor_data)
        self.create_timer(0.05, self.sample)

    def odom(self, msg):
        self.velocity = abs(msg.twist.twist.linear.x)

    def sample(self):
        if self.recording:
            self.samples.append(self.velocity)

    def wait(self, future, timeout=30.0):
        deadline = time.monotonic() + timeout
        while not future.done() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)
        if not future.done():
            raise TimeoutError('ROS 응답 대기 시간이 초과되었습니다.')
        return future.result()

    def spin_for(self, seconds):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.05)

    def robot(self):
        deadline = time.monotonic() + 15.0
        while time.monotonic() < deadline:
            try:
                return self.buffer.lookup_transform('map', 'base_link', Time()).transform
            except Exception:
                rclpy.spin_once(self, timeout_sec=0.05)
        raise TimeoutError('map과 base_link 사이의 TF를 확인해 주세요.')

    def pose(self, x, y, yaw=0.0):
        p = PoseStamped()
        p.header.frame_id = 'map'
        p.header.stamp = self.get_clock().now().to_msg()
        p.pose.position.x, p.pose.position.y = float(x), float(y)
        p.pose.orientation.z, p.pose.orientation.w = math.sin(yaw/2), math.cos(yaw/2)
        return p

    def service(self, node, kind, suffix, request):
        client = self.create_client(kind, '/' + node + '/' + suffix)
        try:
            if not client.wait_for_service(timeout_sec=15.0):
                raise RuntimeError(node + ' 서비스를 찾지 못했습니다.')
            return self.wait(client.call_async(request))
        finally:
            self.destroy_client(client)

    def get(self, node, names):
        request = GetParameters.Request(names=names)
        response = self.service(node, GetParameters, 'get_parameters', request)
        fields = {1: 'bool_value', 2: 'integer_value', 3: 'double_value', 4: 'string_value'}
        return {name: getattr(value, fields[value.type]) for name, value in zip(names, response.values)}

    def set(self, node, values):
        request = SetParametersAtomically.Request(parameters=[
            Parameter(name, value=value).to_parameter_msg() for name, value in values.items()])
        result = self.service(node, SetParametersAtomically, 'set_parameters_atomically', request).result
        if not result.successful:
            raise RuntimeError(result.reason)

    def action(self, name, goal, timeout=120.0):
        client = self.action_clients[name]
        if not client.wait_for_server(timeout_sec=20.0):
            raise RuntimeError(name + ' 액션 서버를 찾지 못했습니다.')
        handle = self.wait(client.send_goal_async(goal))
        if not handle.accepted:
            raise RuntimeError(name + ' 목표가 거절되었습니다.')
        result = handle.get_result_async()
        try:
            return self.wait(result, timeout)
        except BaseException:
            self.get_logger().info('실행 중인 목표를 취소합니다.')
            self.wait(handle.cancel_goal_async(), 10.0)
            self.wait(result, 10.0)
            raise

    @staticmethod
    def successful(result):
        if result.status != 4 or result.result.error_code != 0:
            raise RuntimeError(f'status={result.status}, {result.result}')
        return result.result.path

    def plan(self, start, goal, planner='GridBased'):
        request = ComputePathToPose.Goal(start=self.pose(*start), goal=self.pose(*goal),
                                        planner_id=planner, use_start=True)
        return self.successful(self.action('compute_path_to_pose', request, 30.0))

    def smooth(self, path, smoother):
        request = SmoothPath.Goal(path=path, smoother_id=smoother, check_for_collisions=True)
        request.max_smoothing_duration.sec = 5
        return self.successful(self.action('smooth_path', request, 15.0))

    def show(self, paths, title):
        for name, path in paths.items():
            self.paths[name].publish(path)
        labels = MarkerArray()
        label = Marker()
        label.header.frame_id = 'map'
        label.ns, label.id = 'tuning', 0
        label.type, label.action = Marker.TEXT_VIEW_FACING, Marker.ADD
        label.pose.position.x, label.pose.position.y, label.pose.position.z = 4.6, 6.5, 0.1
        label.pose.orientation.w = 1.0
        label.scale.z = 0.20
        label.color.r, label.color.g, label.color.b, label.color.a = 0.1, 0.1, 0.1, 1.0
        label.text = title
        labels.markers.append(label)
        self.markers.publish(labels)
        self.get_logger().info('RViz: 주황색 before / 청록색 after / 회색 input. Ctrl+C로 종료해줍니다.')

    def motion(self, path, checker, progress):
        goal = Marker()
        goal.header = path.poses[-1].header
        goal.ns, goal.id = 'tuning_goal', 0
        goal.type, goal.action = Marker.ARROW, Marker.ADD
        goal.pose = path.poses[-1].pose
        goal.scale.x, goal.scale.y, goal.scale.z = 0.7, 0.09, 0.12
        goal.color.g, goal.color.a = 0.75, 1.0
        self.markers.publish(MarkerArray(markers=[goal]))
        self.samples = []
        self.recording = True
        start_time = self.get_clock().now().nanoseconds * 1e-9
        request = FollowPath.Goal(path=path, controller_id='FollowPath',
                                  goal_checker_id=checker, progress_checker_id=progress,
                                  path_handler_id='PathHandler')
        response = self.action('follow_path', request)
        elapsed = self.get_clock().now().nanoseconds * 1e-9 - start_time
        self.spin_for(1.0)
        self.recording = False
        samples = sorted(self.samples)
        end = self.robot()
        return {'status': response.status, 'error_code': response.result.error_code,
                'error_msg': response.result.error_msg, 'simulation_seconds': elapsed,
                'max_speed_mps': max(samples, default=0.0),
                'p90_speed_mps': samples[int(0.9*(len(samples)-1))] if samples else 0.0,
                'end_x': end.translation.x, 'end_y': end.translation.y,
                'end_yaw': angle(end.rotation)}

    def close(self):
        self.listener.unregister()
        self.destroy_node()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['planner', 'navfn', 'smoother', 'drive', 'rotate', 'home'])
    parser.add_argument('--goal-checker', default='general_goal_checker')
    parser.add_argument('--progress-checker', default='progress_checker')
    parser.add_argument('--follow', action='store_true', help='Follow the smoothed path after comparison')
    parser.add_argument('--once', action='store_true', help='Exit after publishing comparison results')
    parser.add_argument('--before-cost', type=float, default=0.1, help='ThetaStar w_traversal_cost before tuning')
    parser.add_argument('--after-cost', type=float, default=10.0, help='ThetaStar w_traversal_cost after tuning')
    args = parser.parse_args()
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    def interrupt_once(signum, frame):
        signal.signal(signum, signal.SIG_IGN)
        raise KeyboardInterrupt

    signal.signal(signal.SIGINT, interrupt_once)
    node = Tuning()
    hold = False
    try:
        node.spin_for(1.0)
        if args.mode in ['planner', 'navfn']:
            parameter = 'ThetaStar.w_traversal_cost' if args.mode == 'planner' else 'GridBased.use_astar'
            values = [args.before_cost, args.after_cost] if args.mode == 'planner' else [False, True]
            planner = 'ThetaStar' if args.mode == 'planner' else 'GridBased'
            previous = node.get('planner_server', [parameter])
            paths = {}
            try:
                for name, value in zip(['before', 'after'], values):
                    node.set('planner_server', {parameter: value})
                    paths[name] = node.plan(HOME, GOAL, planner)
                    print(json.dumps({'label': name, parameter: value, **geometry(paths[name])}), flush=True)
            finally:
                node.set('planner_server', previous)
            node.show(paths, parameter + ': ' + str(values[0]) + ' / ' + str(values[1]))
            hold = True
        elif args.mode == 'smoother':
            start = HOME
            if args.follow:
                current = node.robot()
                if math.hypot(current.translation.x-HOME[0], current.translation.y-HOME[1]) > 0.4:
                    raise RuntimeError('출발점 근처에서 실행해 주세요. 비교 주행은 시뮬레이션과 Nav2를 다시 실행해줍니다.')
                start = (current.translation.x, current.translation.y, angle(current.rotation))
            raw = node.plan(start, GOAL)
            paths = {'input': raw, 'before': node.smooth(raw, 'data_smoother'),
                     'after': node.smooth(raw, 'smooth_smoother')}
            for name, path in paths.items():
                print(json.dumps({'label': name, **geometry(path)}), flush=True)
            settings = node.get('smoother_server', [p + '.' + field for p in ['data_smoother', 'smooth_smoother']
                                                     for field in ['w_data', 'w_smooth', 'do_refinement']])
            print(json.dumps(settings), flush=True)
            node.show(paths, 'SimpleSmoother w_data: ' + str(settings['data_smoother.w_data'])
                      + ' / ' + str(settings['smooth_smoother.w_data'])
                      + ' (w_smooth: ' + str(settings['data_smoother.w_smooth']) + ')')
            if args.follow:
                print(json.dumps(node.motion(paths['after'], args.goal_checker, args.progress_checker)), flush=True)
            hold = True
        elif args.mode == 'home':
            response = node.action('navigate_to_pose', NavigateToPose.Goal(pose=node.pose(*HOME)))
            print(json.dumps({'status': response.status, 'error_code': response.result.error_code}), flush=True)
        else:
            current = node.robot()
            start = (current.translation.x, current.translation.y, angle(current.rotation))
            if args.mode == 'drive':
                if math.hypot(start[0]-GOAL[0], start[1]-GOAL[1]) < 0.4:
                    raise RuntimeError('이미 목적지 근처입니다. 먼저 home 명령으로 출발점으로 이동해 주세요.')
                path = node.plan(start, GOAL)
                print(json.dumps(node.get('controller_server', ['FollowPath.max_vel_x', 'FollowPath.max_speed_xy'])), flush=True)
            else:
                goal_yaw = math.atan2(math.sin(start[2]+math.pi), math.cos(start[2]+math.pi))
                pose = node.pose(start[0], start[1], goal_yaw)
                path = Path(header=pose.header, poses=[pose, pose])
            result = node.motion(path, args.goal_checker, args.progress_checker)
            if args.mode == 'rotate':
                result['requested_yaw'] = goal_yaw
                result['remaining_yaw_error'] = abs(math.atan2(math.sin(result['end_yaw']-goal_yaw),
                                                             math.cos(result['end_yaw']-goal_yaw)))
            print(json.dumps(result), flush=True)
        if hold:
            if args.once:
                node.spin_for(2.0)
            else:
                rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
