from panda3d.core import WindowProperties
from panda3d.core import CollisionTraverser, CollisionNode
from panda3d.core import CollisionHandlerQueue, CollisionRay
from panda3d.core import CollisionTube, CollisionSegment
from panda3d.core import Point3, Vec3, Vec4, BitMask32
from panda3d.core import LightRampAttrib
from code.enum import *
import sys

SPEED = 0.5


class Controls:

    def __init__(self, world):
        print "Controls init"
        self.world = world
        self.controlMap = {"left": 0, "right": 0, "forward": 0, "backward": 0,
                           "zoom-in": 0, "zoom-out": 0,
                           "wheel-in": 0, "wheel-out": 0}
        self.mousebtn = [0, 0, False]
        #self.world.win.setClearColor(Vec4(0, 0, 0, 1))

        # Accept the control keys for movement and rotation

        #self.world.taskMgr.add(self.update, "controlTask")
        self.player = self.world.player
        
        self.world.accept("escape", sys.exit)
        self.world.accept("w", self.player.setControl, [FORWARD, True])
        self.world.accept("a", self.player.setControl, [ROT_LEFT, True])
        self.world.accept("s", self.player.setControl, [BACK, True])
        self.world.accept("d", self.player.setControl, [ROT_RIGHT, True])
        self.world.accept("w-up", self.player.setControl, [FORWARD, False])
        self.world.accept("a-up", self.player.setControl, [ROT_LEFT, False])
        self.world.accept("s-up", self.player.setControl, [BACK, False])
        self.world.accept("d-up", self.player.setControl, [ROT_RIGHT, False])
#        self.accept("mouse1", self.setControl, ["zoom-in", True])
#        self.accept("mouse1-up", self.setControl, ["zoom-in", False])
#        self.accept("mouse3", self.setControl, ["zoom-out", True])
#        self.accept("mouse3-up", self.setControl, ["zoom-out", False])
        self.world.accept("wheel_up", self.player.setControl, ["wheel-in", True])
        self.world.accept("wheel_down", self.player.setControl, ["wheel-out", True])
        self.world.accept("page_up", self.player.setControl, ["zoom-in", True])
        self.world.accept("page_up-up", self.player.setControl, ["zoom-in", False])
        self.world.accept("page_down", self.player.setControl, ["zoom-out", True])
        self.world.accept("page_down-up", self.player.setControl, ["zoom-out", False])

        self.camera = self.world.camera
        self.camera.reparentTo(self.world.player.model)

        self.cameraTargetHeight = 6.0

        self.cameraDistance = 30

        self.cameraPitch = 10

        self.camera.setY(self.camera, -20)

        self.world.disableMouse()

        props = WindowProperties()
        props.setCursorHidden(True)
        self.world.win.requestProperties(props)
        print "Controls init success"

