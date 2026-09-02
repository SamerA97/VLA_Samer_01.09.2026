from lerobot_local.src.lerobot.robots.ur5e_schunk.ur5e_schunk import ur5e_schunk
from lerobot_local.src.lerobot.robots.ur5e_schunk.config_ur5e_schunkfollower import ur5_schunkFollowerRobotConfig
import time


if __name__ == "__main__":
    robot = ur5e_schunk(ur5_schunkFollowerRobotConfig(ip= "192.168.2.200", gripper_ip= "192.168.2.201"))
    time.sleep(0.1)  # wait for the robot to connect
    
    try: 
        robot.connect()
    except Exception as e:
        print(f"Failed to connect to the robot: {e}")
        exit(1)
    else:
        print("Robot connected")

    time.sleep(0.1)  # wait for the robot to be ready
    try:
        observation = robot.get_observation()
        print("Observation:", observation)
    except Exception as e:
        print(f"Failed to get observation: {e}")

    time.sleep(0.1)
    try: 
        action = {"x": -0.4825, "y": 0.0918, "z": 0.30, "u": 2.0644, "v": 2.0644, "w":-0.0539, "gripper_position": 0.0}
        robot.send_action(action)
        print("Action sent:", action)
    except Exception as e:
        print(f"Failed to send action: {e}")