import yaml
import test_tmp as mv


# import camera_move as mv
# pan = [-0.1, 0.5]
# tilt = [0.1, 0]
# step = [5, 5]
# mv.CameraPtz.move_scan(pan ,tilt, step)    #测试用例
# mv.move_to_point(0.5, 0)    #测试用例
# mv.read_ch4()    # 读取甲烷浓度，正常返回0  (需连接485接口)
'''
    Move_camera((x1,y1),(x2,y2),(p1,p2))
    参数说明：
    x1：float
       x轴水平方向开始位置
    y1：float
       y轴竖直方向开始位置
    x2：float
       x轴水平方向结束位置
    y2：float
       y轴竖直方向结束位置
    p1、p2：int
       水平、竖直方向的移动次数，值越大，移动越精确。一般不建议p1>100，p2>20
        数值过大，会导致相机移动次数过多，耗费时间。
    
    例子：
    move_pan(-0.25, 0.90, 0.25 -0.90, 50, 8)---相机前向90°范围内扫描，水平方向每次旋转角度为1.8°

    返回值：
    return(Alarm_images, str_alarm)
    每次移动打印甲烷浓度值“The concentration of ch4 is X”

    若甲烷浓度值超标,则对疑似泄露位置拍照返图Alarm_images,并返回甲烷浓度值str_alarm
    若甲烷浓度值未超标,则返回None及当前最大甲烷浓度值.
'''

'''
寻找测试检查点(移动云台)
输入值Find_Points(x, y)
'''


f = open(r"C:\Users\10619\OneDrive\燃气\vehicle_detection-v1\vehicle_detect\vehicle.yaml")
vehicle_params = yaml.load(f, Loader=yaml.FullLoader)

ip = vehicle_params['camera_info']['ip']
username = vehicle_params['camera_info']['username']
password = vehicle_params['camera_info']['password']
point1 = vehicle_params['leakage_det_region'][0]  # [-0.1, 0.95]
point2 = vehicle_params['leakage_det_region'][1]  # [0.1, -0.92]
step_nums = vehicle_params['leakage_det_step_nums']  # [5,5]
detect_point = vehicle_params['detect_point']

a = mv.CameraPtz(ip, username, password, point1, point2, step_nums, detect_point)
a.snap()
a.move_scan()





