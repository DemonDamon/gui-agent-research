"""
ADB utility functions module.
Provides Android device connection, screenshot, and operation functions.
"""

import subprocess
import re
import os
import time
import uuid
from io import BytesIO
from typing import Tuple, List, Optional, Union
from PIL import Image


class DeviceCache:
    """
    Device information cache to avoid frequent adb devices calls.
    Suitable for slow network environments like NAT traversal.
    """
    
    def __init__(self, cache_ttl: float = 30.0):
        """
        Args:
            cache_ttl: Cache validity period (seconds), default 30 seconds
        """
        self._device_id: Optional[str] = None
        self._devices: List[str] = []
        self._resolution: Optional[Tuple[int, int]] = None
        self._last_check: float = 0
        self._cache_ttl = cache_ttl
    
    def get_device_id(self, force_refresh: bool = False) -> Optional[str]:
        """Get cached device ID, refresh if expired."""
        if force_refresh or self._is_expired():
            self._refresh()
        return self._device_id
    
    def get_devices(self, force_refresh: bool = False) -> List[str]:
        """Get cached device list."""
        if force_refresh or self._is_expired():
            self._refresh()
        return self._devices
    
    def set_device_id(self, device_id: str) -> None:
        """Manually set device ID (for Web UI device selection)."""
        self._device_id = device_id
        self._last_check = time.time()
    
    def set_resolution(self, width: int, height: int) -> None:
        """Cache device resolution."""
        self._resolution = (width, height)
    
    def get_resolution(self) -> Optional[Tuple[int, int]]:
        """Get cached resolution."""
        return self._resolution
    
    def invalidate(self) -> None:
        """Clear cache."""
        self._device_id = None
        self._devices = []
        self._resolution = None
        self._last_check = 0
    
    def _is_expired(self) -> bool:
        return time.time() - self._last_check > self._cache_ttl
    
    def _refresh(self) -> None:
        """Refresh device list."""
        try:
            result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="ignore",
                timeout=10
            )
            self._devices = []
            if result.returncode == 0:
                lines = result.stdout.split("\n")[1:]
                for line in lines:
                    if "\tdevice" in line:
                        device_id = line.split("\t")[0]
                        self._devices.append(device_id)
            
            if self._devices and (not self._device_id or self._device_id not in self._devices):
                self._device_id = self._devices[0]
            self._last_check = time.time()
        except Exception as e:
            print(f"[DeviceCache] Failed to refresh device list: {e}")


# Global device cache instance
device_cache = DeviceCache(cache_ttl=30.0)

# Screenshot temporary directory configuration
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_TMP_DIR = os.path.join(_PROJECT_ROOT, "logs", "tmp_screenshot")
SCREENSHOT_REMOTE_DIR = "/sdcard"

# YADB path configuration (for Chinese input support)
YADB_REMOTE_PATH = "/data/local/tmp/yadb"
YADB_LOCAL_PATH = os.path.join(_PROJECT_ROOT, "tools", "yadb")


def run_adb_command(
    command: List[str],
    timeout: int = 30,
    binary: bool = False,
    device_id: Optional[str] = None
) -> Tuple[Union[str, bytes], str, int]:
    """
    Run ADB command.
    
    Args:
        command: Command argument list
        timeout: Timeout in seconds
        binary: Whether to return binary output
        device_id: Specify device ID
    
    Returns:
        Tuple of (stdout, stderr, return_code)
    """
    if device_id and device_id not in command:
        if command and command[0] == "adb":
            command = ["adb", "-s", device_id] + command[1:]
    
    print(f"[ADB] {' '.join(command)}")
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=not binary,
            timeout=timeout,
            encoding=None if binary else "utf-8",
            errors=None if binary else "replace"
        )
        if result.returncode != 0:
            stderr_str = result.stderr if not binary else result.stderr.decode("utf-8", errors="replace")
            print(f"[ADB Error] Code: {result.returncode}, Stderr: {stderr_str[:200] if stderr_str else 'None'}")
        return (
            result.stdout,
            result.stderr if not binary else result.stderr.decode("utf-8", errors="replace"),
            result.returncode
        )
    except subprocess.TimeoutExpired:
        return "" if not binary else b"", "Command timeout", -1
    except Exception as e:
        return "" if not binary else b"", str(e), -1


