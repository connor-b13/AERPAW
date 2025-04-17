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

class Drone (ZmqStateMachine):

    rtl_coords = None

    print("DRONE WORKING")

    @state(name="wait_loop", first = True)
    async def state_wait_loop(self,_):    
        #print("WAITINGG")
        await asyncio.sleep(0.1)
        return "wait_loop"

    @state(name="report_ready")
    async def state_report_ready(self, _):
        print("Reporting Ready")
        await self.transition_runner("repocoordinator","drone_ready")
        print("Reported Ready")
        return "wait_loop"

    @state(name="start_moving")
    async def state_start_moving(self, vehicle: Drone):
        coords = await self.query_field("repocoordinator", "drone_next_waypoint")
        print("Moving to Waypoint")
        action = vehicle.goto_coordinates(coords)
        await action
        await self.transition_runner("repocoordinator", "drone_at_waypoint")
        return "wait_loop"

    @state(name="take_off")
    async def state_take_off(self, vehicle: Drone):
        print("taking off")
        await drone.takeoff(50)
        print("taken off")
        self.rtl_coords = Drone.position
        return "start_moving"

    @state(name="rtl")
    async def state_rtl(self, vehicle: Drone):
        await vehicle.goto_coordinates(self.rtl_coords)
        await Drone.land()
        return 

    @state(name="ping")
    async def state_ping(self, vehicle: Drone):
        print("PINGED")
        return "wait_loop"