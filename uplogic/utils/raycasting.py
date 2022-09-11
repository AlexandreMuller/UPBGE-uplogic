from bge import logic
from bge import render
from bge.types import KX_GameObject as GameObject
from bge.types import KX_PolyProxy
from mathutils import Vector


def ray_data(
    origin: Vector,
    dest: Vector,
    local: bool,
    dist: float
):
    """Get necessary data to calculate the ray.\n
    Not intended for manual use.
    """
    origin = getattr(origin, 'worldPosition', origin)
    dest = getattr(dest, 'worldPosition', dest)
    if local:
        dest = origin + dest
    d = dest - origin
    d.normalize()
    dist = dist if dist else (origin - dest).length
    dest = origin + d * dist
    return d, dist, dest



def raycast(
    caster: GameObject,
    origin: Vector,
    dest: Vector,
    distance: float = 0,
    prop: str = '',
    material: str = '',
    exclude: bool = False,
    xray: bool = False,
    local: bool = False,
    mask: int = 65535,
    visualize: bool = False
) -> tuple[GameObject, Vector, Vector, Vector]:
    """Raycast from any point to any target

    :param `caster`: casting object, this object will be ignored by the ray.
    :param `origin`: origin point; any vector or list.
    :param `dest`: target point; any vector or list.
    :param `distance`: distance the ray will be cast
    (0 means the ray will only be cast to target).
    :param `prop`: look only for objects with this property.
    :param `material`: look only for objects with this material applied.
    :param `exclude`: invert the selection for `prop` and `material`.
    :param `xray`: look for objects behind others.
    :param `local`: add the target vector to the origin.
    :param `mask`: Collision Mask for this ray.
    :param `visualize`: show the raycast.

    :returns: (`obj`, `point`, `normal`, `direction`)
    """
    if exclude:
        exclude_prop, prop = prop, ''
    origin = getattr(origin, 'worldPosition', Vector(origin)).copy()
    dest = getattr(dest, 'worldPosition', Vector(dest)).copy()
    direction, distance, dest = ray_data(origin, dest, local, distance)
    obj, point, normal = caster.rayCast(
        dest,
        origin,
        distance,
        prop,
        xray=xray,
        mask=mask
    )
    if (material and point) or (obj and exclude and exclude_prop in obj):
        bo = obj.blenderObject
        leftover_dist = distance - (origin - point).length
        while (
            material in [
                slot.material.name for
                slot in
                bo.material_slots
            ] or exclude_prop in obj.getPropertyNames() if exclude else
            material not in [
                slot.material.name for
                slot in
                bo.material_slots
            ]
        ) and leftover_dist > 0:
            if not xray:
                obj, point, normal = None, None, None
                break
            elif point:
                old_point = point
                obj, point, normal = obj.rayCast(
                    dest,
                    point,
                    leftover_dist,
                    prop,
                    xray=xray
                )
                if not obj:
                    break
                bo = obj.blenderObject
                leftover_dist -= (origin - old_point).length
            else:
                obj, point, normal = None, None, None
                break

    if visualize:
        line_dest: Vector = direction.copy()
        line_dest.x *= distance
        line_dest.y *= distance
        line_dest.z *= distance
        line_dest = line_dest + origin
        if not obj:
            render.drawLine(
                origin,
                line_dest,
                [1, 0, 0, 1]
            )
        else:
            render.drawLine(
                origin,
                point,
                [0, 1, 0, 1]
            )
    return (obj, point, normal, direction)


def raycast_face(
    caster: GameObject,
    origin: Vector,
    dest: Vector,
    distance: float = 0,
    prop: str = '',
    material: str = '',
    exclude: bool = False,
    xray: bool = False,
    local: bool = False,
    mask: int = 65535,
    visualize: bool = False
) -> tuple[GameObject, Vector, KX_PolyProxy, Vector]:
    """Raycast from any point to any target. Returns additional face data.

    :param `caster`: casting object, this object will be ignored by the ray.
    :param `origin`: origin point; any vector or list.
    :param `dest`: target point; any vector or list.
    :param `distance`: distance the ray will be cast
    (0 means the ray will only be cast to target).
    :param `prop`: look only for objects with this property.
    :param `material`: look only for objects with this material applied.
    :param `exclude`: invert the selection for `prop` and `material`.
    :param `xray`: look for objects behind others.
    :param `local`: add the target vector to the origin.
    :param `mask`: Collision Mask for this ray.
    :param `visualize`: show the raycast.

    :returns: (`obj`, `point`, `normal`, `direction`, `face`, `uv`)
    """
    if exclude:
        exclude_prop, prop = prop, ''
    direction, distance, dest = ray_data(origin, dest, local, distance)
    origin = getattr(origin, 'worldPosition', origin)
    obj, point, normal, face, uv = caster.rayCast(
        dest,
        origin,
        distance,
        prop,
        xray=xray,
        poly=2,
        mask=mask
    )
    if (material and point) or (obj and exclude):
        bo = obj.blenderObject
        leftover_dist = distance - (origin - point).length
        while (
            material in [
                slot.material.name for
                slot in
                bo.material_slots
            ] or exclude_prop in obj.getPropertyNames() if exclude else
            material not in [
                slot.material.name for
                slot in
                bo.material_slots
            ]
        ) and leftover_dist > 0:
            if not xray:
                obj, point, normal = None, None, None
                break
            elif point:
                old_point = point
                obj, point, normal, face, uv = obj.rayCast(
                    dest,
                    point,
                    leftover_dist,
                    prop,
                    xray=xray,
                    poly=2
                )
                if not obj:
                    break
                bo = obj.blenderObject
                leftover_dist -= (origin - old_point).length
            else:
                obj, point, normal = None, None, None
                break

    if visualize:
        line_dest: Vector = direction.copy()
        line_dest.x *= distance
        line_dest.y *= distance
        line_dest.z *= distance
        line_dest = line_dest + origin
        if not obj:
            render.drawLine(
                origin,
                line_dest,
                [1, 0, 0, 1]
            )
        else:
            render.drawLine(
                origin,
                point,
                [0, 1, 0, 1]
            )
    return (obj, point, normal, direction, face, uv)


