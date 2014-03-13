from math import *
from direct.showbase.ShowBase import ShowBase
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, defer
from twisted.internet.threads import deferToThread
from twisted.internet.protocol import Protocol, Factory, ClientFactory
from direct.actor.Actor import Actor
from code.controls import Controls
from code.enum import *
import json
import sys

isServer = "-s" in sys.argv
print sys.argv
if isServer:
    print 'Mode: server'
else:
    print 'Mode: client'

def safeLoads(raw):
    if '}{' in raw:
        try:
            return [json.loads(t)
                    for t in raw.replace('}{', '}||{').split('||')]
        except:
            print 'failed to parse ', raw
            return []
    else:
        return [json.loads(raw)]


class Movable(object):

    def __init__(self, model, world):
        self.actions = []
        self.world = world
        self.id = -1
        # simplify
        self.gc = self.world.gc
        self.model = model

        self.speedForward = 20
        self.speedBack = -10
        self.speedRotate = 20

        self.loocVec = (0, 0)
        # only H rotate
        self.rotate = 0

    def setMoveTask(self):
        taskMgr.add(self.move, "playerTask")

    def isKey(self, key):
        return key in self.actions

    def move(self, task):
        if self.isKey(FORWARD):
            self.model.setY(self.model, self.gc.getDt() * self.speedForward)
        elif self.isKey(BACK):
            self.model.setY(self.model, self.gc.getDt() * self.speedBack)

        if self.isKey(ROT_LEFT):
            self.model.setH(self.model, self.gc.getDt() * self.speedRotate)
        elif self.isKey(ROT_RIGHT):
            self.model.setH(self.model, -self.gc.getDt() * self.speedRotate)

        return task.cont

    def json(self):
        return json.dumps(self.actions)

    def getPos(self):
        return [self.model.getX(), self.model.getY(), self.model.getZ()]

    def setPos(self, loc):
        x, y, z = loc
        self.model.setPos(render, x, y, z)

    def setRot(self, rot):
        self.model.setH(rot)


class Player(Movable):

    """Player has many parts, and all of them we must sync"""

    def __init__(self, model, world):
        model = render.attachNewNode("player")
        super(Player, self).__init__(model, world)

        # Player has some parts
        #Legs, body, weapons
        self.legs = Actor('content/entity/mech', {
                          'stay': 'content/entity/mech-Anim1',
                          'start': 'content/entity/ech-Anim1',
                          'walk': 'content/entity/mech-walk',
                          })
        self.legs.reparentTo(model)
        self.legs.loop('walk')
        point = self.legs.exposeJoint(None, "modelRoot", "pelvis")
        self.body = loader.loadModel('content/entity/torso')
        self.body.reparentTo(point)
        self.body.setHpr(render, 0, 0, 0)
        # weapons has limited points
        # 1
        self.tower = None
        # 2
        self.right = None
        # 3
        self.left = None
        # 4
        self.right2 = None
        # 5
        self.left2 = None

        # For firing using dict, witch weapon is on
        self.firing = [1, ]

        # variables hardcoded
        self.bodyRotate = 50
        self.speedRotate = 50
        self.isPlayer = False
        self.targetRotation = (0, 0)
        self.target = None

    def setControl(self, key, value):
        '''TODO '''
        changed = False
        if value and key not in self.actions:
            self.actions.append(key)
            changed = True
        elif not value and key in self.actions:
            self.actions.remove(key)
            changed = True

        if changed and self.isPlayer:
            self.world.stateChange(json.dumps({"action": [key, value]}))

    def updateTarget(self):
        # send P and H
        self.world.stateChange(json.dumps({"targetRot": self.targetRotation}))

    def targeting(self, task):
        pass

    def move(self, task):
        if self.body:
            needH = self.targetRotation[1]
            h = self.body.getH(render)
            if abs(needH - h) < 1:
                self.body.setH(render, needH)
            else:
                rot = (needH - h) / abs(needH - h)
                self.body.setH(
                    self.body, rot * self.gc.getDt() * self.bodyRotate)
        return super(Player, self).move(task)


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
        self.instance.setScale(5, 5, 5)

    def setPlayer(self):
        self.player = Player("content/entity/sphere", self)
        self.player.model.setPos(0, 0, 0)
        self.player.setMoveTask()
        self.player.isPlayer = True

    def playerEnter(self, id=None):
        player = Player("content/entity/sphere", self)
        player.model.setPos(0, 0, 0)
        player.setMoveTask()
        player.id = id
        self.playerAdd(player, id)
        return player

    def playerAdd(self, player, id):
        # self.players.append(player)
        self.players[id] = player

    def stateChange(self, data):
        '''data: players, mobs '''
        '''fires then state changed'''
        '''Default - server version'''
        print 'Server stateChange', data

    def updateData(self, data):
        print "updateData", data
        if "add_player" in data:
            self.playerEnter(data["add_player"])
        if "player" in data:
            self.updatePlayer(data["player"])
        if "players" in data:
            for p in data["players"]:
                self.updatePlayer(p)

    def updatePlayer(self, data):
        player = None
        if "id" not in data or (not isServer and data["id"] == self.player.id):
            # Without ID it's client's player
            player = self.player
        elif "id" in data:
            if data["id"] in self.players:
                player = self.players[data["id"]]
            else:
                # Add player!
                player = self.playerEnter(data["id"])
        else:
            print "Incorrect data", data
            return
        if "action" in data:
            player.setControl(data["action"][0], data["action"][1])
        if "actions" in data:
            player.actions = data["actions"]
        if "loc" in data:
            player.setPos(data["loc"])

    def getPlayers(self):
        return self.players

    def stop(self):
        print 'going to bed...'
        self.taskMgr.stop()
        print 'stop reactor'
        reactor.stop()
        print 'close window'
        self.closeWindow(self.win)
        print 'sys.exit'
        sys.exit()
        print 'user exit'
        base.userExit()