def get_adb_devices() -> Tuple[List[str], str]:
    """
    Get all connected ADB devices.
    
    Returns:
        Tuple of (device_id_list, status_message)
    """
    try:
        result = subprocess.run(
            ["adb", "devices"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10
        )
        devices = []
        device_details = []

        if result.returncode == 0:
            lines = result.stdout.split("\n")[1:]
            for line in lines:
                if "\tdevice" in line:
                    device_id = line.split("\t")[0]
                    devices.append(device_id)
                    device_type = "Wireless" if ":" in device_id else "USB"
                    device_details.append(f"{device_type}: {device_id}")

        if not device_details:
            return [], "No devices found"

        device_list = "\n".join(device_details)
        return devices, f"Connected devices ({len(devices)}):\n\n{device_list}\n\nDefault: {devices[0]}"
    except Exception as e:
        return [], f"Failed to get device list: {str(e)}"


def connect_wireless_device(ip_address: str, port: str = "5555") -> Tuple[bool, str]:
    """
    Connect wireless device.
    
    Args:
        ip_address: Device IP address
        port: Port number, default 5555
    
    Returns:
        Tuple of (success, message)
    """
    try:
        parts = ip_address.strip().split(".")
        if len(parts) != 4:
            return False, "Invalid IP address format"

        connect_addr = f"{ip_address}:{port}"
        result = subprocess.run(
            ["adb", "connect", connect_addr],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10
        )

        if result.returncode == 0:
            devices_result = subprocess.run(
                ["adb", "devices"],
                capture_output=True,
                text=True,
                encoding="utf-8"
            )
            if connect_addr in devices_result.stdout and "device" in devices_result.stdout:
                return True, f"Successfully connected to wireless device: {connect_addr}"
            else:
                return False, "Connection failed, please check device settings"
        else:
            return False, f"Connection failed: {result.stderr.strip() if result.stderr else result.stdout.strip()}"

    except subprocess.TimeoutExpired:
        return False, "Connection timeout"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def disconnect_wireless_device(device_id: Optional[str] = None) -> Tuple[bool, str]:
    """
    Disconnect wireless device.
    
    Args:
        device_id: Optional, specify device ID
    
    Returns:
        Tuple of (success, message)
    """
    try:
        cmd = ["adb", "disconnect"] if not device_id else ["adb", "disconnect", device_id]
        subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        return True, "Wireless device disconnected"
    except Exception as e:
        return False, f"Disconnect error: {str(e)}"


def take_screenshot_file_mode(
    device_id: Optional[str] = None,
    tmp_dir: str = SCREENSHOT_TMP_DIR,
    timeout: int = 30,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    scale: float = 1.0,
    use_cache: bool = True,
    cleanup_remote: bool = True
) -> Image.Image:
    """
    Capture device screen (file mode, better for slow networks).
    
    Implementation:
    1. Execute screencap on phone and save to /sdcard
    2. Pull to local with adb pull
    3. Delete temporary file on phone
    
    Args:
        device_id: Optional, specify device ID
        tmp_dir: Local temporary directory
        timeout: Timeout per step (seconds)
        max_retries: Maximum retry count
        retry_delay: Retry interval (seconds)
        scale: Scale ratio (0.1-1.0)
        use_cache: Whether to use device cache
        cleanup_remote: Whether to delete temporary file on phone
    
    Returns:
        PIL Image object
    
    Raises:
        Exception: Screenshot failed
    """
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
        print(f"[Screenshot] Created temporary directory: {tmp_dir}")
    
    if use_cache and not device_id:
        cached_id = device_cache.get_device_id()
        if cached_id:
            device_id = cached_id
            print(f"[Screenshot] Using cached device ID: {device_id}")
    
    if not device_id:
        devices, _ = get_adb_devices()
        if not devices:
            raise Exception("No Android device connected, please connect a device first")
        device_id = devices[0]
        device_cache.set_device_id(device_id)
    
    filename = f"screenshot_{uuid.uuid4().hex[:8]}.png"
    remote_path = f"{SCREENSHOT_REMOTE_DIR}/{filename}"
    local_path = os.path.join(tmp_dir, filename)
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Screenshot] File mode screenshot (attempt {attempt}/{max_retries})...")
            
            # Step 1: Screenshot on phone
            cmd_capture = ["adb"]
            if device_id:
                cmd_capture.extend(["-s", device_id])
            cmd_capture.extend(["shell", "screencap", "-p", remote_path])
            
            stdout, stderr, code = run_adb_command(cmd_capture, timeout=timeout)
            if code != 0:
                last_error = f"Phone screenshot failed: {stderr}"
                print(f"[Screenshot] Step 1 failed (attempt {attempt}): {stderr}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                continue
            
            print(f"[Screenshot] Phone screenshot complete: {remote_path}")
            
            # Step 2: Pull to local
            cmd_pull = ["adb"]
            if device_id:
                cmd_pull.extend(["-s", device_id])
            cmd_pull.extend(["pull", remote_path, local_path])
            
            stdout, stderr, code = run_adb_command(cmd_pull, timeout=timeout)
            if code != 0:
                last_error = f"Pull screenshot failed: {stderr}"
                print(f"[Screenshot] Step 2 failed (attempt {attempt}): {stderr}")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                continue
            
            print(f"[Screenshot] Pull complete: {local_path}")
            
            # Step 3: Delete temporary file on phone
            if cleanup_remote:
                cmd_rm = ["adb"]
                if device_id:
                    cmd_rm.extend(["-s", device_id])
                cmd_rm.extend(["shell", "rm", remote_path])
                run_adb_command(cmd_rm, timeout=10)
            
            # Step 4: Read local image
            if not os.path.exists(local_path):
                last_error = f"Local file not found: {local_path}"
                print(f"[Screenshot] Step 4 failed (attempt {attempt}): file not found")
                if attempt < max_retries:
                    time.sleep(retry_delay)
                continue
            
            image = Image.open(local_path)
            original_size = image.size
            
            device_cache.set_resolution(original_size[0], original_size[1])
            
            if scale < 1.0:
                new_width = int(original_size[0] * scale)
                new_height = int(original_size[1] * scale)
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                print(f"[Screenshot] Scaled: {original_size} -> {image.size}")
            else:
                print(f"[Screenshot] Success: {image.size} mode={image.mode}")
            
            return image
            
        except Exception as e:
            last_error = str(e)
            print(f"[Screenshot] Exception (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(retry_delay)
    
    raise Exception(f"Screenshot failed (retried {max_retries} times): {last_error}")


def take_screenshot(
    device_id: Optional[str] = None,
    timeout: int = 60,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    scale: float = 1.0,
    use_cache: bool = True,
    quality: int = 80
) -> Image.Image:
    """
    Capture device screen (stream mode, backup method).
    
    Uses adb exec-out screencap to transfer screenshot data through pipe.
    For slow networks, use take_screenshot_file_mode() instead.
    
    Args:
        device_id: Optional, specify device ID
        timeout: Timeout in seconds
        max_retries: Maximum retry count
        retry_delay: Retry interval (seconds)
        scale: Scale ratio (0.1-1.0)
        use_cache: Whether to use device cache
        quality: JPEG compression quality (1-100)
    
    Returns:
        PIL Image object
    
    Raises:
        Exception: Screenshot failed
    """
    if use_cache and not device_id:
        cached_id = device_cache.get_device_id()
        if cached_id:
            device_id = cached_id
            print(f"[Screenshot] Using cached device ID: {device_id}")
    
    if not device_id:
        devices, _ = get_adb_devices()
        if not devices:
            raise Exception("No Android device connected, please connect a device first")
        device_id = devices[0]
        device_cache.set_device_id(device_id)
    
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["exec-out", "screencap", "-p"])
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"[Screenshot] Attempt {attempt}/{max_retries}, timeout {timeout}s, scale {scale}...")
            
            stdout, stderr, code = run_adb_command(cmd, binary=True, timeout=timeout)
            
            if code != 0:
                last_error = f"Screenshot command failed: {stderr}"
                print(f"[Screenshot] ADB Error (attempt {attempt}): {stderr}")
                if attempt < max_retries:
                    print(f"[Screenshot] Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                continue
            
            if not stdout:
                last_error = "Screenshot data is empty, please check device connection"
                print(f"[Screenshot] Empty stdout (attempt {attempt})")
                if attempt < max_retries:
                    print(f"[Screenshot] Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                continue
                
            print(f"[Screenshot] Received {len(stdout)} bytes")
            
            png_header = b"\x89PNG\r\n\x1a\n"
            if isinstance(stdout, str):
                stdout = stdout.encode("latin-1")
                
            start_index = stdout.find(png_header)
            if start_index == -1:
                last_error = "Invalid screenshot data: PNG header not found"
                print(f"[Screenshot] No PNG header found (attempt {attempt})")
                if attempt < max_retries:
                    print(f"[Screenshot] Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                continue
            
            if start_index > 0:
                print(f"[Screenshot] Found PNG header at offset {start_index}, trimming...")
                stdout = stdout[start_index:]
            
            try:
                image = Image.open(BytesIO(stdout))
                original_size = image.size
                
                device_cache.set_resolution(original_size[0], original_size[1])
                
                if scale < 1.0:
                    new_width = int(original_size[0] * scale)
                    new_height = int(original_size[1] * scale)
                    image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    print(f"[Screenshot] Scaled: {original_size} -> {image.size}")
                else:
                    print(f"[Screenshot] Valid image: {image.size} mode={image.mode}")
                
                return image
                
            except Exception as e:
                last_error = f"Screenshot data parsing failed: {e}"
                print(f"[Screenshot] Image.open failed (attempt {attempt}): {e}")
                if attempt < max_retries:
                    print(f"[Screenshot] Waiting {retry_delay}s before retry...")
                    time.sleep(retry_delay)
                continue
                
        except Exception as e:
            last_error = str(e)
            print(f"[Screenshot] Exception (attempt {attempt}): {e}")
            if attempt < max_retries:
                print(f"[Screenshot] Waiting {retry_delay}s before retry...")
                time.sleep(retry_delay)
    
    raise Exception(f"Screenshot failed (retried {max_retries} times): {last_error}")


def get_device_resolution(device_id: Optional[str] = None) -> Tuple[int, int]:
    """
    Get device screen resolution.
    
    Args:
        device_id: Optional, specify device ID
    
    Returns:
        Tuple of (width, height)
    """
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "wm", "size"])
    
    stdout, stderr, code = run_adb_command(cmd)
    
    if code == 0 and stdout:
        match = re.search(r"(\d+)x(\d+)", stdout)
        if match:
            return int(match.group(1)), int(match.group(2))
    
    return 1080, 1920


def tap_device(x: int, y: int, device_id: Optional[str] = None) -> bool:
    """
    Tap device screen.
    
    Args:
        x: X coordinate
        y: Y coordinate
        device_id: Optional, specify device ID
    
    Returns:
        Whether successful
    """
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "tap", str(x), str(y)])
    
    _, _, code = run_adb_command(cmd)
    return code == 0


