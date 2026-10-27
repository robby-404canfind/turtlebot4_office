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

## 0.2.0: parameter tuning

The Ch02 tuning launch was additionally tested on the same Ubuntu/ROS/Gazebo setup, with Nav2 1.5.2. The Ch01 default MPPI configuration is unchanged.

| Exercise | Observed result |
| --- | --- |
| NavFn Dijkstra / A* | Both ComputePathToPose requests succeeded; paths may overlap or differ |
| ThetaStar traversal cost 0.1 / 10.0 | Same start and goal, paths 6.706 / 7.848 m; the higher-cost result stayed farther from the wall in RViz |
| DWB limits 0.5 / 0.15 m/s | Fresh identical starts; 20.407 / 59.905 simulation seconds; measured maximum and 90th-percentile speeds approximately matched the limits; both succeeded and stopped |
| Simple / Pose progress checker, 1 s allowance | Half-turn request: Simple aborted with error 105; Pose (0.1 rad progress threshold) succeeded |
| Goal yaw tolerance 1.0 / 0.25 rad | Both succeeded, with final sampled heading differences approximately 0.931 / 0.250 rad; green requested-heading marker and robot axes were inspected in RViz |
| StoppedGoalChecker | With translation/angular thresholds 0.25, succeeded and subsequently settled to zero velocity |
| SimpleSmoother w_data 0.8 / 0.05 | Identical real NavFn input, w_smooth=0.3 and identical refinement; maximum adjacent-segment turn 18.10 / 3.07 degrees, compared with 83.66 degrees in the input; collision checks passed |
| Follow smoothed path | From a fresh default spawn and actual estimated starting pose: succeeded in 21.370 simulation seconds; actual movement and zero final velocity confirmed |
| Return home | NavigateToPose succeeded using the supplied tuning Behavior Tree; actual return movement and stop confirmed |
| Ctrl+C during motion | Final installed helper cancelled FollowPath; server confirmed cancellation and measured linear/angular velocities settled to zero |

Path shape measurements describe the computed path, not robot steering angles. Clearance measurements used privately during validation were distances to occupied-cell centers, not a guaranteed robot-body safety margin. Normal localization and odometry differences are retained.

The tuning Behavior Tree passes the selected checker/path handler IDs to FollowPath. The installed upstream default tree selected those IDs but did not pass them, causing rejection when multiple goal checkers were loaded. Ch01 uses a single checker and its default configuration was retained.

SimpleSmoother reads weights during configuration; a successful parameter-set response alone does not establish a changed algorithm. The two comparison profiles differ only in w_data. Smoothing is explicitly requested by this helper and is not automatically inserted into ordinary Nav2 goals.

Preparation failures were retained separately from successful final runs: aggressive smoothing of decimated paths failed collision checking; a 0.05 rad/s stopped-velocity threshold could fail to settle before progress timeout; an early fixed-start smoothed-path follow after an approximate return home failed. The final lesson requires a fresh start for that comparison and plans from the actual estimated pose. A verifier TF-discovery race and an early helper attribute-name collision were also corrected. Repeated Ctrl+C signals are ignored while cancelling an action so cancellation can complete.

Lyrical DWB does not consume the historical FollowPath.transform_tolerance or FollowPath.stateful settings; those keys were removed from the tuning configuration. FeasiblePathHandler obtains the transform tolerance from the local costmap (0.3 s here). Goal-checker stateful behavior is a separate active setting.

Dependency checks and builds passed. Actual Ubuntu/RViz screens were inspected through RustDesk. Navigation lifecycle shutdown was requested with simulation time running before SIGINT; no tracked descendants remained. Upstream container/bridge/RViz shutdown diagnostics are distinguished from the successful runtime exercises in the private validation record.
