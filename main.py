from math import *
from direct.showbase.ShowBase import ShowBase
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, defer
from twisted.internet.threads import deferToThread
from twisted.internet.protocol import Protocol
from code.controls import Controls
from code.enum import *
import json
import sys

isServer = "-s" in sys.argv

class Movable(object):
    def __init__(self, model, world):
        self.actions = []
        self.world = world

        #simplify
        self.gc = self.world.gc
        self.model = world.loader.loadModel(model)
        self.model.reparentTo(render)

        self.speedForward = 20
        self.speedBack = -10
        self.speedRotate = 10

        self.loocVec = (0, 0)

    def setMoveTask(self):
        taskMgr.add(self.move, "playerTask")

    def isKey(self, key):
        return key in self.actions

    def move(self, task):
        if self.isKey(FORWARD):
            self.model.setY(self.model, self.gc.getDt() * self.speedForward)
        elif self.isKey(BACK):
            self.model.setY(self.model, self.gc.getDt() * self.speedBack)
        return task.cont

    def json(self):
        return json.dumps(self.actions)


    def setControl(self, key, value):
        '''TODO '''
        if value and key not in self.world.player.actions:
            self.world.player.actions.append(key)
        elif not value and key in self.world.player.actions:
            self.world.player.actions.remove(key)        

class Player(Movable):
    """docstring for Player"""
    def __init__(self, model, world):
        super(Player, self).__init__(model, world)
        world.cameras


class World(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.players = []

        self.gc = globalClock
        self.loadInstance("content/entity/terr")
        if not isServer:
            self.setPlayer()
            Controls(self)

    def loadInstance(self, instanceModel):
        self.instance = self.loader.loadModel(instanceModel)
        self.instance.reparentTo(render)
        #self.instance.setScale(0.25, 0.25, 0.25)
        self.instance.setPos(0, 0, 0)

    def setPlayer(self):
        self.player = Player("content/entity/sphere", self)
        self.player.model.setPos(0, 0, 0)
        self.player.setMoveTask()

    def playerLog(self, player):
        self.players.append(player)

    def stateChange(self, data):
        '''data: players, mobs '''
        print data

class Server(Protocol):
    """docstring for Server"""
    def __init__(self, factory, world):
        self.factory = factory
        self.world = world

    def connectionMade(self):
        self.factory.numProtocols = self.factory.numProtocols+1 
        

    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols-1

    def dataReceived(self, data):
        d = defer.Deferred()
        d.addCallback(self.world.stateChange(json.loads(data)))
        self.world.stateChange(data)
        self.transport.write(data)

class ServerFactory(Factory):

    def __init__(self, world):
        self.world = world # maps user names to Chat instances

    def buildProtocol(self, addr):
        return Chat(self.world) 

class Client(Protocol):
    def sendData(self, data):
        '''data in json.dumps!'''
        self.transport.write(data)


w = World()

#w.run()
if isServer:
    reactor.listenTCP(8123, ServerFactory())

LoopingCall(w.taskMgr.step).start(1 / 60)
reactor.run()