def long_press_device(
    x: int,
    y: int,
    duration: int = 1000,
    device_id: Optional[str] = None
) -> bool:
    """
    Long press device screen.
    
    Args:
        x: X coordinate
        y: Y coordinate
        duration: Press duration (milliseconds)
        device_id: Optional, specify device ID
    
    Returns:
        Whether successful
    """
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "swipe", str(x), str(y), str(x), str(y), str(duration)])
    
    _, _, code = run_adb_command(cmd)
    return code == 0


def swipe_device(
    x1: int,
    y1: int,
    x2: int,
    y2: int,
    duration: int = 300,
    device_id: Optional[str] = None
) -> bool:
    """
    Swipe device screen.
    
    Args:
        x1, y1: Start coordinates
        x2, y2: End coordinates
        duration: Swipe duration (milliseconds)
        device_id: Optional, specify device ID
    
    Returns:
        Whether successful
    """
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)])
    
    _, _, code = run_adb_command(cmd)
    return code == 0


def swipe_direction(
    direction: str,
    x: Optional[int] = None,
    y: Optional[int] = None,
    distance: int = 500,
    device_id: Optional[str] = None
) -> bool:
    """
    Swipe by direction.
    
    Args:
        direction: Direction (up, down, left, right)
        x, y: Start coordinates (optional, default screen center)
        distance: Swipe distance
        device_id: Optional, specify device ID
    
    Returns:
        Whether successful
    """
    width, height = get_device_resolution(device_id)
    
    if x is None:
        x = width // 2
    if y is None:
        y = height // 2
    
    direction = direction.lower()
    if direction == "up":
        x2, y2 = x, y - distance
    elif direction == "down":
        x2, y2 = x, y + distance
    elif direction == "left":
        x2, y2 = x - distance, y
    elif direction == "right":
        x2, y2 = x + distance, y
    else:
        return False
    
    return swipe_device(x, y, x2, y2, device_id=device_id)


