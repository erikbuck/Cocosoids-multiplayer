"""
 * Licensed to the Apache Software Foundation (ASF) under one or more
 * contributor license agreements.  See the NOTICE file distributed with
 * this work for additional information regarding copyright ownership.
 * The ASF licenses this file to You under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance with
 * the License.  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 * AUTHOR: Erik M. Buck
 *
 """
import CommonLayers
import cocos
import pyglet
import socket
import sys
from time import sleep
from sys import stdin, exit

from PodSixNet.Connection import connection, ConnectionListener
from thread import *

class ChatClient(ConnectionListener):
    """
    """
    def Loop(self):
        connection.Pump()
        self.Pump()

    #######################################
    ### Network event/message callbacks ###
    #######################################

    def Network_players(self, data):
        print "*** players: " + ", ".join([p for p in data['players']])

    def Network_message(self, data):
        print data['who'] + ": " + data['message']

    # built in stuff

    def Network_connected(self, data):
        print "You are now connected to the server"

    def Network_error(self, data):
        print 'error:', data['error'][1]
        connection.Close()

    def Network_disconnected(self, data):
        print 'Server disconnected'
        exit()


class ClientPlayLayerAction(cocos.actions.Action):
    """ 
    """
    
    def handleLocalKeyboard(self):
        """ """
        if pyglet.window.key.LEFT in self.target.keys_being_pressed:
            self.target.crotatePlayer(-5)
        if pyglet.window.key.RIGHT in self.target.keys_being_pressed:
            self.target.crotatePlayer(5)
        if pyglet.window.key.UP in self.target.keys_being_pressed:
            self.target.cthrustPlayer()
        
    def step(self, dt):
        """ """
        self.handleLocalKeyboard()


class ClientPlayLayer(CommonLayers.PlayLayer):
    """
    """
    
    def on_key_press(self, key, modifiers):
        """ """
        super( ClientPlayLayer, self ).on_key_press(\
            key, modifiers)
        if pyglet.window.key.SPACE == key:
            connection.Send({"action": "fireBulletForPlayer",
                "fireBulletForPlayer":''})

    def crotatePlayer(self, deg):
        connection.Send({"action": "rotatePlayer",
            "rotatePlayer":deg})

    def cthrustPlayer(self):
        connection.Send({"action": "thrustPlayer",
            "thrustPlayer":''})


class ClientNetworkAction(ClientPlayLayerAction, ChatClient):
    """    
    """
    
    def __init__(self, host, port):
        """ """
        super( ClientNetworkAction, self ).__init__()
        if not host:
            host = socket.gethostbyname(socket.gethostname())
        
        if not port:
            port = 8000
        
        self.Connect((host, port))
        print "Client started"
    
    def start(self):
        """ """
    
    def step(self, dt):
        """ """
        super( ClientNetworkAction, self ).step(dt)
        self.Loop()

    def Network_info(self, data):
        """ """
        live_instances = CommonLayers.GameSprite.live_instances
        for info in data['info']:
            id = info['id']
            inst = None
            if not id in live_instances:
                if info['type'] == 'a':
                    inst = CommonLayers.Asteroid(id=id)
                    self.target.batch.add(inst)
                    inst.updateWithInfo(info)
                    inst.motion_vector = (0,0)
                    inst.start()
                
                elif info['type'] == 'b':
                    inst = CommonLayers.Bullet(id=id)
                    self.target.batch.add(inst)
                    inst.updateWithInfo(info)
                    inst.motion_vector = (0,0)
                    inst.start()
                
                elif info['type'] == 'p':
                    inst = CommonLayers.Player(
                        player_id=info['player_id'], id=id)
                    self.target.batch.add(inst)
                    inst.motion_vector = (0,0)
                    inst.updateWithInfo(info)
                    inst.start()
                    if CommonLayers.PlayLayer.ownID != inst.player_id:
                        inst.color = (255, 255, 0)
                    else:
                        self.target.updateLivesRemaining(
                            inst.lives_remaining)
                            
                elif info['type'] == 'e':
                    inst = CommonLayers.Explosion(id=id)
                    self.target.batch.add(inst)
                    inst.updateWithInfo(info)
                    inst.motion_vector = (0,0)
                    inst.start()
            else:
                inst = live_instances[id]
                inst.updateWithInfo(info)
            
            if inst:
                CommonLayers.GameSprite.live_instances[id] = inst


class ClientGamePlayLayer(ClientPlayLayer):
    """
    """

    def __init__(self):
        """ """
        # Delete all existing asteroids before initializing a new
        # play layer
        asteroids = CommonLayers.GameSprite.getInstances(\
                CommonLayers.Asteroid)
        for asteroid in asteroids:
            asteroid.markForDeath()
        
        super( ClientGamePlayLayer, self ).__init__()
        self.isWaitingToSpawnAsteroids = True

    def addAsteroids(self, count=8):
        """ """
        super( ClientGamePlayLayer, self ).addAsteroids(count)
        self.isWaitingToSpawnAsteroids = False

    def getInfo(self):
        """ """
        return [x.getInfo() for x in
            CommonLayers.GameSprite.live_instances.values()]


class GameClient(object):
    """
    """
    def __init__(self):
        """ """
        super( GameClient, self ).__init__()
        
        self.game_layer = ClientGamePlayLayer()
        self.ui_layer = CommonLayers.UILayer()
        self.ui_layer.add(self.game_layer)
        
        self.game_scene = cocos.scene.Scene(self.ui_layer)

    def start(self, host, port):
        """ """
        # setup to handle asynchronous network messages
        self.game_layer.do(ClientNetworkAction(host, port))

    def get_scene(self):
        """ """
        return self.game_scene


if __name__ == "__main__":
    assert False
