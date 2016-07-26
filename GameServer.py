import CommonLayers
import cocos
import pyglet

class ServerPlayLayerAction(cocos.actions.Action):
    """ 
    """
    
    def handleLocalKeyboard(self):
        """ """
        if pyglet.window.key.LEFT in self.target.keys_being_pressed:
            self.target.rotatePlayer(self.target.ownID, -5)
        if pyglet.window.key.RIGHT in self.target.keys_being_pressed:
            self.target.rotatePlayer(self.target.ownID, 5)
        if pyglet.window.key.UP in self.target.keys_being_pressed:
            self.target.thrustPlayer(self.target.ownID)

    def step(self, dt):
        """ """
        self.handleLocalKeyboard()
        CommonLayers.GameSprite.handleCollisions()
        self.spawnAsteroids()

    def spawnAsteroids(self):
        """ """
        if not self.target.isWaitingToSpawnAsteroids:
            asteroids = CommonLayers.GameSprite.getInstances(\
                CommonLayers.Asteroid)
            if 0 == len(asteroids):
                self.target.isWaitingToSpawnAsteroids = True
                self.target.do(cocos.actions.Delay(5) + \
                    cocos.actions.CallFuncS(\
                    ServerGamePlayLayer.addAsteroids))
    

class ServerPlayLayer(CommonLayers.PlayLayer):
    """
    """
    
    def on_key_press(self, key, modifiers):
        """ """
        super( ServerPlayLayer, self ).on_key_press(\
            key, modifiers)
        if pyglet.window.key.SPACE == key:
            self.fireBulletForPlayer(self.ownID)


class ServerGamePlayLayer(ServerPlayLayer):
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
        
        super( ServerGamePlayLayer, self ).__init__()
        self.isWaitingToSpawnAsteroids = True

    def addAsteroids(self, count=8):
        """ """
        super( ServerGamePlayLayer, self ).addAsteroids(count)
        self.isWaitingToSpawnAsteroids = False

    def getInfo(self):
        """ """
        return [x.getInfo() for x in
            CommonLayers.GameSprite.live_instances.values()]

######################################################################
# MULTI-PLAYER SUPPORT STARTS HERE
######################################################################
import socket
import sys
from time import sleep, localtime
from weakref import WeakKeyDictionary
from PodSixNet.Server import Server
from PodSixNet.Channel import Channel

class ClientChannel(Channel):
    """
    This entire class has been added.
    This is the server representation of a single connected client.
    """
    def __init__(self, *args, **kwargs):
        self.nickname = "anonymous"
        Channel.__init__(self, *args, **kwargs)
        self.commands = []
    
    def Close(self):
        self._server.DelPlayer(self)

    ##################################
    ### Network specific callbacks ###
    ##################################

    def Network_message(self, data):
        self._server.SendToAll({"action": "message",
            "message": data['message'],
            "who": self.nickname})

    def Network_nickname(self, data):
        self.nickname = data['nickname']
        self._server.SendPlayers()

    def Network_rotatePlayer(self, data):
        self.commands.append(data)

    def Network_thrustPlayer(self, data):
        self.commands.append(data)

    def Network_fireBulletForPlayer(self, data):
        self.commands.append(data)


class ChatServer(Server):
    """
        This entire class has been added.
        This is the network server itself.
    """
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        Server.__init__(self, *args, **kwargs)
        self.client_channels = WeakKeyDictionary()
        print 'Server launched'

    def Connected(self, channel, addr):
        self.AddPlayer(channel)

    def AddPlayer(self, player):
        print "New Player" + str(player.addr)
        self.client_channels[player] = True
        self.SendPlayers()

    def DelPlayer(self, player):
        print "Deleting Player" + str(player.addr)
        del self.client_channels[player]
        self.SendPlayers()

    def SendPlayers(self):
        self.SendToAll({"action": "players",
            "players": [p.nickname for p in self.client_channels]})

    def SendToAll(self, data):
        [p.Send(data) for p in self.client_channels]


class ServerNetworkAction(ServerPlayLayerAction):
    """ 
    This entire class has been added
    """
    
    def __init__(self):
        """ """
        super( ServerNetworkAction, self ).__init__()
        self.chat_server = None
    
    def start(self):
        """ """
        host = socket.gethostbyname(socket.gethostname())
        port = 8000
        self.chat_server = ChatServer(localaddr=(host, port))
    
    def step(self, dt):
        """ """
        super( ServerNetworkAction, self ).step(dt)
        
        for channel in self.chat_server.client_channels: # Is this thread sage?!?
            if not channel.addr[0] in self.target.players:
                self.target.addPlayer(channel.addr[0])
            
            commands = channel.commands # Is this thread sage?!?
            for command in commands:
                if command['action'] == 'rotatePlayer':
                    deg = command['rotatePlayer']
                    self.target.rotatePlayer(channel.addr[0], deg)
                elif command['action'] == 'thrustPlayer':
                    self.target.thrustPlayer(channel.addr[0])
                elif command['action'] == 'fireBulletForPlayer':
                    self.target.fireBulletForPlayer(channel.addr[0])
                else:
                    print 'Error: Unknown command,', command,\
                        'from client,', channel

            channel.commands = [] # Is this thread sage?!?
    
        new_info = self.target.getInfo()
        self.chat_server.SendToAll({"action": "info",
            "info":new_info})
        self.chat_server.Pump()

######################################################################
# MULTI-PLAYER SUPPORT ENDS HERE
######################################################################


class GameServer(object):
    """
    """
    def __init__(self):
        """ """
        super( GameServer, self ).__init__()
        
        self.game_layer = ServerGamePlayLayer()
        self.game_layer.addAsteroids(3)
        self.ui_layer = CommonLayers.UILayer()
        self.ui_layer.add(self.game_layer)
        
        self.game_scene = cocos.scene.Scene(self.ui_layer)

    def start(self):
        """ """
        # setup to handle asynchronous network messages
        self.game_layer.do(ServerNetworkAction())   # Changed for multi-player
        #self.game_layer.addPlayer(\                # Changed for multi-player
        #    CommonLayers.PlayLayer.ownID)          # Changed for multi-player

    def get_scene(self):
        """ """
        return self.game_scene


if __name__ == "__main__":
    assert False
