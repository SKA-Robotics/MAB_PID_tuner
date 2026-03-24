from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='candle_ros2',
            executable='candle_container',
            name='candle_container',
            output='screen'
        ),
        
        Node(
            package='mab_pid_tuner',
            executable='tuner',
            name='pid_tuner',
            output='screen'
        )
    ])