def input_text(text: str, device_id: Optional[str] = None) -> bool:
    """
    Input text.
    
    Args:
        text: Text to input
        device_id: Optional, specify device ID
    
    Returns:
        Whether successful
    """
    escaped_text = (
        text.replace(" ", "%s")
        .replace("'", "")
        .replace('"', "")
        .replace("&", "")
        .replace("<", "")
        .replace(">", "")
    )
    
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "text", escaped_text])
    
    _, _, code = run_adb_command(cmd)
    return code == 0


def install_yadb(device_id: Optional[str] = None) -> bool:
    """
    Install YADB to device (for Chinese input support).
    
    Args:
        device_id: Optional, specify device ID
    
    Returns:
        Whether successful
    """
    if not os.path.exists(YADB_LOCAL_PATH):
        print(f"[YADB] Local file not found: {YADB_LOCAL_PATH}")
        return False
    
    check_cmd = ["adb"]
    if device_id:
        check_cmd.extend(["-s", device_id])
    check_cmd.extend(["shell", "ls", YADB_REMOTE_PATH])
    
    stdout, _, code = run_adb_command(check_cmd)
    if code == 0 and "No such file" not in stdout:
        print("[YADB] Already installed on device")
        return True
    
    push_cmd = ["adb"]
    if device_id:
        push_cmd.extend(["-s", device_id])
    push_cmd.extend(["push", YADB_LOCAL_PATH, YADB_REMOTE_PATH])
    
    _, _, code = run_adb_command(push_cmd, timeout=30)
    if code == 0:
        chmod_cmd = ["adb"]
        if device_id:
            chmod_cmd.extend(["-s", device_id])
        chmod_cmd.extend(["shell", "chmod", "+x", YADB_REMOTE_PATH])
        run_adb_command(chmod_cmd)
        print("[YADB] Installation successful")
        return True
    
    print("[YADB] Installation failed")
    return False


