from bge import logic
from bge.types import KX_GameObject as GameObject
import bpy
from bpy.types import Material
from .errors import LogicControllerNotSupportedError
from .constants import LO_AXIS_TO_VECTOR
from .math import project_vector3
from .math import clamp


def xrot_to(
    rotating_object,
    target_pos,
    front_axis_code=1,
    factor=1
):
    front_vector = LO_AXIS_TO_VECTOR[front_axis_code]
    vec = rotating_object.getVectTo(target_pos)[1]
    vec = project_vector3(vec, 1, 2)
    vec.normalize()
    front_vector = rotating_object.getAxisVect(front_vector)
    front_vector = project_vector3(front_vector, 1, 2)
    signed_angle = vec.angle_signed(front_vector, None)
    if signed_angle is None:
        return
    abs_angle = abs(signed_angle)
    if abs_angle < 0.01:
        return True
    angle_sign = (signed_angle > 0) - (signed_angle < 0)
    drot = angle_sign * abs_angle * clamp(factor)
    eulers = rotating_object.localOrientation.to_euler()
    eulers[0] += drot
    rotating_object.localOrientation = eulers
    return False


def yrot_to(
    rotating_object,
    target_pos,
    front_axis_code=1,
    factor=1
):
    front_vector = LO_AXIS_TO_VECTOR[front_axis_code]
    vec = rotating_object.getVectTo(target_pos)[1]
    vec = project_vector3(vec, 2, 0)
    vec.normalize()
    front_vector = rotating_object.getAxisVect(front_vector)
    front_vector = project_vector3(front_vector, 2, 0)
    signed_angle = vec.angle_signed(front_vector, None)
    if signed_angle is None:
        return
    abs_angle = abs(signed_angle)
    if abs_angle < 0.01:
        return True
    angle_sign = (signed_angle > 0) - (signed_angle < 0)
    drot = angle_sign * abs_angle * clamp(factor)
    eulers = rotating_object.localOrientation.to_euler()
    eulers[1] += drot
    rotating_object.localOrientation = eulers
    return False


def zrot_to(
    rotating_object,
    target_pos,
    front_axis_code=1,
    factor=1
):
    front_vector = LO_AXIS_TO_VECTOR[front_axis_code]
    vec = rotating_object.getVectTo(target_pos)[1]
    vec = project_vector3(vec, 0, 1)
    vec.normalize()
    front_vector = rotating_object.getAxisVect(front_vector)
    front_vector = project_vector3(front_vector, 0, 1)
    signed_angle = vec.angle_signed(front_vector, None)
    if signed_angle is None:
        return True
    abs_angle = abs(signed_angle)
    if abs_angle < 0.01:
        return True
    angle_sign = (signed_angle > 0) - (signed_angle < 0)
    drot = angle_sign * abs_angle * clamp(factor)
    eulers = rotating_object.localOrientation.to_euler()
    eulers[2] += drot
    rotating_object.localOrientation = eulers
    return False


def rot_to(
    rot_axis_index,
    rotating_object,
    target_pos,
    front_axis_code,
    factor=1
):
    if rot_axis_index == 0:
        return xrot_to(
            rotating_object,
            target_pos,
            front_axis_code,
            factor
        )
    elif rot_axis_index == 1:
        return yrot_to(
            rotating_object,
            target_pos,
            front_axis_code,
            factor
        )
    elif rot_axis_index == 2:
        return zrot_to(
            rotating_object,
            target_pos,
            front_axis_code,
            factor
        )


def move_to(
    moving_object,
    destination_point,
    speed,
    time_per_frame,
    dynamic,
    distance
):
    if dynamic:
        direction = (
            destination_point -
            moving_object.worldPosition)
        dst = direction.length
        if(dst <= distance):
            return True
        direction.z = 0
        direction.normalize()
        velocity = direction * speed
        velocity.z = moving_object.worldLinearVelocity.z
        moving_object.worldLinearVelocity = velocity
        return False
    else:
        direction = (
            destination_point -
            moving_object.worldPosition
            )
        dst = direction.length
        if(dst <= distance):
            return True
        direction.normalize()
        displacement = speed * time_per_frame
        motion = direction * displacement
        moving_object.worldPosition += motion
        return False


def controller_brick_status(owner, controller_name):
    cont = owner.controllers[controller_name]
    state = (
        owner
        .blenderObject
        .game
        .controllers[controller_name]
        .type
    )
    if not cont.sensors:
        return False
    elif state == 'LOGIC_AND':
        return False not in [sens.positive for sens in cont.sensors]
    elif state == 'LOGIC_OR':
        return True in [sens.positive for sens in cont.sensors]
    elif state == 'LOGIC_NAND':
        return False in [sens.positive for sens in cont.sensors]
    elif state == 'LOGIC_NOR':
        return True not in [sens.positive for sens in cont.sensors]
    elif state == 'LOGIC_XOR':
        return [
            sens.positive
            for sens in
            cont.sensors
        ].count(True) % 2 != 0
    elif state == 'LOGIC_XNOR':
        check = cont.sensors[0].positive
        return False not in [
            sens.positive == check
            for sens in
            cont.sensors
        ]
    else:
        raise LogicControllerNotSupportedError


