# MAB PID tuner

> Author: Selim Mucharski

> TO DO: The README file will be improved

## Creating workspace
```bash
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src
```

```bash
git clone https://github.com/mabrobotics/candle_ros2.git
git clone https://github.com/SKA-Robotics/MAB_PID_tuner.git
```

```bash
cd ~/ros_ws
colcon build
source install/setup.bash
```

## Launch tuner
```bash
ros2 launch mab_pid_tuner tuner.launch.py
```

```bash
ros2 service call /pid_tuner/init_motor std_srvs/srv/Trigger
```

## Run test (Step Response)
```bash
ros2 service call /pid_tuner/run_step_test std_srvs/srv/Trigger
```

## Online PID parameter change
```bash
ros2 run rqt_reconfigure rqt_reconfigure
```

## Real-time Visualization
```bash
ros2 run plotjuggler plotjuggler
```