def input_text_yadb(text: str, device_id: Optional[str] = None) -> bool:
    """
    Input text using YADB (supports Chinese and special characters).
    
    Args:
        text: Text to input
        device_id: Optional, specify device ID
    
    Returns:
        Whether successful
    """
    install_yadb(device_id)
    
    escaped_text = text.replace(" ", "_")
    
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend([
        "shell",
        "app_process",
        "-Djava.class.path=" + YADB_REMOTE_PATH,
        "/data/local/tmp",
        "com.ysbing.yadb.Main",
        "-keyboard",
        escaped_text
    ])
    
    _, _, code = run_adb_command(cmd, timeout=10)
    return code == 0


# System button mapping
SYSTEM_BUTTONS = {
    "home": "KEYCODE_HOME",
    "back": "KEYCODE_BACK",
    "menu": "KEYCODE_MENU",
    "enter": "KEYCODE_ENTER",
    "power": "KEYCODE_POWER",
    "volume_up": "KEYCODE_VOLUME_UP",
    "volume_down": "KEYCODE_VOLUME_DOWN",
}


def press_system_button(button: str, device_id: Optional[str] = None) -> bool:
    """
    Press system button.
    
    Args:
        button: Button name (home, back, menu, enter, power, volume_up, volume_down)
        device_id: Optional, specify device ID
    
    Returns:
        Whether successful
    """
    keycode = SYSTEM_BUTTONS.get(button.lower())
    if not keycode:
        keycode = button.upper() if button.upper().startswith("KEYCODE_") else f"KEYCODE_{button.upper()}"
    
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "input", "keyevent", keycode])
    
    _, _, code = run_adb_command(cmd)
    return code == 0


def check_package_exists(package_name: str, device_id: Optional[str] = None) -> bool:
    """
    Check if app package exists on device.
    
    Args:
        package_name: Package name
        device_id: Optional, specify device ID
    
    Returns:
        Whether exists
    """
    cmd = ["adb"]
    if device_id:
        cmd.extend(["-s", device_id])
    cmd.extend(["shell", "pm", "path", package_name])
    
    stdout, _, code = run_adb_command(cmd, timeout=10)
    return code == 0 and "package:" in stdout


