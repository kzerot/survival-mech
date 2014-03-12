from math import *
from direct.showbase.ShowBase import ShowBase
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, defer
from twisted.internet.threads import deferToThread
from twisted.internet.protocol import Protocol, Factory, ClientFactory
from code.controls import Controls
from code.enum import *
import json
import sys

isServer = "-s" in sys.argv

#test
#isServer = True

class Movable(object):
    def __init__(self, model, world):
        self.actions = []
        self.world = world
        self.id = -1
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


class Player(Movable):
    """docstring for Player"""
    def __init__(self, model, world):
        super(Player, self).__init__(model, world)

    def setControl(self, key, value):
        '''TODO '''
        changed = False
        if value and key not in self.actions:
            self.actions.append(key)
            changed = True
        elif not value and key in self.actions:
            self.actions.remove(key)
            changed = True
        print 'Controlling'
        if changed:
            print 'Send data to server'
            self.world.stateChange( json.dumps({"action": [key, value]}))


class World(ShowBase):
    def __init__(self, client=None):
        ShowBase.__init__(self)

        self.client = None
        self.players = {}

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

    def playerEnter(self, id=None):
        player = Player("content/entity/sphere", self)
        player.model.setPos(0, 0, 0)
        player.setMoveTask()
        self.playerAdd(player, id)

    def playerAdd(self, player, id):
        #self.players.append(player)
        self.players[id] = player

    def stateChange(self, data):
        '''data: players, mobs '''
        '''fires then state changed ))) '''
        print 'Clasic stateChange', data

class Server(Protocol):
    """docstring for Server"""
    def __init__(self, factory, world):
        self.factory = factory
        self.world = world
        self.id = -1

    def connectionMade(self):
        print 'New player'
        for p in self.factory.clients:
            p.transport.write(json.dumps({"add_player":self.factory.numProtocols}))
        self.factory.clients.append(self)
        self.world.playerEnter(self.factory.numProtocols)
        self.id = self.factory.numProtocols
        self.transport.write(json.dumps({"id":self.factory.numProtocols}))
        self.factory.numProtocols = self.factory.numProtocols+1 


    def connectionLost(self, reason):
        self.factory.numProtocols = self.factory.numProtocols-1

    def dataReceived(self, data):
        print 'Data received', data
        jdata = json.loads(data)
        jdata["player"] = self.id
        self.world.stateChange(jdata)
        for p in self.factory.clients:
            if p != self:
                p.transport.write(json.dumps(jdata))

class ServerFactory(Factory):
    def __init__(self, world):
        self.world = world # maps user names to Chat instances
        self.numProtocols = 0
        self.clients = []

    def buildProtocol(self, addr):
        return Server(self, self.world) 


class GameClient(Protocol):
    """docstring for Server"""
    def __init__(self, factory, world):
        self.factory = factory
        self.world = world
        self.world.stateChange = self.sendData

    def connectionMade(self):
        print 'Client connected OK'

    def connectionLost(self, reason):
        print 'Lost connect'

    def dataReceived(self, data):
        print "Data received", data
        jdata = json.loads(data)
        if "id" in jdata:
            self.world.player.id = jdata["id"]

    def sendData(self, data):
        '''data in json.dumps!'''
        print 'send', data
        if not isinstance(data, type("")):
            data = json.dumps(data)
        self.transport.write(data)


class GameClientFactory(ClientFactory):
    def __init__(self, world):
        self.world = world 

    def startedConnecting(self, connector):
        print 'Started to connect.'

    def buildProtocol(self, addr):
        print 'Connected.'
        return GameClient(self, self.world)

    def clientConnectionLost(self, connector, reason):
        print 'Lost connection.  Reason:', reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason

w = World()

#w.run()
if isServer:
    reactor.listenTCP(8123, ServerFactory(w))
else:
    reactor.connectTCP('localhost', 8123, GameClientFactory(w))

LoopingCall(w.taskMgr.step).start(1 / 60)
reactor.run()
