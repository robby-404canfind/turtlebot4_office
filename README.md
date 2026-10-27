# TurtleBot4 Office

TurtleBot4 in the Husarion Office world, with ROS 2 Lyrical, Gazebo Jetty, AMCL and Nav2.

## Install

On Ubuntu 26.04 with ROS 2 Lyrical and rosdep configured:

```bash
cd ~/ros2_ws/src
git clone --branch v0.2.0 https://github.com/robby-404canfind/turtlebot4_office.git
cd ~/ros2_ws
rosdep install --from-paths src/turtlebot4_office --ignore-src -r -y --rosdistro lyrical
colcon build --symlink-install --packages-select turtlebot4_office
source install/setup.bash
```

## Run

```bash
ros2 launch turtlebot4_office bringup.launch.py
```

In another sourced terminal:

```bash
ros2 launch turtlebot4_office navigation.launch.py
```

The supplied SLAM map and AMCL initial estimate match the default spawn. Use **2D Pose Estimate** if localization needs correction, then drag a **Nav2 Goal** in known free space. The map covers the tested teaching routes; some rooms and corridors remain unmapped. Fuel assets are downloaded on first launch, so internet access is required and the first start can take longer.

Optional arguments: `headless:=true`, `nvidia:=true`, `x_pose`, `y_pose`, `yaw`, `world` for simulation; `map`, `params_file`, `use_rviz`, `use_composition` for navigation. A changed spawn or map also requires a matching localization estimate.

## Goal interfaces

```bash
ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose "pose: {header: {frame_id: map}, pose: {position: {x: 3.0, y: 4.0, z: 0.0}, orientation: {w: 1.0}}}"
ros2 topic pub -1 /goal_pose geometry_msgs/PoseStamped "{header: {frame_id: map}, pose: {position: {x: 2.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}"
```

Run these one at a time and wait for the robot to stop before sending the next goal.

The included ActionClient uses the RViz **Publish Point** tool:

```bash
ros2 run turtlebot4_office nav_to_pose_client --ros-args -p use_sim_time:=true
```

Click a free point in the map. The client sends one goal with yaw zero, prints its status/result and exits when the result arrives.

The `trajectory_path` node converts the MPPI controller's `nav_msgs/Trajectory` output to `nav_msgs/Path` for the supplied RViz **Controller / Local Plan** display. It does not send velocity commands.

## Parameter tuning

Start the simulator as above, then use the following **instead of** `navigation.launch.py`:

```bash
ros2 launch turtlebot4_office tuning.launch.py
```

This uses `config/tuning.yaml`: DWB, NavFn/ThetaStar, two progress checkers, two goal checkers, and SimpleSmoother comparison profiles. The tuning Behavior Tree passes the selected checker/path handler IDs explicitly to FollowPath. The default Ch01 navigation configuration remains MPPI. Do not run both navigation launches together.

In another terminal, run one comparison at a time:

```bash
ros2 run turtlebot4_office parameter_tuning navfn
ros2 run turtlebot4_office parameter_tuning planner --before-cost 0.1 --after-cost 10.0
ros2 run turtlebot4_office parameter_tuning smoother
```

Each command waits until Ctrl+C to keep its RViz results available. Gray is the input path, orange is `before`, cyan is `after`. Toggle paths in **Tuning comparison** to inspect overlapping paths. Planner comparisons use the same fixed start/goal and restore the previous parameters after computing. They do not drive the robot.

The ThetaStar comparison changes only `w_traversal_cost`. The smoother comparison uses one actual NavFn input path and changes only `w_data` (0.8 / 0.05); `w_smooth=0.3` and refinement settings are identical. Both smoothing requests check collisions. SimpleSmoother reads these settings during configuration: edit YAML and restart Nav2 to change them. Ordinary Nav2 goals do not automatically use this explicit `SmoothPath` comparison.

To follow the cyan smoothed result, restart simulation and navigation to restore the default starting position. This mode plans from the actual current estimated pose:

```bash
ros2 run turtlebot4_office parameter_tuning smoother --follow
```

For a DWB speed comparison, use a fresh simulation and navigation start for each run:

```bash
ros2 param set /controller_server FollowPath.max_vel_x 0.5
ros2 param set /controller_server FollowPath.max_speed_xy 0.5
ros2 run turtlebot4_office parameter_tuning drive
```

Restart both launches and repeat with **both** limits set to `0.15`. These are upper limits; they do not force a constant speed. `simulation_seconds` uses simulation time; measured speeds use odometry. Restore both limits to `0.5` afterwards. `home` returns approximately to the starting pose, but a fresh simulation gives more comparable starting conditions.

```bash
ros2 run turtlebot4_office parameter_tuning home
```

The `rotate` mode requests a half turn from the current heading using `FollowPath`, without Behavior Tree recovery retries. A green arrow shows the requested heading; the robot's red axis shows its current forward direction.

```bash
ros2 param set /controller_server progress_checker.movement_time_allowance 1.0
ros2 run turtlebot4_office parameter_tuning rotate
ros2 param set /controller_server pose_progress_checker.required_movement_angle 0.1
ros2 param set /controller_server pose_progress_checker.movement_time_allowance 1.0
ros2 run turtlebot4_office parameter_tuning rotate --progress-checker pose_progress_checker
```

The first case is expected to abort with error 105 because SimpleProgressChecker only counts translation. PoseProgressChecker also counts angular progress. Restore the allowances to `10.0` and the angle to `0.3` before other exercises.

With normal progress settings, compare `general_goal_checker.yaw_goal_tolerance` at `1.0` and `0.25`, running `rotate --progress-checker pose_progress_checker` after each change. Restore `0.25` afterwards. To also require a low measured speed, add `--goal-checker stopped_goal_checker` (configured translation/angular speed thresholds: `0.25`). Goal checker tolerances and DWB's near-goal rotation window are separate settings.

Complete each movement before the next request. Ctrl+C cancels an active action. Stop navigation before simulation, while `/clock` is still running. If restarting navigation alone after moving, correct the AMCL initial estimate; restarting simulation as well restores the matching default spawn.

## Stop

While simulation time is still running:

```bash
ros2 run turtlebot4_office shutdown_navigation
```

Then stop the navigation launch with Ctrl+C, followed by the simulator launch.

For mapping, run `ros2 launch turtlebot4_office slam_launch.py` instead of the AMCL/navigation launch. Do not run both localization systems at once.

See [VALIDATION.md](VALIDATION.md) for tested behavior and [THIRD_PARTY.md](THIRD_PARTY.md) for source and license notices.