def open_app(
    app_name: str,
    device_id: Optional[str] = None,
    prefer_awake: bool = True,
    fallback_to_search: bool = True
) -> Tuple[bool, str]:
    """
    Open app by name.
    Supports Chinese app names (e.g. "WeChat") and package names (e.g. "com.tencent.mm")
    
    Args:
        app_name: App name or package name
        device_id: Optional, specify device ID
        prefer_awake: If True, try to start with package name directly
        fallback_to_search: If AWAKE fails, return "need to search" status
    
    Returns:
        Tuple of (success, message)
    """
    package_name = None
    try:
        from utils.package_map import find_package_name
        package_name = find_package_name(app_name)
        print(f"[App] Resolved app name: {app_name} -> {package_name}")
    except Exception as e:
        if "." in app_name and app_name.count(".") >= 2:
            package_name = app_name
            print(f"[App] Using original package name: {app_name}")
        else:
            print(f"[App] Cannot resolve app name: {app_name}, error: {e}")
            if fallback_to_search:
                return False, f"NEED_SEARCH:{app_name}"
            return False, f"Cannot resolve app name: {app_name}"
    
    if prefer_awake and package_name:
        if check_package_exists(package_name, device_id):
            cmd = ["adb"]
            if device_id:
                cmd.extend(["-s", device_id])
            cmd.extend([
                "shell", "monkey", "-p", package_name,
                "-c", "android.intent.category.LAUNCHER", "1"
            ])
            
            _, _, code = run_adb_command(cmd)
            if code == 0:
                return True, f"Started: {app_name} ({package_name})"
            else:
                cmd2 = ["adb"]
                if device_id:
                    cmd2.extend(["-s", device_id])
                cmd2.extend(["shell", "am", "start", "-n", f"{package_name}/.MainActivity"])
                _, _, code2 = run_adb_command(cmd2)
                if code2 == 0:
                    return True, f"Started (am): {app_name}"
                
                if fallback_to_search:
                    return False, f"NEED_SEARCH:{app_name}"
                return False, f"Start failed: {app_name}"
        else:
            print(f"[App] App not installed: {package_name}")
            if fallback_to_search:
                return False, f"NEED_SEARCH:{app_name}"
            return False, f"App not installed: {app_name}"
    
    if fallback_to_search:
        return False, f"NEED_SEARCH:{app_name}"
    return False, f"Cannot start: {app_name}"


def restart_adb() -> Tuple[bool, str]:
    """
    Restart ADB service.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        subprocess.run(["adb", "kill-server"], capture_output=True, text=True, timeout=10)
        time.sleep(1)
        subprocess.run(["adb", "start-server"], capture_output=True, text=True, timeout=10)
        
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            devices = [f"Device: {line.split()[0]}" for line in lines[1:] if "\tdevice" in line]
            if devices:
                return True, "ADB restarted successfully\nDevices:\n" + "\n".join(devices)
            return True, "ADB restarted successfully\nNo devices connected"
        return False, "ADB restart failed"
    except Exception as e:
        return False, f"Restart error: {str(e)}"


def check_adb_connection() -> Tuple[bool, str]:
    """
    Check ADB connection status.
    
    Returns:
        Tuple of (connected, status_message)
    """
    try:
        subprocess.run(["adb", "start-server"], capture_output=True, text=True, timeout=5)
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=5)

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            devices = []
            for line in lines[1:]:
                if line.strip():
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        devices.append(f"Device: {parts[0]} - {parts[1]}")

            if devices:
                return True, "ADB service OK\nConnected devices:\n" + "\n".join(devices)
            else:
                return False, "ADB service OK but no devices connected"
        return False, "ADB command execution failed"

    except FileNotFoundError:
        return False, "ADB not installed or not in PATH"
    except subprocess.TimeoutExpired:
        return False, "ADB command timeout"
    except Exception as e:
        return False, f"Error checking ADB connection: {str(e)}"


def get_available_apps(device_id: Optional[str] = None) -> str:
    """
    Get list of third-party apps installed on device.
    
    Args:
        device_id: Optional, specify device ID
    
    Returns:
        App list string
    """
    try:
        cmd = ["adb"]
        if device_id:
            cmd.extend(["-s", device_id])
        cmd.extend(["shell", "pm", "list", "packages", "-3"])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=30
        )
        if result.returncode != 0:
            return "Failed to get apps"
        apps = [line.replace("package:", "").strip() for line in result.stdout.splitlines() if line.strip()]
        apps.sort()
        return "\n".join(apps)
    except Exception as e:
        return str(e)
