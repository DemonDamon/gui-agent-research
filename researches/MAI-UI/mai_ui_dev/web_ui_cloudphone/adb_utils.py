"""
ADB 工具模块 - 云手机版本
提供 Android 设备连接、截图、操作等功能
"""

import subprocess
import os
import time
import uuid
from typing import Tuple, List, Optional
from PIL import Image

# 配置日志
import logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - [ADB] - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# ==================== 配置 ====================
SCREENSHOT_TMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "tmp_screenshot")
SCREENSHOT_REMOTE_DIR = "/sdcard"
YADB_REMOTE_PATH = "/data/local/tmp/yadb"


# ==================== 基础 ADB 命令 ====================
def run_adb_command(command: List[str], timeout: int = 30, device_id: Optional[str] = None) -> Tuple[str, str, int]:
    """运行 ADB 命令"""
    if device_id and device_id not in command:
        if command and command[0] == "adb":
            command = ["adb", "-s", device_id] + command[1:]

    logger.debug(f"执行命令: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        if result.returncode != 0:
            logger.warning(f"命令返回错误: {result.stderr[:100]}")
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "命令超时", -1
    except Exception as e:
        return "", str(e), -1


def get_adb_devices() -> Tuple[List[str], str]:
    """获取已连接的 ADB 设备列表"""
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            timeout=10
        )
        devices = []
        details = []

        if result.returncode == 0:
            for line in result.stdout.split('\n')[1:]:
                if '\tdevice' in line:
                    device_id = line.split('\t')[0]
                    devices.append(device_id)
                    dtype = "📶 无线" if ':' in device_id else "🔌 USB"
                    details.append(f"{dtype}: {device_id}")

        if not details:
            return [], "未找到设备"

        return devices, f"已连接设备 ({len(devices)}个):\n\n" + "\n".join(details)
    except Exception as e:
        return [], f"获取设备失败: {str(e)}"


# ==================== 截图 ====================
def take_screenshot(device_id: Optional[str] = None, timeout: int = 30) -> Image.Image:
    """截取设备屏幕（文件模式）"""
    os.makedirs(SCREENSHOT_TMP_DIR, exist_ok=True)

    # 获取设备 ID
    if not device_id:
        devices, _ = get_adb_devices()
        if not devices:
            raise Exception("没有连接的设备")
        device_id = devices[0]
        logger.info(f"使用设备: {device_id}")

    # 生成文件名
    filename = f"screenshot_{uuid.uuid4().hex[:8]}.png"
    remote_path = f"{SCREENSHOT_REMOTE_DIR}/{filename}"
    local_path = os.path.join(SCREENSHOT_TMP_DIR, filename)

    logger.info(f"开始截图: {filename}")

    # 1. 手机端截图
    cmd = ["adb", "-s", device_id, "shell", "screencap", "-p", remote_path]
    stdout, stderr, code = run_adb_command(cmd, timeout=timeout)
    if code != 0:
        raise Exception(f"手机端截图失败: {stderr}")

    # 2. 拉取到本地
    cmd = ["adb", "-s", device_id, "pull", remote_path, local_path]
    stdout, stderr, code = run_adb_command(cmd, timeout=timeout)
    if code != 0:
        raise Exception(f"拉取截图失败: {stderr}")

    # 3. 删除手机端临时文件
    cmd = ["adb", "-s", device_id, "shell", "rm", remote_path]
    run_adb_command(cmd, timeout=10)

    # 4. 读取图片
    if not os.path.exists(local_path):
        raise Exception(f"本地文件不存在: {local_path}")

    image = Image.open(local_path)
    logger.info(f"截图成功: {image.size}")

    return image


# ==================== 设备操作 ====================
def tap_device(x: int, y: int, device_id: Optional[str] = None) -> bool:
    """点击屏幕"""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "tap", str(x), str(y)])

    _, _, code = run_adb_command(cmd)
    logger.info(f"点击 ({x}, {y}): {'成功' if code == 0 else '失败'}")
    return code == 0


def long_press_device(x: int, y: int, duration: int = 1000, device_id: Optional[str] = None) -> bool:
    """长按屏幕"""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "swipe", str(x), str(y), str(x), str(y), str(duration)])

    _, _, code = run_adb_command(cmd)
    logger.info(f"长按 ({x}, {y}) {duration}ms: {'成功' if code == 0 else '失败'}")
    return code == 0


def double_tap_device(x: int, y: int, device_id: Optional[str] = None) -> bool:
    """双击屏幕"""
    success1 = tap_device(x, y, device_id)
    time.sleep(0.05)
    success2 = tap_device(x, y, device_id)
    logger.info(f"双击 ({x}, {y}): {'成功' if success1 and success2 else '失败'}")
    return success1 and success2


