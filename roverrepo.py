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



class Drone(ZmqStateMachine):

    print("ROVER WORKING")

    rtl_coords = Drone.position

    # @state(name="test", first = True)
    # async def test(self, _):
    #     await asyncio.sleep(0.5)
    #     print("sleeping")
    #     return "test"

    @state(name="wait_loop", first = True)
    async def state_wait_loop(self,_):
        await asyncio.sleep(0.1)
        return "wait_loop"

    @state(name="report_ready")
    async def state_report_ready(self, _):
        await self.transition_runner("repocoordinator","rover_ready")
        return "wait_loop"
        
    @state(name="start_moving")
    async def state_moving(self, vehicle: Drone):
        coords = await self.query_field("repocoordinator", "rover_next_waypoint")
        print(f"Received coordinates: {coords}")
        print("Moving to Waypoint")
        action = vehicle.goto_coordinates(coords,1)
        await action
        await self.transition_runner("repocoordinator", "rover_at_waypoint")
        return "wait_loop"

    @state(name="rtl")
    async def state_rtl(self, vehicle: Drone):
        action = drone.goto_coordinates(rtl_coords)
        print("Returning to launch")
        await action
        return

    @state(name="ping")
    async def state_ping(self, vehicle: Drone):
        print("PINGED")
        return "wait_loop"

    @state(name="take_off")
    async def state_take_off(self, vehicle: Drone):
        print("Taking off")
        await drone.takeoff(50)
        return "wait_loop"