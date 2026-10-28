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

## 0.3.0: behaviors and BT Navigator

Validated on 2026-10-28 with Nav2 1.5.2 and BehaviorTree.CPP 4.10.0. The Ch01 default navigation and Ch02 tuning profiles are unchanged. The new `behavior.launch.py` starts the complete `config/behavior.yaml` profile and its dedicated RViz configuration.

| Check | Observed result |
| --- | --- |
| DriveOnHeading, 1 m at 0.2 m/s in open space | SUCCEEDED, actual travel 1.021 m, positive forward displacement, then zero velocity |
| BackUp, -0.5 m at 0.2 m/s | SUCCEEDED, actual travel 0.522 m and negative forward displacement, then zero velocity |
| Spin, 3.14 rad | SUCCEEDED, actual accumulated rotation 3.116 rad, then zero velocity |
| Wait, 3 s | SUCCEEDED, no translation or rotation |
| AssistedTeleop, 0.2 m/s for 2 simulation seconds | Actual forward displacement 0.401 m; explicit zero input followed by preempt completed successfully and stopped |
| Corrected BT with a specified path | NavigateToPose to map (6, 4), yaw 0 succeeded; actual movement and stop confirmed |
| New complete profile with the default BT | Fresh default spawn/AMCL seed, NavigateToPose to (6, 4), yaw 0 succeeded, actual motion and zero final velocity confirmed |

Actual movement was observed from Gazebo model poses independently of action status and odometry, and the Ubuntu RViz/robot heading were inspected through RustDesk. Natural localization and wheel-odometry differences are retained.

Historical configuration failures were reproduced before correction: `SequenceStar` was not recognized (BT error 9001); an explicitly missing XML file failed with 9001; the removed `error_code_names` parameter prevented navigator configuration. Its isolated upstream node also faulted during cleanup after that configuration failure. The original `enable_stamped_cmd_vel: false` produced Twist, incompatible with this profile's TwistStamped pipeline. The active keys are `transform_tolerance` and navigator-scoped blackboard IDs.

From the default spawn the original 1 m forward command correctly stopped after approximately 0.281 m because the costmap predicted a collision. Moving to open space allowed the same distance and speed to succeed; collision checks and command difficulty were not reduced.

An attempt to reload the RViz configuration in a running RViz instance raised a duplicate `base_frame` parameter error in upstream code. Launching a fresh RViz with the supplied configuration displayed correctly. Runtime verification is separate from this reload limitation and upstream shutdown diagnostics.

An explicitly empty `plugin_lib_names: []` entry triggered a launch parameter tuple-conversion error in the current composed launch. The final profile omits that optional key and uses Nav2's declared empty default for additional libraries. Built-in BT nodes still load automatically.

## 0.4.0: costmap layers

Validated on 2026-10-28 with Nav2 1.5.2. The complete costmap profile retains the default MPPI controller and adds a focused RViz layout and an installed Gazebo obstacle helper. Earlier navigation, tuning and behavior profiles are unchanged.

| Check | Observed result |
| --- | --- |
| Fresh costmap launch and goal (6, 4), yaw 0 | SUCCEEDED; actual movement and zero final velocity confirmed |
| Installed obstacle helper | Added the orange box to the running Office world; its observed faces appeared in global and local costmaps |
| Fixed start (6, 4), goal (8, 4), global obstacle layer on / off | Both plans succeeded; minimum path-point distance to observed added-obstacle lethal-cell centers changed from 0.399 m to 0.0086 m |
| RQt global obstacle checkbox | Actual GUI mouse/keyboard operation toggled the parameter true/false; local voxel observations remained enabled |
| Student action CLI with the global obstacle layer disabled | ABORTED with error 105 after recovery attempts; actual travel 1.051 m and zero final velocity confirmed |
| Restore global obstacle layer and remove the box, same goal | SUCCEEDED, actual movement and zero final velocity confirmed |
| Inflation factor 1.0 / 10.0, radius 0.7 | Identical static geometry; 18,131 differing nonlethal cells all had lower costs at factor 10.0, with none higher; factor 3.0 and obstacle layer restored |
| Local width / height 3 m → 5 m → 3 m | Grid changed 60 × 60 → 100 × 100 → 60 × 60 at 0.05 m/cell |
| Global static map | Grid follows the received map: 293 × 274 cells at 0.05 m/cell |
| Voxel grid | Actual dimensions 60 × 60 × 16; vertical resolution 0.05 m, total vertical span 0.8 m |
| Unknown-space inflation flags | `inflate_unknown` wrote gradient costs into 13,849 formerly unknown cells; `inflate_around_unknown` increased costs in 7,838 known cells; both flags restored to false |

Plan-to-cell measurements are not guaranteed robot-body clearance. Navigation outcomes depend on geometry and controller settings; disabling the global obstacle layer does not imply every goal must fail. Inflation comparisons used a stationary robot and static geometry with the obstacle layer temporarily disabled, then restored. Runtime parameters and the supplied YAML were compared with the teaching examples. Defaults, types and API behavior were checked against the matching official Nav2 1.5.2 sources.

The final installed helper was exercised from fresh interactive shells using Gazebo's default partition. An earlier private test used a custom partition; a helper launched outside that partition could not discover its world. No validation-only partition is built into this package.

Actual Ubuntu Gazebo, RViz and RQt screens were inspected through RustDesk. Wheel odometry and true displacement were allowed to differ naturally. Shutdown diagnostics are recorded separately from successful runtime behavior.