def swipe_device(x1: int, y1: int, x2: int, y2: int, duration: int = 300, device_id: Optional[str] = None) -> bool:
    """滑动屏幕"""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])

    _, _, code = run_adb_command(cmd)
    logger.info(f"滑动 ({x1},{y1}) → ({x2},{y2}): {'成功' if code == 0 else '失败'}")
    return code == 0


def input_text(text: str, device_id: Optional[str] = None) -> bool:
    """输入文本（基础版，不支持中文）"""
    # 转义特殊字符
    escaped = text.replace(' ', '%s').replace("'", "").replace('"', '')
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "text", escaped])

    _, _, code = run_adb_command(cmd)
    logger.info(f"输入文本: {text[:30]}...")
    return code == 0


def input_text_paste(text: str, device_id: Optional[str] = None) -> bool:
    """
    通过剪贴板粘贴输入文本（支持中文和特殊字符）
    适用于云手机环境
    """
    # 将文本复制到剪贴板
    escaped_text = text.replace("'", "'\\''").replace(" ", "\\ ")
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "am", "broadcast", "-a", "adb.clipboard", f"--es", f"text", f"'{escaped_text}'"])

    _, _, code = run_adb_command(cmd, timeout=10)

    if code == 0:
        # 等待一下，然后模拟粘贴 (长按 + Ctrl+V)
        time.sleep(0.2)
        # 先尝试 Ctrl+V
        cmd_paste = ["adb"]
        if device_id:
            cmd_paste.extend(["-s", device_id])
        cmd_paste.extend(["shell", "input", "keyevent", "KEYCODE_CTRL_LEFT", "KEYCODE_V"])
        run_adb_command(cmd_paste, timeout=5)

        logger.info(f"剪贴板输入: {text[:30]}...")
        return True

    logger.warning(f"剪贴板输入失败，尝试基础输入")
    return input_text(text, device_id)


def input_text_broadcast(text: str, device_id: Optional[str] = None) -> bool:
    """
    通过 broadcast 方式输入文本（支持中文）
    使用 ADB Keyboard 方法
    """
    # URL 编码文本
    import urllib.parse
    encoded = urllib.parse.quote(text)

    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "am", "broadcast", "-a", "com.android.intent.action.INPUT_TEXT",
               "--es", "text", f"'{text}'"])

    _, _, code = run_adb_command(cmd, timeout=10)
    logger.info(f"Broadcast 输入: {text[:30]}...")
    return code == 0


def input_text_yadb(text: str, device_id: Optional[str] = None) -> bool:
    """
    输入文本（支持中文），尝试多种方法

    方法优先级：
    1. YADB（如果已安装）
    2. 剪贴板 + Ctrl+V
    3. Broadcast 意图
    4. 基础 input text（不支持中文）
    """
    # 方法1: 检查 YADB 是否可用
    check_cmd = ["adb"]
    if device_id:
        check_cmd.extend(["-s", device_id])
    check_cmd.extend(["shell", "ls", YADB_REMOTE_PATH])
    stdout, _, _ = run_adb_command(check_cmd, timeout=10)

    if "No such file" not in stdout:
        # YADB 可用，尝试使用
        escaped = text.replace(" ", "_")
        cmd = ["adb"]
        if device_id:
            cmd.extend(["-s", device_id])
        cmd.extend([
            "shell", "app_process",
            "-Djava.class.path=" + YADB_REMOTE_PATH,
            "/data/local/tmp",
            "com.ysbing.yadb.Main",
            "-keyboard", escaped
        ])

        stdout, stderr, code = run_adb_command(cmd, timeout=10)

        if code == 0:
            logger.info(f"✅ YADB 输入成功: {text[:30]}...")
            return True
        else:
            logger.warning(f"YADB 返回错误: {stdout[:100]}")

    # YADB 不可用或失败，尝试其他方法
    logger.info("YADB 不可用，尝试剪贴板方法...")

    # 方法2: 剪贴板 + Ctrl+V
    if input_text_paste(text, device_id):
        return True

    # 方法3: Broadcast 意图
    if input_text_broadcast(text, device_id):
        return True

    # 方法4: 基础输入（不支持中文）
    logger.warning("所有方法失败，使用基础输入（不支持中文）")
    return input_text(text, device_id)


