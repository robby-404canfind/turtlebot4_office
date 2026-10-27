# Validation

Validated on 2026-10-27 with Ubuntu 26.04, ROS 2 Lyrical, Gazebo Jetty and the installed Nav2 minimal TurtleBot4 packages.

- `rosdep check --from-paths src/turtlebot4_office --ignore-src --rosdistro lyrical`: all dependencies satisfied.
- `colcon build --symlink-install --packages-select turtlebot4_office`: passed.
- Gazebo Office furniture and TurtleBot4, RViz map, scan, global/local costmaps and planner/controller groups were inspected on the actual Ubuntu desktop through RustDesk.
- A final clean simulator/navigation restart used the supplied default spawn and AMCL seed without a manual reset; its GUI goal also succeeded.
- GUI 2D Pose Estimate was applied and recorded. GUI Nav2 Goal, action CLI, `/goal_pose` CLI and the included Python ActionClient were run sequentially. Each returned SUCCEEDED, the robot actually moved, and odometry velocity settled to zero.

| Interface | Goal in map | Actual traveled distance | Result |
| --- | --- | ---: | --- |
| RViz Nav2 Goal | approximately (6, 4), yaw 0 | 8.03 m | SUCCEEDED |
| Action CLI | (3, 4), yaw 0 | 3.53 m | SUCCEEDED |
| `/goal_pose` topic | (2, 0), yaw 0 | 5.37 m | SUCCEEDED |
| Python + RViz Publish Point | (6.032, 0.964), yaw 0 | 4.00 m | SUCCEEDED |

Distance was measured from Gazebo model poses, independently of the action response and wheel odometry. Small localization/odometry errors are retained.

During these runs the MPPI trajectory and converted RViz Path each delivered 1,483 messages; the last pair used frame `odom` with 56 poses. The converter only displays the controller's output.

The unmodified historical Python sample also accepted a goal at the robot's current position. It is not reported as a failed navigation test. Its all-zero quaternion and use of position.z for yaw were corrected to encode orientation properly; the included sample uses simulation time and reports the action status and result.

The supplied occupancy map was saved from an actual SLAM Toolbox run. It covers the tested rooms and connecting routes, with other areas still unknown. Earlier temporary wall-projection guidance and attempts to navigate in unmapped areas were preparation experiments, not successful course runs. A supplied map is not a guarantee that every office room or arbitrary goal is reachable.

Navigation was shut down through its lifecycle manager while simulation time was running, then the navigation and simulator processes exited after SIGINT without remaining descendants. One composed Nav2 container reported exit code -6 during shutdown, and the Python display node printed KeyboardInterrupt; these shutdown diagnostics occurred after successful navigation and lifecycle shutdown. They are retained as a runtime limitation, not counted as a clean zero-error shutdown.

The optional standalone SLAM launch is included for remapping; the four goal-interface checks above used AMCL with the supplied map. Other ROS distributions and hardware have not been validated by this release.
