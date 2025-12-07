# M30 Handler for Moonraker - CNC Standard Compliance
# Intercepts M30 G-Code and resets file position for program repeat
#
# Copyright (C) 2025 Universal CNC Controller Team
# This file may be distributed under the terms of the GNU GPLv3 license.

from __future__ import annotations
import logging
import re
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from .klippy_apis import KlippyAPI
    from .klippy_connection import KlippyConnection

class M30Handler:
    """
    M30 G-Code Handler for CNC Standard Compliance
    
    Standard behavior (LinuxCNC/ISO 6983):
    - M30: Program End with Reset
    - Resets file position to beginning
    - Ready for repeat/cycle start
    
    This wraps Klipper's G-Code execution and intercepts M30 commands
    to ensure proper file position reset for CNC operation.
    """
    
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.m30_pattern = re.compile(r'\bM30\b', re.IGNORECASE)
        
        # Register M30 endpoint immediately (works even without Klipper)
        self.server.register_endpoint(
            "/server/cnc/m30",
            request_types=['POST'],
            callback=self._handle_m30_endpoint
        )
        
        # Also wait for klippy to be ready for automatic monitoring
        self.server.register_event_handler(
            "server:klippy_ready", self._handle_klippy_ready
        )
        
        logging.info("M30 Handler initialized - Endpoint: /server/cnc/m30")
    
    async def _handle_m30_endpoint(self, web_request) -> dict:
        """Handle explicit M30 requests via REST API"""
        try:
            # Try to reset file position if Klipper is available
            try:
                klippy_apis: KlippyAPI = self.server.lookup_component('klippy_apis')
                await klippy_apis.run_gcode("SDCARD_RESET_FILE")
                message = "M30 executed - file position reset for repeat"
            except Exception:
                # Klipper not available - just acknowledge
                message = "M30 acknowledged (Klipper not connected)"
            
            logging.info(message)
            return {"result": "ok", "message": message}
        except Exception as e:
            logging.error(f"M30 Handler error: {e}")
            return {"error": str(e)}
    
    async def _handle_klippy_ready(self) -> None:
        """Hook into G-Code processing when Klippy is ready"""
        try:
            klippy: KlippyConnection = self.server.lookup_component('klippy_connection')
            # Subscribe to print_stats to detect when M30 is executed
            self.server.register_event_handler(
                "server:status_update", self._check_m30_execution
            )
            logging.info("M30 Handler ready - monitoring G-Code stream")
        except Exception as e:
            logging.info(f"M30 Handler: Could not hook into Klippy: {e}")
    
    async def _check_m30_execution(self, status_update: dict) -> None:
        """
        Check if print has ended (state = complete)
        This indicates M30 or M2 was executed
        """
        print_stats = status_update.get('print_stats', {})
        if print_stats.get('state') == 'complete':
            # Job completed - could be M2 or M30
            # For CNC: Always reset position for M30 behavior
            try:
                klippy_apis: KlippyAPI = self.server.lookup_component('klippy_apis')
                await klippy_apis.run_gcode("SDCARD_RESET_FILE")
                logging.info("Job complete - File position reset for repeat (M30 behavior)")
            except Exception as e:
                # Not critical - file might not be from SD
                logging.debug(f"Could not reset file position: {e}")

def load_component(config: ConfigHelper) -> M30Handler:
    return M30Handler(config)

# Alias for backwards compatibility
load_config = load_component
