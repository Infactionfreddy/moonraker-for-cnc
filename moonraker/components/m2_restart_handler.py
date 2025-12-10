# M2 RESTART Handler for Moonraker - CNC Program Reset
# Monitors M2 RESTART command and resets file position for program repeat
#
# Copyright (C) 2025 Universal CNC Controller Team
# This file may be distributed under the terms of the GNU GPLv3 license.

from __future__ import annotations
import logging
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from .klippy_apis import KlippyAPI
    from .klippy_connection import KlippyConnection

class M2RestartHandler:
    """
    M2 RESTART Handler for CNC Standard Compliance
    
    Monitors for M2 RESTART command execution and automatically
    resets file position to beginning for program repeat.
    
    Behavior:
    - Detects when M2 RESTART is executed (via virtual_sdcard:complete event)
    - Automatically runs SDCARD_RESET_FILE
    - Prepares machine for next cycle start
    
    This replaces the need for ISO/LinuxCNC M30 command by using
    M2 RESTART as the program end with reset command.
    """
    
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        
        # Register REST API endpoint for manual reset
        self.server.register_endpoint(
            "/server/cnc/restart",
            request_types=['POST'],
            callback=self._handle_restart_endpoint
        )
        
        # Wait for klippy to be ready for automatic monitoring
        self.server.register_event_handler(
            "server:klippy_ready", self._handle_klippy_ready
        )
        
        logging.info("M2 RESTART Handler initialized - Endpoint: /server/cnc/restart")
    
    async def _handle_restart_endpoint(self, web_request) -> dict:
        """Handle explicit restart requests via REST API"""
        try:
            # Try to reset file position if Klipper is available
            try:
                klippy_apis: KlippyAPI = self.server.lookup_component('klippy_apis')
                await klippy_apis.run_gcode("SDCARD_RESET_FILE")
                message = "M2 RESTART executed - file position reset for repeat"
            except Exception:
                # Klipper not available - just acknowledge
                message = "M2 RESTART acknowledged (Klipper not connected)"
            
            logging.info(message)
            return {"result": "ok", "message": message}
        except Exception as e:
            logging.error(f"M2 RESTART Handler error: {e}")
            return {"error": str(e)}
    
    async def _handle_klippy_ready(self) -> None:
        """Hook into G-Code processing when Klippy is ready"""
        try:
            klippy: KlippyConnection = self.server.lookup_component('klippy_connection')
            # Subscribe to print_stats to detect when M2 RESTART is executed
            self.server.register_event_handler(
                "server:status_update", self._check_restart_execution
            )
            logging.info("M2 RESTART Handler ready - monitoring for virtual_sdcard:complete event")
        except Exception as e:
            logging.info(f"M2 RESTART Handler: Could not hook into Klippy: {e}")
    
    async def _check_restart_execution(self, status_update: dict) -> None:
        """
        Check if print has ended (state = complete)
        This indicates M2 RESTART was executed
        (triggered by printer.send_event("virtual_sdcard:complete") in cnc_program_control.py)
        """
        print_stats = status_update.get('print_stats', {})
        if print_stats.get('state') == 'complete':
            # Job completed via M2 RESTART
            # Reset file position for program repeat
            try:
                klippy_apis: KlippyAPI = self.server.lookup_component('klippy_apis')
                await klippy_apis.run_gcode("SDCARD_RESET_FILE")
                logging.info("M2 RESTART detected - File position reset for repeat (CNC mode)")
            except Exception as e:
                # Not critical - file might not be from SD
                logging.debug(f"Could not reset file position: {e}")

def load_component(config: ConfigHelper) -> M2RestartHandler:
    return M2RestartHandler(config)

# Alias for backwards compatibility
load_config = load_component
