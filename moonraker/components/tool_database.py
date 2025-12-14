# Moonraker Tool Database API Extension
# Erweitert Moonraker mit REST API Endpunkten für Tool-Management
#
# Copyright (C) 2025 Freddy <infactionfreddy@gmail.com>
#
# This file may be distributed under the terms of the GNU GPLv3 license.

import logging
from tornado.web import HTTPError

class ToolDatabaseAPI:
    """REST API für Tool-Datenbank"""
    
    def __init__(self, server):
        self.server = server
        self.printer = None
        
        # Register API endpoints
        self.server.register_endpoint(
            "/server/tools/list",
            ["GET"],
            self._handle_list_tools
        )
        
        self.server.register_endpoint(
            "/server/tools/add",
            ["POST"],
            self._handle_add_tool
        )
        
        self.server.register_endpoint(
            "/server/tools/update",
            ["POST"],
            self._handle_update_tool
        )
        
        self.server.register_endpoint(
            "/server/tools/delete",
            ["DELETE"],
            self._handle_delete_tool
        )
        
        self.server.register_endpoint(
            "/server/tools/select",
            ["POST"],
            self._handle_select_tool
        )
        
        self.server.register_endpoint(
            "/server/tools/info",
            ["GET"],
            self._handle_tool_info
        )
        
        self.server.register_endpoint(
            "/server/tools/stats",
            ["GET"],
            self._handle_tool_stats
        )
        
        self.server.register_endpoint(
            "/server/tools/monitoring/start",
            ["POST"],
            self._handle_start_monitoring
        )
        
        self.server.register_endpoint(
            "/server/tools/monitoring/stop",
            ["POST"],
            self._handle_stop_monitoring
        )
        
        self.server.register_endpoint(
            "/server/tools/monitoring/status",
            ["GET"],
            self._handle_monitoring_status
        )
        
        self.server.register_endpoint(
            "/server/tools/export",
            ["GET"],
            self._handle_export_tools
        )
        
        self.server.register_endpoint(
            "/server/tools/import",
            ["POST"],
            self._handle_import_tools
        )
        
        logging.info("Tool Database API initialized")
    
    async def _get_klippy_connection(self):
        """Get Klippy connection"""
        if self.printer is None:
            self.printer = self.server.lookup_component('klippy_connection')
        return self.printer
    
    async def _run_gcode(self, gcode):
        """Execute G-Code command"""
        printer = await self._get_klippy_connection()
        result = await printer.run_gcode(gcode)
        return result
    
    async def _query_printer_objects(self, objects):
        """Query printer objects"""
        printer = await self._get_klippy_connection()
        result = await printer.query_objects(objects)
        return result
    
    # API Handlers
    
    async def _handle_list_tools(self, web_request):
        """
        GET /server/tools/list
        
        Query Parameters:
        - type: Filter by tool type (optional)
        
        Response:
        {
          "tools": [
            {
              "id": 1,
              "name": "3mm Drill",
              "type": "drill",
              "diameter": 3.0,
              "length": 50.0,
              "wear_level": 25.5,
              "is_active": true
            },
            ...
          ],
          "current_tool": {
            "id": 11,
            "name": "6mm Endmill"
          }
        }
        """
        tool_type = web_request.get_str('type', None)
        
        # Query tool database
        result = await self._query_printer_objects({'tool_database': None})
        tool_db = result.get('status', {}).get('tool_database', {})
        
        tools = tool_db.get('tools', [])
        
        # Filter by type if specified
        if tool_type:
            tools = [t for t in tools if t['type'] == tool_type]
        
        return {
            'tools': tools,
            'current_tool': tool_db.get('current_tool'),
            'tool_count': len(tools)
        }
    
    async def _handle_add_tool(self, web_request):
        """
        POST /server/tools/add
        
        Body:
        {
          "id": 1,
          "name": "3mm Drill",
          "type": "drill",
          "diameter": 3.0,
          "length": 50.0,
          "flute_length": 25.0,
          "offset_x": 0.0,
          "offset_y": 0.0,
          "offset_z": 0.0,
          "max_rpm": 10000,
          "feedrate": 300.0,
          "plunge_rate": 100.0,
          "angle": 0.0,
          "description": "Standard drill"
        }
        
        Response:
        {
          "success": true,
          "message": "Tool added successfully"
        }
        """
        tool_id = web_request.get_int('id')
        name = web_request.get_str('name')
        tool_type = web_request.get_str('type')
        diameter = web_request.get_float('diameter')
        length = web_request.get_float('length')
        
        # Optional parameters
        flute_length = web_request.get_float('flute_length', 0.0)
        offset_x = web_request.get_float('offset_x', 0.0)
        offset_y = web_request.get_float('offset_y', 0.0)
        offset_z = web_request.get_float('offset_z', 0.0)
        max_rpm = web_request.get_int('max_rpm', 0)
        feedrate = web_request.get_float('feedrate', 0.0)
        plunge_rate = web_request.get_float('plunge_rate', 0.0)
        angle = web_request.get_float('angle', 0.0)
        description = web_request.get_str('description', '')
        
        # Build G-Code command
        gcode = f'ADD_TOOL ID={tool_id} NAME="{name}" TYPE={tool_type} '
        gcode += f'DIAMETER={diameter} LENGTH={length} '
        gcode += f'FLUTE_LENGTH={flute_length} '
        gcode += f'OFFSET_X={offset_x} OFFSET_Y={offset_y} OFFSET_Z={offset_z} '
        gcode += f'MAX_RPM={max_rpm} FEEDRATE={feedrate} PLUNGE_RATE={plunge_rate} '
        gcode += f'ANGLE={angle} DESCRIPTION="{description}"'
        
        await self._run_gcode(gcode)
        
        return {
            'success': True,
            'message': f'Tool {tool_id} added successfully'
        }
    
    async def _handle_update_tool(self, web_request):
        """
        POST /server/tools/update
        
        Body:
        {
          "id": 1,
          "name": "Updated Name",
          "diameter": 3.5,
          ...
        }
        
        Response:
        {
          "success": true,
          "message": "Tool updated successfully"
        }
        """
        tool_id = web_request.get_int('id')
        
        # Build update command with all provided parameters
        gcode = f'UPDATE_TOOL ID={tool_id}'
        
        # Add all optional parameters if provided
        params = [
            ('name', 'NAME', 'str'),
            ('type', 'TYPE', 'str'),
            ('diameter', 'DIAMETER', 'float'),
            ('length', 'LENGTH', 'float'),
            ('flute_length', 'FLUTE_LENGTH', 'float'),
            ('offset_x', 'OFFSET_X', 'float'),
            ('offset_y', 'OFFSET_Y', 'float'),
            ('offset_z', 'OFFSET_Z', 'float'),
            ('max_rpm', 'MAX_RPM', 'int'),
            ('feedrate', 'FEEDRATE', 'float'),
            ('plunge_rate', 'PLUNGE_RATE', 'float'),
            ('angle', 'ANGLE', 'float'),
            ('description', 'DESCRIPTION', 'str'),
            ('is_active', 'IS_ACTIVE', 'int'),
            ('max_runtime', 'MAX_RUNTIME', 'int'),
            ('max_distance', 'MAX_DISTANCE', 'float'),
            ('wear_warning_threshold', 'WEAR_WARNING_THRESHOLD', 'int')
        ]
        
        for param_name, gcode_param, param_type in params:
            try:
                if param_type == 'str':
                    value = web_request.get_str(param_name, None)
                    if value is not None:
                        gcode += f' {gcode_param}="{value}"'
                elif param_type == 'float':
                    value = web_request.get_float(param_name, None)
                    if value is not None:
                        gcode += f' {gcode_param}={value}'
                elif param_type == 'int':
                    value = web_request.get_int(param_name, None)
                    if value is not None:
                        gcode += f' {gcode_param}={value}'
            except:
                pass
        
        await self._run_gcode(gcode)
        
        return {
            'success': True,
            'message': f'Tool {tool_id} updated successfully'
        }
    
    async def _handle_delete_tool(self, web_request):
        """
        DELETE /server/tools/delete
        
        Query Parameters:
        - id: Tool ID to delete
        
        Response:
        {
          "success": true,
          "message": "Tool deleted successfully"
        }
        """
        tool_id = web_request.get_int('id')
        
        gcode = f'REMOVE_TOOL ID={tool_id}'
        await self._run_gcode(gcode)
        
        return {
            'success': True,
            'message': f'Tool {tool_id} deleted successfully'
        }
    
    async def _handle_select_tool(self, web_request):
        """
        POST /server/tools/select
        
        Body:
        {
          "id": 11
        }
        
        Response:
        {
          "success": true,
          "message": "Tool selected",
          "tool": {...}
        }
        """
        tool_id = web_request.get_int('id')
        
        gcode = f'SELECT_TOOL ID={tool_id}'
        await self._run_gcode(gcode)
        
        # Query current tool
        result = await self._query_printer_objects({'tool_database': None})
        current_tool = result.get('status', {}).get('tool_database', {}).get('current_tool')
        
        return {
            'success': True,
            'message': f'Tool {tool_id} selected',
            'tool': current_tool
        }
    
    async def _handle_tool_info(self, web_request):
        """
        GET /server/tools/info
        
        Query Parameters:
        - id: Tool ID (optional, uses current tool if not provided)
        
        Response:
        {
          "tool": {
            "id": 11,
            "name": "6mm Endmill",
            "type": "endmill",
            "diameter": 6.0,
            "length": 60.0,
            "flute_length": 30.0,
            "offset_x": 0.0,
            "offset_y": 0.0,
            "offset_z": 0.0,
            "max_rpm": 12000,
            "feedrate": 500.0,
            "plunge_rate": 150.0,
            "angle": 0.0,
            "description": "4-Flute endmill",
            "total_runtime": 3600.5,
            "total_distance": 15234.7,
            "spindle_on_count": 45,
            "wear_level": 35.2,
            "last_used": "2025-12-14T10:30:00",
            "is_active": true
          }
        }
        """
        tool_id = web_request.get_int('id', None)
        
        if tool_id:
            gcode = f'TOOL_INFO ID={tool_id}'
        else:
            gcode = 'TOOL_INFO'
        
        await self._run_gcode(gcode)
        
        # Query tool database for detailed info
        result = await self._query_printer_objects({'tool_database': None})
        tools = result.get('status', {}).get('tool_database', {}).get('tools', [])
        
        if tool_id:
            tool = next((t for t in tools if t['id'] == tool_id), None)
        else:
            current = result.get('status', {}).get('tool_database', {}).get('current_tool')
            tool = current if current else None
        
        if not tool:
            raise HTTPError(404, "Tool not found")
        
        return {'tool': tool}
    
    async def _handle_tool_stats(self, web_request):
        """
        GET /server/tools/stats
        
        Response:
        {
          "tool_count": 8,
          "active_tools": 7,
          "inactive_tools": 1,
          "total_runtime": 25432.5,
          "total_distance": 125432.8,
          "most_used_tool": {
            "id": 11,
            "name": "6mm Endmill",
            "runtime": 8543.2
          }
        }
        """
        result = await self._query_printer_objects({'tool_database': None})
        tools = result.get('status', {}).get('tool_database', {}).get('tools', [])
        
        active_tools = [t for t in tools if t.get('is_active', True)]
        inactive_tools = [t for t in tools if not t.get('is_active', True)]
        
        total_runtime = sum(t.get('total_runtime', 0) for t in tools)
        total_distance = sum(t.get('total_distance', 0) for t in tools)
        
        most_used = max(tools, key=lambda t: t.get('total_runtime', 0)) if tools else None
        
        return {
            'tool_count': len(tools),
            'active_tools': len(active_tools),
            'inactive_tools': len(inactive_tools),
            'total_runtime': total_runtime,
            'total_distance': total_distance,
            'most_used_tool': most_used
        }
    
    async def _handle_start_monitoring(self, web_request):
        """
        POST /server/tools/monitoring/start
        
        Response:
        {
          "success": true,
          "message": "Tool monitoring started"
        }
        """
        await self._run_gcode('START_TOOL_MONITORING')
        
        return {
            'success': True,
            'message': 'Tool monitoring started'
        }
    
    async def _handle_stop_monitoring(self, web_request):
        """
        POST /server/tools/monitoring/stop
        
        Response:
        {
          "success": true,
          "message": "Tool monitoring stopped"
        }
        """
        await self._run_gcode('STOP_TOOL_MONITORING')
        
        return {
            'success': True,
            'message': 'Tool monitoring stopped'
        }
    
    async def _handle_monitoring_status(self, web_request):
        """
        GET /server/tools/monitoring/status
        
        Response:
        {
          "monitoring_active": true,
          "collision_detected": false,
          "break_detected": false,
          "wear_alert": false,
          "collision_count": 0,
          "baseline_current": 2.5,
          "current_current": 2.3,
          "vibration_level": 0.8
        }
        """
        result = await self._query_printer_objects({'tool_monitoring': None})
        monitoring = result.get('status', {}).get('tool_monitoring', {})
        
        return monitoring
    
    async def _handle_export_tools(self, web_request):
        """
        GET /server/tools/export
        
        Query Parameters:
        - filename: Export filename (optional)
        
        Response:
        {
          "success": true,
          "filename": "tools_export.json",
          "path": "/home/pi/printer_data/tools/tools_export.json"
        }
        """
        filename = web_request.get_str('filename', 'tools_export.json')
        
        gcode = f'EXPORT_TOOLS FILENAME="{filename}"'
        await self._run_gcode(gcode)
        
        return {
            'success': True,
            'filename': filename,
            'path': f'~/printer_data/tools/{filename}'
        }
    
    async def _handle_import_tools(self, web_request):
        """
        POST /server/tools/import
        
        Body:
        {
          "filename": "tools_backup.json",
          "overwrite": true
        }
        
        Response:
        {
          "success": true,
          "message": "Tools imported successfully"
        }
        """
        filename = web_request.get_str('filename')
        overwrite = web_request.get_boolean('overwrite', False)
        
        gcode = f'IMPORT_TOOLS FILENAME="{filename}" OVERWRITE={1 if overwrite else 0}'
        await self._run_gcode(gcode)
        
        return {
            'success': True,
            'message': 'Tools imported successfully'
        }


def load_component(config):
    return ToolDatabaseAPI(config)