def press_home(device_id: Optional[str] = None) -> bool:
    """按下 Home 键"""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "keyevent", "KEYCODE_HOME"])

    _, _, code = run_adb_command(cmd)
    logger.info("按下 Home 键")
    return code == 0


def press_back(device_id: Optional[str] = None) -> bool:
    """按下返回键"""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "keyevent", "KEYCODE_BACK"])

    _, _, code = run_adb_command(cmd)
    logger.info("按下返回键")
    return code == 0


def press_enter(device_id: Optional[str] = None) -> bool:
    """按下回车键"""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "keyevent", "KEYCODE_ENTER"])

    _, _, code = run_adb_command(cmd)
    logger.info("按下回车键")
    return code == 0


def wait_device(duration: int, device_id: Optional[str] = None) -> bool:
    """等待指定时间"""
    time.sleep(duration)
    logger.info(f"等待 {duration} 秒")
    return True


def get_device_resolution(device_id: Optional[str] = None) -> Tuple[int, int]:
    """获取设备分辨率"""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "wm", "size"])

    stdout, _, code = run_adb_command(cmd)
    if code == 0 and stdout:
        import re
        match = re.search(r'(\d+)x(\d+)', stdout)
        if match:
            return int(match.group(1)), int(match.group(2))
    return 1080, 1920


# ==================== 应用启动 ====================
def check_package_exists(package_name: str, device_id: Optional[str] = None) -> bool:
    """检查应用包是否存在"""
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "pm", "path", package_name])

    stdout, _, code = run_adb_command(cmd, timeout=10)
    return code == 0 and "package:" in stdout


def launch_app(app_name: str, device_id: Optional[str] = None) -> Tuple[bool, str]:
    """启动应用"""
    # 尝试解析包名
    package_name = None
    try:
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "web_ui"))
        from package_map import find_package_name
        package_name = find_package_name(app_name)
        logger.info(f"解析应用名: {app_name} → {package_name}")
    except Exception as e:
        if "." in app_name and app_name.count(".") >= 2:
            package_name = app_name
            logger.info(f"使用原始包名: {app_name}")
        else:
            logger.warning(f"无法解析应用名: {app_name}")
            return False, f"无法解析应用名: {app_name}"

    if package_name and check_package_exists(package_name, device_id):
        cmd = ["adb", "-s", device_id, "shell", "monkey", "-p", package_name,
               "-c", "android.intent.category.LAUNCHER", "1"]
        _, _, code = run_adb_command(cmd)
        if code == 0:
            return True, f"已启动: {app_name} ({package_name})"
        return False, f"启动失败: {app_name}"

    return False, f"应用未安装: {app_name}"


# ==================== 连接管理 ====================
def check_adb_connection() -> Tuple[bool, str]:
    """检查 ADB 连接状态"""
    try:
        subprocess.run(["adb", "start-server"], capture_output=True, timeout=5)
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            devices = []
            for line in lines[1:]:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        devices.append(f"📱 {parts[0]} - {parts[1]}")

            if devices:
                return True, "✅ ADB 服务正常\n已连接设备:\n" + "\n".join(devices)
            return False, "⚠️ ADB 服务正常但无设备连接"
        return False, "❌ ADB 命令执行失败"

    except FileNotFoundError:
        return False, "❌ ADB 未安装或未添加到 PATH"
    except Exception as e:
        return False, f"❌ 检查 ADB 连接时出错: {str(e)}"


def restart_adb() -> Tuple[bool, str]:
    """重启 ADB 服务"""
    try:
        subprocess.run(["adb", "kill-server"], capture_output=True, timeout=10)
        time.sleep(1)
        subprocess.run(["adb", "start-server"], capture_output=True, timeout=10)

        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            devices = [f"📱 {line.split()[0]}" for line in lines[1:] if '\tdevice' in line]
            if devices:
                return True, f"✅ ADB 重启成功\n当前设备:\n" + "\n".join(devices)
            return True, "✅ ADB 重启成功\n当前无设备连接"
        return False, "❌ ADB 重启失败"
    except Exception as e:
        return False, f"❌ 重启出错: {str(e)}"


def get_available_apps(device_id: Optional[str] = None) -> str:
    """获取设备上已安装的第三方应用列表"""
    try:
        cmd = ["adb"]
        if device_id:
            cmd.extend(["-s", device_id])
        cmd.extend(["shell", "pm", "list", "packages", "-3"])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            timeout=30
        )
        if result.returncode != 0:
            return "获取失败"
        apps = [line.replace('package:', '').strip() for line in result.stdout.splitlines() if line.strip()]
        apps.sort()
        return "\n".join(apps)
    except Exception as e:
        return str(e)
