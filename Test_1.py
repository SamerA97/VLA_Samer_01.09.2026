from sympy import true
import time

from lerobot_local.src.lerobot.robots.ur5e_schunk.ur5e_schunk import ur5e_schunk
from lerobot_local.src.lerobot.robots.ur5e_schunk.config_ur5e_schunkfollower import ur5_schunkFollowerRobotConfig
from lerobot_local.src.lerobot.teleoperators.controller_8bit.Controller8Bit import Controller8Bit
from lerobot_local.src.lerobot.teleoperators.controller_8bit.Controller8BitConfig import Controller8BitConfig


from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig
from lerobot.cameras.realsense.camera_realsense import RealSenseCamera
from lerobot.cameras.configs import ColorMode, Cv2Rotation

###realsens camera config
robot_config = ur5_schunkFollowerRobotConfig(
    ip= "192.168.2.200", 
    gripper_ip= "192.168.2.105"   
    )



teleop_config = Controller8BitConfig()




robot = ur5e_schunk(robot_config)

teleop = Controller8Bit(teleop_config)
print("Hello World")
robot.connect()
teleop.connect()
time.sleep(0.1)  # wait for the teleop to connect

robot.reset_robot()
time.sleep(0.1)  # wait for the robot to reset

## exit when ESC is pressed
while True:
    try: 
        action = teleop.get_action()
        print(action)
        robot.send_action(action)

    except KeyboardInterrupt:
        print("Exiting...")
        break
  

print("Disconnecting...")
teleop.disconnect()
robot.disconnect()

        

    







#robot.connect()
#print(robot.get_observation())

