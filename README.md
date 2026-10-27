# TurtleBot4 Office

TurtleBot4 in the Husarion Office world, with ROS 2 Lyrical, Gazebo Jetty, AMCL and Nav2.

## Install

On Ubuntu 26.04 with ROS 2 Lyrical and rosdep configured:

```bash
cd ~/ros2_ws/src
git clone --branch v0.1.1 https://github.com/robby-404canfind/turtlebot4_office.git
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

## Stop

While simulation time is still running:

```bash
ros2 run turtlebot4_office shutdown_navigation
```

Then stop the navigation launch with Ctrl+C, followed by the simulator launch.

For mapping, run `ros2 launch turtlebot4_office slam_launch.py` instead of the AMCL/navigation launch. Do not run both localization systems at once.

See [VALIDATION.md](VALIDATION.md) for tested behavior and [THIRD_PARTY.md](THIRD_PARTY.md) for source and license notices.
