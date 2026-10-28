#!/usr/bin/env python3
# Copyright 2026 Robby
# SPDX-License-Identifier: Apache-2.0
"""Add or remove the Office costmap exercise's extra obstacle."""
import argparse
import sys

from gz.transport import Node
from gz.msgs.boolean_pb2 import Boolean
from gz.msgs.entity_factory_pb2 import EntityFactory
from gz.msgs.entity_pb2 import Entity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['add', 'remove'])
    args = parser.parse_args()
    name = 'costmap_demo_box'
    if args.command == 'add':
        request = EntityFactory()
        request.name = name
        request.allow_renaming = False
        request.sdf = f'''<sdf version="1.10"><model name="{name}">
  <static>true</static><pose>11.25 -5.35 0.4 0 0 0</pose>
  <link name="box">
    <collision name="collision"><geometry><box><size>0.6 0.6 0.8</size></box></geometry></collision>
    <visual name="visual"><geometry><box><size>0.6 0.6 0.8</size></box></geometry>
      <material><ambient>1 0.3 0 1</ambient><diffuse>1 0.3 0 1</diffuse></material>
    </visual>
  </link>
</model></sdf>'''
        service = '/world/husarion_office/create'
        request_type = EntityFactory
    else:
        request = Entity()
        request.name = name
        request.type = 2  # MODEL
        service = '/world/husarion_office/remove'
        request_type = Entity
    transport = Node()
    replied, response = transport.request(service, request, request_type, Boolean, 5000)
    if not replied or response is None or not response.data:
        print('Obstacle request failed. Check that Office is running and the model name is available.',
              file=sys.stderr)
        return 1
    print(f'Obstacle {args.command} request accepted: {name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