class ControllerBrick(tuple):

    @property
    def brick(self):
        return self[0]

    @property
    def name(self):
        return self[0].name

    @property
    def positive(self):
        return self[1]

    @property
    def sensors(self):
        return self[2]

    @property
    def actuators(self):
        return self[3]


def controller_brick(owner, controller_name):
    cont = owner.controllers[controller_name]
    state = (
        owner
        .blenderObject
        .game
        .controllers[controller_name]
        .type
    )
    if not cont.sensors:
        return ControllerBrick([cont, False, cont.sensors, cont.actuators])
    elif state == 'LOGIC_AND':
        return ControllerBrick([cont, False not in [sens.positive for sens in cont.sensors], cont.sensors, cont.actuators])
    elif state == 'LOGIC_OR':
        return ControllerBrick([cont, True in [sens.positive for sens in cont.sensors], cont.sensors, cont.actuators])
    elif state == 'LOGIC_NAND':
        return ControllerBrick([cont, False in [sens.positive for sens in cont.sensors], cont.sensors, cont.actuators])
    elif state == 'LOGIC_NOR':
        return ControllerBrick([cont, True not in [sens.positive for sens in cont.sensors], cont.sensors, cont.actuators])
    elif state == 'LOGIC_XOR':
        return ControllerBrick([cont, [
            sens.positive
            for sens in
            cont.sensors
        ].count(True) % 2 != 0, cont.sensors, cont.actuators])
    elif state == 'LOGIC_XNOR':
        check = cont.sensors[0].positive
        return ControllerBrick([cont, False not in [
            sens.positive == check
            for sens in
            cont.sensors
        ], cont.sensors, cont.actuators])
    else:
        raise LogicControllerNotSupportedError


def create_curve(
    name: str,
    bevel_depth: float = 0.0,
    dimensions: int = 3,
    material: str or Material = None,
    collection: str = None
) -> GameObject:
    """Create a `KX_GameObject` containing a `bpy.types.Curve` object.

    :param `name`: Name of the new `KX_GameObject`.
    :param `bevel_depth`: Define the "thickness" of the curve. This will add
    geometry along the spline.
    :param `dimensions`: Set the coordinate space in which to calculate the
    curve.
    :param `material`: The material to use for bevel geometry.
    :param `collection`: The collection to which to add the curve. Leave at
    `None` to use scene collection.
    """
    bcurve = bpy.data.curves.new(name, 'CURVE')
    bcurve.bevel_depth = bevel_depth
    bcurve.dimensions = f'{dimensions}D'
    bobj = bpy.data.objects.new(name, bcurve)
    if material:
        if isinstance(material, str):
            bobj.data.materials.append(bpy.data.materials[material])
        elif isinstance(material, Material):
            bobj.data.materials.append(material)
    if collection:
        if isinstance(collection, str):
            collection = bpy.data.collections.get(collection, bpy.context.scene.collection)
    elif collection is None:
        collection = bpy.context.scene.collection
    collection.objects.link(bobj)
    game_obj = logic.getCurrentScene().convertBlenderObject(bobj)
    return game_obj


def set_curve_points(
    curve: GameObject,
    points: list
) -> None:
    """Set the curve points of a `KX_GameObject` containing a `bpy.types.Curve` object.

    :param `curve`: `KX_GameObject`
    :param `points`: A list of points to use for the curve.
    """
    bcurve = curve.blenderObject.data
    for spline in bcurve.splines:
        bcurve.splines.remove(spline)
    spline = bcurve.splines.new('POLY')
    pos = curve.worldPosition

    spline.points.add(len(points)-1)
    for p, new_co in zip(spline.points, points):
        p.co = ([
            new_co[0] - pos.x,
            new_co[1] - pos.y,
            new_co[2] - pos.z
        ] + [1.0])


class ULCurve():
    """Wrapper class for creating and handling curves more easily.

    :param `name`: Name of this curve object.
    :param `bevel_depth`: Define the "thickness" of the curve. This will add
    geometry along the spline.
    :param `dimensions`: Set the coordinate space in which to calculate the
    curve.
    :param `material`: The material to use for bevel geometry.
    :param `collection`: The collection to which to add the curve. Leave at
    `None` to use scene collection.
    """

    _deprecated = True

    def __init__(
        self,
        name: str,
        bevel_depth: float = 0.0,
        dimensions: int = 3,
        material: str or Material =None,
        collection: str = None
    ) -> None:
        if self._deprecated:
            print('[UPLOGIC] ULCurve class will be renamed to "Curve" in future releases!')
        self.object = create_curve(
            name,
            bevel_depth,
            dimensions,
            material,
            collection
        )

    @property
    def name(self):
        """Name of the game object (Read-Only)."""
        return self.object.name

    @name.setter
    def name(self, val):
        print('ULCurve.name is read-only!')

    @property
    def points(self):
        """Points of the curve. These points use global coordinates."""
        splines = self.object.blenderObject.data.splines
        return splines[0].points if len(splines) > 0 else []

    @points.setter
    def points(self, val):
        if val != self.points:
            set_curve_points(self.object, val)

    @property
    def bevel_depth(self):
        """Thickness of the curve geometry."""
        return self.object.blenderObject.data.bevel_depth

    @bevel_depth.setter
    def bevel_depth(self, val):
        self.object.blenderObject.data.bevel_depth = val


class Curve(ULCurve):
    _deprecated = False