def raycast_projectile(
    caster: GameObject,
    origin: Vector,
    aim: Vector,
    power: float,
    distance: float = 100,
    resolution: float = .05,
    prop: str = '',
    xray: bool = False,
    local: bool = False,
    mask: int = 65535,
    visualize: bool = False
) -> tuple[GameObject, Vector, Vector, list]:
    """Raycast along the predicted parabola of a projectile.

    :param `caster`: casting object, this object will be ignored by the ray.
    :param `origin`: origin point; any vector or list.
    :param `aim`: target point; the parabola will start towards this point.
    :param `power`: "speed" of the projectile; a higher values mean further throws
    :param `distance`: total distance the ray will be cast
    :param `resolution`: detail quality of the parabola; higher values mean less detail
    :param `prop`: look only for objects with this property.
    :param `xray`: look for objects behind others.
    :param `local`: add the target vector to the origin.
    :param `mask`: Collision Mask for this ray.
    :param `visualize`: show the raycast.

    :returns: (`obj`, `point`, `normal`, `points`)
    """
    def calc_projectile(t, vel, pos):
        half: float = logic.getCurrentScene().gravity.z * (.5 * t * t)
        vel = vel * t
        return Vector((0, 0, half)) + vel + pos

    aim.normalize()
    aim *= power
    origin = getattr(origin, 'worldPosition', origin)
    if local:
        origin = origin + caster.worldPosition

    points: list = []
    color: list = [1, 0, 0]
    idx = 0
    total_dist: float = 0

    while total_dist < distance:
        target = (calc_projectile(idx, aim, origin))
        start = origin if not points else points[-1]
        obj, point, normal = caster.rayCast(
            start,
            target,
            prop=prop,
            xray=xray,
            mask=mask
        )
        total_dist += (target-start).length
        if not obj:
            points.append(target)
        else:
            points.append(point)
            color = [0, 1, 0]
            break
        idx += resolution
    if visualize:
        for i, p in enumerate(points):
            if i < len(points) - 1:
                render.drawLine(p, points[i+1], color)
    return (obj, point, normal, points)


def raycast_camera(
    distance: float = 0,
    prop: str = '',
    xray: bool = False,
    aim: Vector = Vector((.5, .5)),
    mask: int = 65535
):
    """Raycast from any point to any target. Returns additional face data.

    :param `distance`: distance the ray will be cast
    :param `prop`: look only for objects with this property.
    :param `xray`: look for objects behind others.
    :param `aim`: X and Y coordinates of the screen from 0-1
    :param `mask`: Collision Mask for this ray.

    :returns: (`obj`, `point`, `normal`)
    """
    # assume screen coordinates
    camera = logic.getCurrentScene().active_camera
    if isinstance(aim, Vector) and len(aim) == 2:
        vec = 10 * camera.getScreenVect(aim[0], aim[1])
        ray_target = camera.worldPosition - vec
        aim = ray_target
    if prop:
        obj, point, normal = camera.rayCast(
            aim,
            None,
            distance,
            prop,
            xray=xray,
            mask=mask
        )
    else:
        obj, point, normal = camera.rayCast(aim, None, distance)
    return (obj, point, normal)


def raycast_mouse(
    distance: float = 100,
    prop: str = '',
    material: str = '',
    exclude: bool = False,
    xray: bool = False,
    mask: int = 65535
):
    """Raycast from the active camera to world cursor coordinates.

    :param `distance`: distance the ray will be cast
    :param `prop`: look only for objects with this property.
    :param `material`: look only for objects with this material applied.
    :param `exclude`: invert the selection for `prop` and `material`.
    :param `xray`: look for objects behind others.
    :param `mask`: Collision Mask for this ray.

    :returns: (`obj`, `point`, `normal`, `direction`)
    """
    camera = logic.getCurrentScene().active_camera
    mpos = logic.mouse.position
    vec = 10 * camera.getScreenVect(*mpos)
    ray_target = camera.worldPosition - vec
    return raycast(
        camera,
        camera.worldPosition,
        ray_target,
        distance,
        prop,
        material,
        exclude,
        xray,
        mask=mask
    )
