from math import *
from direct.showbase.ShowBase import ShowBase

from twisted.internet.task import LoopingCall
from twisted.internet import reactor
from code.controls import Controls
from code.enum import *


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


class Player(Movable):
    """docstring for Player"""
    def __init__(self, model, world):
        super(Player, self).__init__(model, world)


class World(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        self.gc = globalClock
        self.loadInstance("content/entity/terr")
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

w = World()

#w.run()
LoopingCall(w.taskMgr.step).start(1 / 60)
reactor.run()
