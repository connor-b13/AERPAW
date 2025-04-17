import asyncio
from argparse import ArgumentParser
import datetime
import re
import math
import csv
import random
import zmq
from typing import List, TextIO

from aerpawlib.external import ExternalProcess
from aerpawlib.runner import ZmqStateMachine, state, background, in_background, timed_state, at_init, sleep, expose_field_zmq
from aerpawlib.util import Coordinate, Waypoint, read_from_plan_complete, VectorNED
from aerpawlib.vehicle import Drone

class DummyVehicle (ZmqStateMachine):
    

    _waypoints = []
    _current_waypoint: int=0
    print("COORDINATOR CONNECTED")

    def initialize_args(self, extra_args: List[str]):
        parser = ArgumentParser()
        parser.add_argument("--file", help="Mission plan file path.", required=True)
        args = parser.parse_args(args=extra_args)
        self._waypoints = read_from_plan_complete(args.file)

    _rover_ready = False
    _drone_ready = False
    _rover_taken_off = False
    _drone_taken_off = False

    @expose_field_zmq(name="rover_next_waypoint")
    async def get_rover_next_waypoint(self, _):
        waypoint = self._waypoints[self._current_waypoint]
        coords = Coordinate(*waypoint["pos"])
        return coords

    @expose_field_zmq(name="drone_next_waypoint")
    async def get__next_waypoint(self, _):
        waypoint = self._waypoints[self._current_waypoint]
        coords = Coordinate(*waypoint["pos"])
        # Add 50 to the altitude
        return Coordinate(coords.lat, coords.lon, coords.alt + 50)


    @state(name= "take_off")
    async def state_take_off(self, _):
        await self.transition_runner("reporover","take_off")
        print("Rover taking off")
        self._rover_taken_off = True
        await self.transition_runner("repodrone","take_off")
        print("Drone taking off")
        self._drone_taken_off = True
        return "next_waypoint"
        

    @state(name="ping",first = True)
    async def state_ping(self, _):
        await self.transition_runner("repodrone","ping")
        await self.transition_runner("reporover","ping")
        print("E-VMs pinged")
        return "start_report_ready"

    @state(name="start_report_ready")
    async def state_start_report_ready(self, _):
        if not (self._rover_ready and self._drone_ready):
            await self.transition_runner("repodrone","report_ready")
            await self.transition_runner("reporover","report_ready")
            return "start_report_ready"
        print("Both reported ready")
        return "next_waypoint"
        

    @state(name="rover_ready")
    async def callback_rover_ready(self, _):
        if not self._rover_ready:
            print("rover armed and ready")
            self._rover_ready = True
        return "start_report_ready"
    
    @state(name="drone_ready")
    async def callback_drone_ready(self, _):
        if not self._drone_ready:
            print("drone armed and ready")
            self._drone_ready = True
        return "start_report_ready"

    _rover_at_waypoint = False
    _drone_at_waypoint = False

    @state(name="next_waypoint")
    async def state_next_waypoint(self, _):
        if not (self._rover_taken_off and self._drone_taken_off):
            return "take_off" 
        self._current_waypoint += 1
        if self._current_waypoint >= len(self._waypoints):
            return "rtl"
        print(f"Waypoint {self._current_waypoint}")
        
        waypoint = self._waypoints[self._current_waypoint]
        if waypoint["command"] == 20:
            return "rtl"
        
        await self.transition_runner("reporover", "start_moving"),
        await self.transition_runner("repodrone", "start_moving"),

        self._rover_at_waypoint = False
        self._drone_at_waypoint = False
        
        return "await_in_transit"

    @state(name="await_in_transit")
    async def state_await_in_transit(self, _):
        if not (self._rover_at_waypoint and self. _drone_at_waypoint):
            return "await_in_transit"
        return "next_waypoint"

    @state(name="rtl")
    async def state_rtl(self, _):
        await self.transition_runner("reporover", "rtl")
        await self.transition_runner("repodrone", "rtl")
        return

    @state(name="rover_at_waypoint")
    async def callback_rover_at_waypoint(self, _):
        self._rover_at_waypoint = True
        return "await_in_transit"

    @state(name="drone_at_waypoint")
    async def callback_drone_at_waypoint(self, _):
        self._drone_at_waypoint = True
        return "await_in_transit"