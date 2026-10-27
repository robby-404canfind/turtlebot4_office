# Sources and licenses

- Husarion Office SDF and local model assets: Husarion `husarion_gz_worlds`, Apache-2.0, commit 87271ef83672d9c9c96cb014ac64d746cacfd2c4. https://github.com/husarion/husarion_gz_worlds
- OpenRobotics furniture is referenced by the upstream Fuel URLs, with upstream model metadata/license retained at the source; those remote files are not redistributed in this repository.
- Launch/configuration base: Robby `turtlebot4_depot`, Apache-2.0. TurtleBot4 robot description/simulation is supplied by installed Nav2 minimal TurtleBot4 packages, which retain their own license notices.

Changes to the Office SDF: modern Gazebo system-plugin filenames, one physics block, removal of legacy GUI floor controls and unsupported legacy saved-state data. Office geometry and furniture are preserved.

- config/slam.yaml is derived from SLAM Toolbox configuration, LGPL-2.1-only; its original notice is preserved. https://github.com/SteveMacenski/slam_toolbox

- `behavior_trees/tuning.xml`: Nav2 `nav2_bt_navigator` Lyrical, Apache-2.0, commit 009a99ee29d040045dac4af6e86e3ea44603c3ae. https://github.com/ros-navigation/navigation2/blob/lyrical/nav2_bt_navigator/behavior_trees/navigate_to_pose_w_replanning_and_recovery.xml . Modified to pass the selected goal checker, progress checker and path handler IDs to FollowPath.
