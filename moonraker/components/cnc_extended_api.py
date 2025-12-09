# CNC M-Codes Extended Handler for Moonraker
# Comprehensive M-Code API endpoints for CNC operations
#
# Copyright (C) 2025 Universal CNC Controller Team
# This file may be distributed under the terms of the GNU GPLv3 license.

from __future__ import annotations
import logging
import asyncio
from typing import TYPE_CHECKING, Dict, Any
if TYPE_CHECKING:
    from ..confighelper import ConfigHelper
    from .klippy_apis import KlippyAPI as APIComp

class CNCMCodesHandler:
    """
    Extended CNC M-Code Handler for Moonraker
    
    Provides REST API endpoints for:
    - Tool change operations (M6)
    - Coolant control monitoring
    - Spindle status monitoring
    - Program state management
    - Modal state backup/restore
    """
    
    def __init__(self, config: ConfigHelper) -> None:
        self.server = config.get_server()
        self.klippy_apis: APIComp | None = None
        
        # Register REST API endpoints
        self.server.register_endpoint(
            "/server/cnc/tool_change",
            request_types=['POST'],
            callback=self._handle_tool_change
        )
        
        self.server.register_endpoint(
            "/server/cnc/status",
            request_types=['GET'],
            callback=self._handle_cnc_status
        )
        
        self.server.register_endpoint(
            "/server/cnc/coolant",
            request_types=['GET', 'POST'],
            callback=self._handle_coolant
        )
        
        self.server.register_endpoint(
            "/server/cnc/spindle",
            request_types=['GET', 'POST'],
            callback=self._handle_spindle
        )
        
        self.server.register_endpoint(
            "/server/cnc/modal_state",
            request_types=['GET', 'POST', 'DELETE'],
            callback=self._handle_modal_state
        )
        
        self.server.register_endpoint(
            "/server/cnc/pallet_change",
            request_types=['POST'],
            callback=self._handle_pallet_change
        )
        
        self.server.register_endpoint(
            "/server/cnc/digital_io",
            request_types=['GET', 'POST'],
            callback=self._handle_digital_io
        )
        
        self.server.register_endpoint(
            "/server/cnc/analog_io",
            request_types=['GET', 'POST'],
            callback=self._handle_analog_io
        )
        
        self.server.register_endpoint(
            "/server/cnc/subroutine",
            request_types=['POST'],
            callback=self._handle_subroutine
        )
        
        # Wait for Klippy to be ready
        self.server.register_event_handler(
            "server:klippy_ready", self._handle_klippy_ready
        )
        
        logging.info("CNC M-Codes Handler initialized")
        logging.info("  - Tool change: POST /server/cnc/tool_change")
        logging.info("  - CNC status: GET /server/cnc/status")
        logging.info("  - Coolant: GET/POST /server/cnc/coolant")
        logging.info("  - Spindle: GET/POST /server/cnc/spindle")
        logging.info("  - Modal state: GET/POST/DELETE /server/cnc/modal_state")
        logging.info("  - Pallet change: POST /server/cnc/pallet_change")
        logging.info("  - Digital I/O: GET/POST /server/cnc/digital_io")
        logging.info("  - Analog I/O: GET/POST /server/cnc/analog_io")
        logging.info("  - Subroutine: POST /server/cnc/subroutine")
    
    async def _handle_klippy_ready(self) -> None:
        """Initialize Klippy APIs when ready"""
        self.klippy_apis = self.server.lookup_component('klippy_apis')
        logging.info("CNC M-Codes Handler: Connected to Klippy")
    
    async def _handle_tool_change(self, web_request) -> Dict[str, Any]:
        """
        Handle M6 Tool Change
        
        POST /server/cnc/tool_change
        {
            "tool": 5,  // Tool number to load
            "manual": true,  // Manual or automatic tool change
            "pause": true  // Pause for operator confirmation
        }
        """
        tool = web_request.get_int('tool', 0)
        manual = web_request.get_boolean('manual', True)
        pause = web_request.get_boolean('pause', True)
        
        logging.info(f"CNC Tool Change: T{tool} (manual={manual}, pause={pause})")
        
        if not self.klippy_apis:
            return {
                'result': 'error',
                'message': 'Klippy not connected'
            }
        
        try:
            # Build G-Code command sequence for tool change
            commands = []
            
            if pause:
                commands.append("M0")  # Pause for tool change
            
            commands.append(f"T{tool}")  # Select tool
            
            if manual:
                commands.append("M117 Insert Tool T{tool} and resume")
            
            # Execute commands
            result = await self.klippy_apis.run_gcode("\n".join(commands))
            
            return {
                'result': 'success',
                'tool': tool,
                'manual': manual,
                'commands': commands
            }
        except Exception as e:
            logging.exception(f"Tool change failed: {e}")
            return {
                'result': 'error',
                'message': str(e)
            }
    
    async def _handle_cnc_status(self, web_request) -> Dict[str, Any]:
        """
        Get comprehensive CNC status
        
        GET /server/cnc/status
        """
        if not self.klippy_apis:
            return {
                'result': 'error',
                'message': 'Klippy not connected'
            }
        
        try:
            # Query CNC M-Codes module status
            result = await self.klippy_apis.query_objects(
                {'cnc_m_codes': None}
            )
            
            status = result.get('cnc_m_codes', {})
            
            return {
                'result': 'success',
                'status': status
            }
        except Exception as e:
            logging.exception(f"Status query failed: {e}")
            return {
                'result': 'error',
                'message': str(e)
            }
    
    async def _handle_coolant(self, web_request) -> Dict[str, Any]:
        """
        Control coolant
        
        GET /server/cnc/coolant - Get coolant status
        POST /server/cnc/coolant - Control coolant
        {
            "mist": true/false,
            "flood": true/false
        }
        """
        if web_request.get_request_type() == 'GET':
            # Get status
            if not self.klippy_apis:
                return {'result': 'error', 'message': 'Klippy not connected'}
            
            try:
                result = await self.klippy_apis.query_objects(
                    {'cnc_m_codes': None}
                )
                status = result.get('cnc_m_codes', {})
                
                return {
                    'result': 'success',
                    'coolant_mist': status.get('coolant_mist', False),
                    'coolant_flood': status.get('coolant_flood', False)
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
        
        else:  # POST
            mist = web_request.get_boolean('mist', None)
            flood = web_request.get_boolean('flood', None)
            
            if not self.klippy_apis:
                return {'result': 'error', 'message': 'Klippy not connected'}
            
            commands = []
            if mist is not None:
                commands.append("M7" if mist else "M9")
            if flood is not None:
                commands.append("M8" if flood else "M9")
            
            try:
                await self.klippy_apis.run_gcode("\n".join(commands))
                return {
                    'result': 'success',
                    'mist': mist,
                    'flood': flood
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
    
    async def _handle_spindle(self, web_request) -> Dict[str, Any]:
        """
        Control spindle
        
        GET /server/cnc/spindle - Get spindle status
        POST /server/cnc/spindle - Control spindle
        {
            "enable": true/false,
            "direction": "cw"/"ccw",  // Optional
            "speed": 1000  // Optional RPM
        }
        """
        if web_request.get_request_type() == 'GET':
            # Get status
            if not self.klippy_apis:
                return {'result': 'error', 'message': 'Klippy not connected'}
            
            try:
                result = await self.klippy_apis.query_objects(
                    {'cnc_m_codes': None}
                )
                status = result.get('cnc_m_codes', {})
                
                return {
                    'result': 'success',
                    'spindle_running': status.get('spindle_running', False),
                    'spindle_direction': status.get('spindle_direction', 0),
                    'spindle_speed': status.get('spindle_speed', 0)
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
        
        else:  # POST
            enable = web_request.get_boolean('enable')
            direction = web_request.get('direction', 'cw').lower()
            speed = web_request.get_int('speed', 0)
            
            if not self.klippy_apis:
                return {'result': 'error', 'message': 'Klippy not connected'}
            
            commands = []
            
            if enable:
                if speed > 0:
                    commands.append(f"S{speed}")
                
                if direction == 'cw':
                    commands.append("M3")
                elif direction == 'ccw':
                    commands.append("M4")
                else:
                    return {'result': 'error', 'message': 'Invalid direction'}
            else:
                commands.append("M5")
            
            try:
                await self.klippy_apis.run_gcode("\n".join(commands))
                return {
                    'result': 'success',
                    'enable': enable,
                    'direction': direction if enable else None,
                    'speed': speed if enable else 0
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
    
    async def _handle_modal_state(self, web_request) -> Dict[str, Any]:
        """
        Manage modal state
        
        GET /server/cnc/modal_state - Get saved states count
        POST /server/cnc/modal_state - Save or restore state
        {
            "action": "save" | "restore" | "invalidate"
        }
        DELETE /server/cnc/modal_state - Clear all saved states
        """
        if not self.klippy_apis:
            return {'result': 'error', 'message': 'Klippy not connected'}
        
        request_type = web_request.get_request_type()
        
        if request_type == 'GET':
            try:
                result = await self.klippy_apis.query_objects(
                    {'cnc_m_codes': None}
                )
                # Would need to add state_count to get_status in Klipper module
                return {
                    'result': 'success',
                    'message': 'Modal state tracking active'
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
        
        elif request_type == 'POST':
            action = web_request.get('action', 'save')
            
            command_map = {
                'save': 'M70',
                'restore': 'M72',
                'invalidate': 'M71',
                'auto_save': 'M73'
            }
            
            command = command_map.get(action)
            if not command:
                return {
                    'result': 'error',
                    'message': f'Invalid action: {action}'
                }
            
            try:
                await self.klippy_apis.run_gcode(command)
                return {
                    'result': 'success',
                    'action': action,
                    'command': command
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
        
        elif request_type == 'DELETE':
            # Clear all saved states by sending M71 repeatedly
            try:
                # Send M71 multiple times to clear stack
                for _ in range(10):  # Max 10 nested states
                    try:
                        await self.klippy_apis.run_gcode("M71")
                    except:
                        break  # No more states to clear
                
                return {
                    'result': 'success',
                    'message': 'All modal states cleared'
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
        
        return {'result': 'error', 'message': 'Invalid request type'}
    
    async def _handle_pallet_change(self, web_request) -> Dict[str, Any]:
        """
        Handle M60 Pallet Change
        
        POST /server/cnc/pallet_change
        {
            "pause": true  // Pause for operator action
        }
        """
        pause = web_request.get_boolean('pause', True)
        
        logging.info(f"CNC Pallet Change: M60 (pause={pause})")
        
        if not self.klippy_apis:
            return {
                'result': 'error',
                'message': 'Klippy not connected'
            }
        
        try:
            # Execute M60 command
            await self.klippy_apis.run_gcode("M60")
            
            return {
                'result': 'success',
                'command': 'M60',
                'pause': pause,
                'message': 'Pallet change initiated - Exchange pallet and resume'
            }
        except Exception as e:
            logging.exception(f"Pallet change failed: {e}")
            return {
                'result': 'error',
                'message': str(e)
            }
    
    async def _handle_digital_io(self, web_request) -> Dict[str, Any]:
        """
        Control Digital I/O (M62-M66)
        
        GET /server/cnc/digital_io - Get all digital I/O states
        
        POST /server/cnc/digital_io - Control digital output
        {
            "pin": 0,  // Pin number (P parameter)
            "value": true,  // true/false for ON/OFF
            "synchronized": false  // false=immediate (M64/M65), true=synchronized (M62/M63)
        }
        
        Or wait on input:
        {
            "action": "wait",
            "pin": 0,  // Pin number
            "mode": 3,  // 0=IMMEDIATE, 1=RISE, 2=FALL, 3=HIGH, 4=LOW
            "timeout": 5.0  // Timeout in seconds
        }
        """
        if web_request.get_request_type() == 'GET':
            # Get all digital I/O states
            if not self.klippy_apis:
                return {'result': 'error', 'message': 'Klippy not connected'}
            
            try:
                result = await self.klippy_apis.query_objects(
                    {'cnc_extended_m_codes': None}
                )
                status = result.get('cnc_extended_m_codes', {})
                
                # Extract digital I/O state (would need to add to get_status in Klipper)
                return {
                    'result': 'success',
                    'message': 'Digital I/O status retrieved'
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
        
        else:  # POST
            action = web_request.get('action', 'set')
            
            if action == 'wait':
                # M66 - Wait on input
                pin = web_request.get_int('pin')
                mode = web_request.get_int('mode', 0)
                timeout = web_request.get_float('timeout', 0.0)
                analog = web_request.get_boolean('analog', False)
                
                if not self.klippy_apis:
                    return {'result': 'error', 'message': 'Klippy not connected'}
                
                try:
                    if analog:
                        command = f"M66 E{pin} L{mode} Q{timeout}"
                    else:
                        command = f"M66 P{pin} L{mode} Q{timeout}"
                    
                    await self.klippy_apis.run_gcode(command)
                    
                    return {
                        'result': 'success',
                        'command': command,
                        'message': f'Waiting on {"analog" if analog else "digital"} input {pin}'
                    }
                except Exception as e:
                    return {'result': 'error', 'message': str(e)}
            
            else:  # Set output
                pin = web_request.get_int('pin')
                value = web_request.get_boolean('value')
                synchronized = web_request.get_boolean('synchronized', False)
                
                if not self.klippy_apis:
                    return {'result': 'error', 'message': 'Klippy not connected'}
                
                try:
                    # Choose appropriate M-Code
                    if synchronized:
                        # M62 (ON) or M63 (OFF) - synchronized with motion
                        command = f"M62 P{pin}" if value else f"M63 P{pin}"
                    else:
                        # M64 (ON) or M65 (OFF) - immediate
                        command = f"M64 P{pin}" if value else f"M65 P{pin}"
                    
                    await self.klippy_apis.run_gcode(command)
                    
                    return {
                        'result': 'success',
                        'command': command,
                        'pin': pin,
                        'value': value,
                        'synchronized': synchronized
                    }
                except Exception as e:
                    return {'result': 'error', 'message': str(e)}
    
    async def _handle_analog_io(self, web_request) -> Dict[str, Any]:
        """
        Control Analog I/O (M67-M68)
        
        GET /server/cnc/analog_io - Get all analog output states
        
        POST /server/cnc/analog_io - Set analog output
        {
            "pin": 0,  // Pin number (E parameter)
            "value": 5.0,  // Analog value (Q parameter)
            "synchronized": false  // false=immediate (M68), true=synchronized (M67)
        }
        """
        if web_request.get_request_type() == 'GET':
            # Get all analog I/O states
            if not self.klippy_apis:
                return {'result': 'error', 'message': 'Klippy not connected'}
            
            try:
                result = await self.klippy_apis.query_objects(
                    {'cnc_extended_m_codes': None}
                )
                status = result.get('cnc_extended_m_codes', {})
                
                # Extract analog I/O state (would need to add to get_status in Klipper)
                return {
                    'result': 'success',
                    'message': 'Analog I/O status retrieved'
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
        
        else:  # POST
            pin = web_request.get_int('pin')
            value = web_request.get_float('value')
            synchronized = web_request.get_boolean('synchronized', False)
            
            if not self.klippy_apis:
                return {'result': 'error', 'message': 'Klippy not connected'}
            
            try:
                # Choose appropriate M-Code
                if synchronized:
                    # M67 - synchronized with motion
                    command = f"M67 E{pin} Q{value}"
                else:
                    # M68 - immediate
                    command = f"M68 E{pin} Q{value}"
                
                await self.klippy_apis.run_gcode(command)
                
                return {
                    'result': 'success',
                    'command': command,
                    'pin': pin,
                    'value': value,
                    'synchronized': synchronized
                }
            except Exception as e:
                return {'result': 'error', 'message': str(e)}
    
    async def _handle_subroutine(self, web_request) -> Dict[str, Any]:
        """
        Execute Subroutine (M98/M99)
        
        POST /server/cnc/subroutine
        {
            "action": "call" | "return",
            "program": 100,  // Program number (for M98)
            "repeats": 1  // Number of repeats (L parameter for M98)
        }
        """
        action = web_request.get('action', 'call')
        
        if not self.klippy_apis:
            return {
                'result': 'error',
                'message': 'Klippy not connected'
            }
        
        try:
            if action == 'call':
                # M98 - Call subroutine
                program = web_request.get_int('program')
                repeats = web_request.get_int('repeats', 1)
                
                command = f"M98 P{program}"
                if repeats > 1:
                    command += f" L{repeats}"
                
                await self.klippy_apis.run_gcode(command)
                
                return {
                    'result': 'success',
                    'command': command,
                    'action': 'call',
                    'program': program,
                    'repeats': repeats,
                    'message': f'Called subroutine O{program} ({repeats} times)'
                }
            
            elif action == 'return':
                # M99 - Return from subroutine
                await self.klippy_apis.run_gcode("M99")
                
                return {
                    'result': 'success',
                    'command': 'M99',
                    'action': 'return',
                    'message': 'Returned from subroutine'
                }
            
            else:
                return {
                    'result': 'error',
                    'message': f'Invalid action: {action}'
                }
        
        except Exception as e:
            logging.exception(f"Subroutine operation failed: {e}")
            return {
                'result': 'error',
                'message': str(e)
            }

def load_component(config: ConfigHelper) -> CNCMCodesHandler:
    return CNCMCodesHandler(config)
