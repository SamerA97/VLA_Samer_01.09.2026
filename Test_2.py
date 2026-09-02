from sympy import true
import time


from lerobot_local.src.lerobot.robots.ur5e_schunk.ur5e_schunk import ur5e_schunk
from lerobot_local.src.lerobot.robots.ur5e_schunk.config_ur5e_schunkfollower import ur5_schunkFollowerRobotConfig
from lerobot_local.src.lerobot.teleoperators.controller_8bit.Controller8Bit import Controller8Bit
from lerobot_local.src.lerobot.teleoperators.controller_8bit.Controller8BitConfig import Controller8BitConfig

from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.pipeline_features import aggregate_pipeline_dataset_features, create_initial_features
from lerobot.datasets.utils import combine_feature_dicts
from lerobot.model.kinematics import RobotKinematics
from lerobot.processor import RobotAction, RobotObservation, RobotProcessorPipeline, make_default_processors
from lerobot.processor.converters import (
    observation_to_transition,
    robot_action_observation_to_transition,
    robot_action_to_transition,
    transition_to_observation,
    transition_to_robot_action,
)
from lerobot.processor import make_default_processors
from lerobot.scripts.lerobot_record import record_loop
from lerobot.utils.utils import log_say

from lerobot.utils.control_utils import init_keyboard_listener
from lerobot.cameras.realsense.configuration_realsense import RealSenseCameraConfig
from lerobot.cameras.realsense.camera_realsense import RealSenseCamera
from lerobot.cameras.configs import ColorMode, Cv2Rotation

NUM_EPISODES = 1
FPS = 15
EPISODE_TIME_SEC = 10
RESET_TIME_SEC = 15
TASK_DESCRIPTION = "Grip the orange block and drop them into the box"
HF_REPO_ID = "Samer/test_dataset_1"  # Hier kannst du deinen eigenen Repo-Namen angeben, z.B. "deinusername/dein-dataset-name"
def main():
###realsens camera config
  
    camera_configs = {"front": RealSenseCameraConfig(
            serial_number_or_name="825312071649",
            width=640,
            height=480,
            fps=FPS,
            color_mode=ColorMode.RGB,
            use_depth=True,
            rotation=Cv2Rotation.ROTATE_180
        ), 
        "side": RealSenseCameraConfig(
            serial_number_or_name="825312070960",
            width=640, 
            height=480, 
            fps=FPS,
            color_mode=ColorMode.RGB,
            use_depth=True,
            rotation=Cv2Rotation.NO_ROTATION
        )
            }


    robot_config = ur5_schunkFollowerRobotConfig(
        ip= "192.168.2.200", 
        gripper_ip= "192.168.2.105",     
        cameras = camera_configs,  
        )
    teleop_config = Controller8BitConfig()




    robot = ur5e_schunk(robot_config)

    teleop = Controller8Bit(teleop_config)


   

    cameras = {name: RealSenseCamera(cfg) for name, cfg in camera_configs.items()}
    for cam in cameras.values():
        cam.connect()

    dataset = LeRobotDataset.create(
            repo_id=HF_REPO_ID,
            fps=FPS,
            robot_type="ur5e_schunk",
            features={
                "observation.images.front": {"dtype": "video", "shape": (3, 480, 640), "names": ["channels", "height", "width"]},
                "observation.images.side": {"dtype": "video", "shape": (3, 480, 640), "names": ["channels", "height", "width"]},
                "observation.state": {"dtype": "float32", "shape": (7,), "names": ["x", "y", "z", "u", "v", "w", "gripper"]},
                "action": {"dtype": "float32", "shape": (7,), "names": ["x", "y", "z", "u", "v", "w", "gripper"]},
            },
            use_videos = True,
            image_writer_threads =4,
        )

    robot.connect()
    teleop.connect()
    robot.reset_robot()
    print("Robot zurücksetzen")
    time.sleep(1)  # wait for the robot to reset

    # 1. Bleibt so (akzeptiert Tupel)
    teleop_to_pose_processor = RobotProcessorPipeline[
        tuple[RobotAction, RobotObservation], RobotAction](
        steps=[],
        to_transition=robot_action_observation_to_transition, 
        to_output=transition_to_robot_action,
    )

    # 2. KORREKTUR: Auch dieser Prozessor muss das Tupel akzeptieren!
    robot_action_processor = RobotProcessorPipeline[
        tuple[RobotAction, RobotObservation], RobotAction](
        steps=[],
        # Hier lag der Fehler: Er muss mit (Action, Observation) umgehen können
        to_transition=robot_action_observation_to_transition, 
        to_output=transition_to_robot_action,
    )

    # 3. Observation bleibt (akzeptiert nur RobotObservation)
    robot_observation_processor = RobotProcessorPipeline[RobotObservation, RobotObservation](
        steps=[],
        to_transition=observation_to_transition,
        to_output=transition_to_observation,
    )
    
    
    
    
    # Keyboard/Events initialisieren (sofern du die Hilfsfunktionen nutzt)
    _, events = init_keyboard_listener()

    print("Starte Aufnahme...")
    episode_idx = 0
    while episode_idx < NUM_EPISODES and not events["stop_recording"]:
        log_say(f"Recording episode {episode_idx + 1} of {NUM_EPISODES}")
        print(f"Episode {episode_idx + 1}/{NUM_EPISODES}")
        # Der eigentliche Aufnahme-Loop
        record_loop(
            robot=robot,
            events=events,
            fps=FPS,
            teleop=teleop,
            dataset=dataset,
            teleop_action_processor=teleop_to_pose_processor,
            robot_action_processor=robot_action_processor,
            robot_observation_processor=robot_observation_processor,
            control_time_s=EPISODE_TIME_SEC,
            single_task=TASK_DESCRIPTION,
            display_data=True,
        )
        print("Prüfe Teleop-Verbindung...")        
        
        robot.reset_robot()
        # Reset-Logik
        if not events["stop_recording"] and (episode_idx < NUM_EPISODES - 1 or events["rerecord_episode"]):
            log_say("Reset the environment")
            robot.reset_robot()
            time.sleep(1)  # wait for the robot to reset

            record_loop(
                robot=robot,
                events=events,
                fps=FPS,
                teleop=teleop,
                teleop_action_processor=teleop_to_pose_processor,
                robot_action_processor=robot_action_processor,
                robot_observation_processor=robot_observation_processor,
                control_time_s=RESET_TIME_SEC,
                display_data=True,
            )

        

        if events["rerecord_episode"]:
            log_say("Re-recording episode")
            events["rerecord_episode"] = False
            dataset.clear_episode_buffer()
            continue

        dataset.save_episode()
        episode_idx += 1

    # Abschluss
    robot.disconnect()
    teleop.disconnect()
    dataset.finalize()
    dataset.push_to_hub()

if __name__ == "__main__":
    main()