class Server(Protocol):

    """docstring for Server"""

    def __init__(self, factory, world):
        self.factory = factory
        self.world = world
        # self.id is connection and player id
        self.id = -1

    def connectionMade(self):
        print 'New player'
        dataToSend = {"add_player": self.factory.numProtocols}
        for p in self.factory.clients:
            p.transport.write(json.dumps(dataToSend))

        players = []
        for pl in self.world.players:
            client_player = self.world.players[pl]
            players.append({
                "id": client_player.id,
                "loc": client_player.getPos(),
                "actions": client_player.actions
            })
        dataToSend = {"id": self.factory.numProtocols,
                      "players": players}
        self.factory.clients.append(self)
        self.world.playerEnter(self.factory.numProtocols)
        self.id = self.factory.numProtocols
        self.transport.write(json.dumps(dataToSend))
        self.factory.numProtocols = self.factory.numProtocols + 1

    def connectionLost(self, reason):
        #self.factory.numProtocols = self.factory.numProtocols - 1
        pass

    def dataReceived(self, data):
        print 'Data received', data
        bigdata = safeLoads(data)
        for jdata in bigdata:
            dataToSend = {}
            dataToSend = jdata
            # dataToSend.update(jdata)
            if "id" not in dataToSend:
                dataToSend["id"] = self.id
            self.world.updatePlayer(dataToSend)
            for p in self.factory.clients:
                if p != self:
                    p.transport.write(json.dumps({"player": dataToSend}))


class ServerFactory(Factory):

    def __init__(self, world):
        self.world = world
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
        bigdata = safeLoads(data)
        for jdata in bigdata:
            if "id" in jdata:
                self.world.player.id = jdata["id"]
            self.world.updateData(jdata)

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
        # connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print 'Connection failed. Reason:', reason

w = World()

# w.run()
if isServer:
    reactor.listenTCP(8123, ServerFactory(w))
else:
    reactor.connectTCP('localhost', 8123, GameClientFactory(w))

LoopingCall(w.taskMgr.step).start(1 / 60)
reactor.run()
