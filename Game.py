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
import GameServer
import cocos
from cocos.scenes.transitions import FadeTRTransition
import pyglet
import sys
import GameClient                       # Added for multi-player


class Game(object):
    """
    """
    
    default_title = "Cocosoids"
    default_window_width = 1024
    default_window_height = 768

    def __init__(self):
        """ """
        super( Game, self ).__init__()

        director_width = Game.default_window_width
        director_height = Game.default_window_height

        caption = Game.default_title + ' ' + \
            CommonLayers.PlayLayer.ownID
        cocos.director.director.init(
            director_width, director_height,
            caption = caption, fullscreen=False)

        intro_layer = CommonLayers.PlayLayer()
        intro_layer.anchor_x = director_width * 0.5
        intro_layer.anchor_y = director_height * 0.5
        intro_layer.addAsteroids(3)

        intro_menu = IntroMenu(self)
        intro_layer.add(intro_menu)
        
        self.intro_scene = cocos.scene.Scene(intro_layer)

    def run(self, host=None, port=None):
        """ """
        self.host = host
        self.port = port
        cocos.director.director.set_show_FPS(True)
        cocos.director.director.run (self.intro_scene)

    def on_join_game( self ):
        """ """
        gameInstance = GameClient.GameClient()   # Changed for multi-player
        cocos.director.director.replace(FadeTRTransition(
            gameInstance.get_scene(), 2))
        gameInstance.start(self.host, self.port) # Changed for multi-player

    def on_host_game( self ):
        """ """
        gameInstance = GameServer.GameServer()
        cocos.director.director.replace(FadeTRTransition(
            gameInstance.get_scene(), 2))
        gameInstance.start()

    def on_name( self, value ):
        """ """
        self.player_name = value

    def on_quit( self ):
        """ """
        pyglet.app.exit()


class IntroMenu(cocos.menu.Menu):
    """
    """
    def __init__( self, game ):
        """ """
        super( IntroMenu, self ).__init__()
        self.game = game
        self.font_item = {
            'font_name': 'Arial',
            'font_size': 32,
            'bold': True,
            'color': (220, 200, 220, 100),
        }
        self.font_item_selected = {
            'font_name': 'Arial',
            'font_size': 42,
            'bold': True,
            'color': (255, 255, 255, 255),
        }

        l = []
        l.append( cocos.menu.MenuItem('Join Game',
            self.game.on_join_game ) )
        l.append( cocos.menu.MenuItem('Host Game',
            self.game.on_host_game ) )
        l.append( cocos.menu.EntryMenuItem('Name:',
            self.game.on_name,
            CommonLayers.PlayLayer.ownID) )
        l.append( cocos.menu.MenuItem('Quit', self.game.on_quit ) )

        self.create_menu( l )


if __name__ == "__main__":
    game = Game()
    if len(sys.argv) == 2:
        host, port = sys.argv[1].split(":")
        print host, port
        game.run(host, int(port))
    else:
        game.run()

