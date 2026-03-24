import rclpy
from rclpy.node import Node
from rcl_interfaces.msg import SetParametersResult
from candle_ros2.msg import ControlModuleData, PositionPidCmd, MotionCmd, Pid
from candle_ros2.srv import SetMode, Generic, AddDevices
from std_srvs.srv import Trigger
import time
import threading

class PidTunerNode(Node):
    def __init__(self):
        super().__init__('pid_tuner')

        # --- PARAMETRY ---
        self.declare_parameter('device_id', 316)
        self.declare_parameter('pos_kp', 20.5)
        self.declare_parameter('pos_ki', 1.5)
        self.declare_parameter('pos_kd', 0.0)
        self.declare_parameter('vel_kp', 0.5)
        self.declare_parameter('vel_ki', 0.0005)
        
        self.target_id = self.get_parameter('device_id').value

        # --- PUBLISHERY I SUB ---
        # Publikujemy parametry PID
        self.pid_pub = self.create_publisher(PositionPidCmd, '/md/position_command', 10)
        # Publikujemy komendy ruchu (setpointy)
        self.motion_pub = self.create_publisher(MotionCmd, '/md/motion_command', 10)
        
        # Opcjonalnie: subskrypcja danych, jeśli chcesz logować błąd w konsoli
        self.state_sub = self.create_subscription(ControlModuleData, '/md/motor_state', self.state_callback, 10)

        # Callback dla dynamicznej zmiany parametrów
        self.add_on_set_parameters_callback(self.on_params_changed)

        # --- SERWISY ---
        self.step_srv = self.create_service(Trigger, '~/run_step_test', self.run_step_callback)
        self.init_srv = self.create_service(Trigger, '~/init_motor', self.init_motor_callback)

        # Klienty usług do drivera MD20
        self.cli_add = self.create_client(AddDevices, '/md/add_mds')
        self.cli_mode = self.create_client(SetMode, '/md/set_mode')
        self.cli_enable = self.create_client(Generic, '/md/enable')

        self.get_logger().info('=== MAB PID Tuner Node uruchomiony ===')
        self.get_logger().info('1. Wywołaj: ros2 service call /pid_tuner/init_motor std_srvs/srv/Trigger')
        self.get_logger().info('2. Zmieniaj parametry w rqt lub przez: ros2 param set /pid_tuner pos_kp <wartość>')

    def state_callback(self, msg):
        # Tutaj moglibyśmy analizować msg.position, msg.velocity itp.
        pass

    def init_motor_callback(self, request, response):
        """Automatyczna inicjalizacja (zastępuje bashe)"""
        self.get_logger().info('Inicjalizacja silnika (Add -> Mode -> Enable)...')
        
        # 1. Add Devices (Dodajemy oba ID jak w Twoim bashu)
        req_add = AddDevices.Request()
        req_add.device_ids = [316, 319]
        self.cli_add.call_async(req_add)
        time.sleep(0.5)

        # 2. Set Mode (POSITION_PID dla Twojego target_id)
        req_mode = SetMode.Request()
        req_mode.device_ids = [self.target_id]
        req_mode.mode = ["POSITION_PID"]
        self.cli_mode.call_async(req_mode)
        time.sleep(0.5)

        # 3. Enable
        req_en = Generic.Request()
        req_en.device_ids = [self.target_id]
        self.cli_enable.call_async(req_en)
        
        response.success = True
        response.message = f"Silnik {self.target_id} gotowy do pracy."
        return response

    def on_params_changed(self, params):
        """Reakcja na zmianę suwaków w rqt"""
        result = SetParametersResult(successful=True)
        # Po każdej zmianie wysyłamy aktualny stan PID do silnika
        self.send_pid_update()
        return result

    def send_pid_update(self):
        """Wysyła aktualne parametry PID do drivera"""
        msg = PositionPidCmd()
        msg.device_ids = [self.target_id]
        
        # Budujemy obiekt PID dla pozycji
        pos_pid = Pid()
        pos_pid.kp = float(self.get_parameter('pos_kp').value)
        pos_pid.ki = float(self.get_parameter('pos_ki').value)
        pos_pid.kd = float(self.get_parameter('pos_kd').value)
        pos_pid.i_windup = 1.0
        pos_pid.max_output = 1.0
        
        # Budujemy obiekt PID dla prędkości
        vel_pid = Pid()
        vel_pid.kp = float(self.get_parameter('vel_kp').value)
        vel_pid.ki = float(self.get_parameter('vel_ki').value)
        vel_pid.kd = 0.0
        vel_pid.i_windup = 0.25
        vel_pid.max_output = 1e9 # Duża wartość domyślna
        
        msg.position_pid = [pos_pid]
        msg.velocity_pid = [vel_pid]
        
        self.pid_pub.publish(msg)

    def run_step_callback(self, request, response):
        """Test skokowy: 0.0 -> 1.5 rad"""
        def execute_step():
            self.get_logger().info('Skok do 0.0')
            m = MotionCmd()
            m.device_ids = [self.target_id]
            m.target_position = [0.0]
            m.target_velocity = [float('nan')]
            m.target_torque = [float('nan')]
            self.motion_pub.publish(m)
            
            time.sleep(1.5)
            
            self.get_logger().info('Skok do 1.5')
            m.target_position = [1.5]
            self.motion_pub.publish(m)

        threading.Thread(target=execute_step).start()
        response.success = True
        return response

def main(args=None):
    rclpy.init(args=args)
    node = PidTunerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()