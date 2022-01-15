from uplogic.nodes import ULActionNode
from uplogic.nodes import ULOutSocket
from uplogic.utils import is_waiting
from uplogic.utils import is_invalid
from uplogic.utils import not_met


class ULSetCameraOrthoScale(ULActionNode):
    def __init__(self):
        ULActionNode.__init__(self)
        self.condition = None
        self.camera = None
        self.scale = None
        self.done = None
        self.OUT = ULOutSocket(self, self.get_done)

    def get_done(self):
        return self.done

    def evaluate(self):
        self.done = False
        condition = self.get_input(self.condition)
        if not_met(condition):
            return
        camera = self.get_input(self.camera)
        scale = self.get_input(self.scale)
        if is_waiting(camera, scale):
            return
        self._set_ready()
        if is_invalid(camera):
            return
        camera.ortho_scale = scale
        self.done = True
