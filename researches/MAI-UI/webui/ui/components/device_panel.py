"""
Device management panel component.
Provides device connection, selection, and status display.
"""

import gradio as gr
from typing import Tuple, List

from core.adb_utils import (
    get_adb_devices,
    connect_wireless_device,
    disconnect_wireless_device,
    restart_adb,
    check_adb_connection,
    device_cache,
)
from ..i18n import t


def create_device_panel() -> Tuple[gr.components.Component, ...]:
    """
    Create device management panel.
    
    Returns:
        Tuple of Gradio components
    """
    with gr.Accordion(t("device.title"), open=True, elem_classes=["mai-accordion"]):
        # Status display
        device_status = gr.Textbox(
            label=t("device.status"),
            value=t("device.not_checked"),
            interactive=False,
            lines=3,
        )
        
        # Device selection
        device_dropdown = gr.Dropdown(
            label=t("device.select_device"),
            choices=[],
            value=None,
            interactive=True,
        )
        
        # Wireless connection
        with gr.Accordion(t("device.wireless_connection"), open=False):
            with gr.Row():
                ip_input = gr.Textbox(
                    label=t("device.ip_address"),
                    placeholder="192.168.1.100",
                    scale=2,
                )
                port_input = gr.Textbox(
                    label=t("device.port"),
                    value="5555",
                    scale=1,
                )
            
            with gr.Row():
                connect_btn = gr.Button(t("device.connect"), variant="primary", size="sm")
                disconnect_btn = gr.Button(t("device.disconnect"), variant="secondary", size="sm")
        
        # ADB controls
        with gr.Row():
            check_btn = gr.Button(t("device.check_adb"), size="sm")
            restart_btn = gr.Button(t("device.restart_adb"), variant="secondary", size="sm")
            refresh_btn = gr.Button(t("common.refresh"), size="sm", elem_classes=["refresh-btn", "refresh-btn-green"])
    
    # Event handlers
    def refresh_devices():
        """Refresh device list."""
        devices, status = get_adb_devices()
        choices = devices if devices else []
        value = devices[0] if devices else None
        if value:
            device_cache.set_device_id(value)
        return gr.update(choices=choices, value=value), status
    
    def select_device(device_id: str):
        """Select a device."""
        if device_id:
            device_cache.set_device_id(device_id)
            return t("device.selected_device", device_id=device_id)
        return t("device.no_device_selected")
    
    def connect_device(ip: str, port: str):
        """Connect wireless device."""
        if not ip:
            return t("device.enter_ip")
        success, msg = connect_wireless_device(ip, port)
        if success:
            devices, _ = get_adb_devices()
            return msg, gr.update(choices=devices)
        return msg, gr.update()
    
    def disconnect_device():
        """Disconnect wireless device."""
        success, msg = disconnect_wireless_device()
        devices, _ = get_adb_devices()
        return msg, gr.update(choices=devices)
    
    def check_connection():
        """Check ADB connection."""
        connected, msg = check_adb_connection()
        return msg
    
    def restart_adb_service():
        """Restart ADB service."""
        success, msg = restart_adb()
        if success:
            devices, status = get_adb_devices()
            return msg + "\n" + status, gr.update(choices=devices)
        return msg, gr.update()
    
    # Wire up events
    refresh_btn.click(
        fn=refresh_devices,
        outputs=[device_dropdown, device_status],
    )
    
    device_dropdown.change(
        fn=select_device,
        inputs=[device_dropdown],
        outputs=[device_status],
    )
    
    connect_btn.click(
        fn=connect_device,
        inputs=[ip_input, port_input],
        outputs=[device_status, device_dropdown],
    )
    
    disconnect_btn.click(
        fn=disconnect_device,
        outputs=[device_status, device_dropdown],
    )
    
    check_btn.click(
        fn=check_connection,
        outputs=[device_status],
    )
    
    restart_btn.click(
        fn=restart_adb_service,
        outputs=[device_status, device_dropdown],
    )
    
    return (
        device_dropdown,
        device_status,
        refresh_btn,
        check_btn,
        restart_btn,
        connect_btn,
        disconnect_btn,
        ip_input,
        port_input,
    )
