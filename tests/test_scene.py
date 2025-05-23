import ast
import math
import os
from pathlib import Path
import pytest

import bpy
import addon_utils


def test_math_isclose(a, b):
    return math.isclose(a, b, rel_tol=1e-4, abs_tol=1e-4)


def get_zip_file_in_parent_dir():
    """Gets first zip file it can find.

    Since this will be in the tests/ folder,
    we need to go up a folder to find the zip file that compress.py builds.
    """
    parent_dir = Path(__file__).parent.parent
    try:
        return next(
            os.path.join(parent_dir, f)
            for f in os.listdir(parent_dir)
            if f.endswith('.zip')
        )
    except StopIteration:
        raise FileNotFoundError('No zip file to install into Blender!')


@pytest.fixture(scope="session", autouse=True)
def install_addon(request):
    """Installs the addon for testing. After the session is finished, it optionally uninstalls the add-on."""
    bpy.ops.preferences.addon_install(filepath=get_zip_file_in_parent_dir())

    addon_utils.modules_refresh()
    bpy.ops.script.reload()

    bpy.ops.preferences.addon_enable(module='separate_with_instances')

    yield

    # In my case (using symlinks), since this add-on is already enabled,
    # this installs the add-on twice.
    # So I need to delete the newly installed add-on folder afterward.

    import os
    import shutil
    if os.getenv('ADDON_INSTALL_PATH_TO_REMOVE') is not None:
        shutil.rmtree(os.getenv('ADDON_INSTALL_PATH_TO_REMOVE'))


@pytest.fixture
def context():
    import bpy
    return bpy.context


@pytest.fixture
def ops():
    import bpy
    # bpy module doesn't refresh the scene per test,
    # so I need to reload the file each time
    bpy.ops.wm.read_homefile()
    return bpy.ops


@pytest.fixture(params=['GEOMETRY_ORIGIN', 'ORIGIN_GEOMETRY', 'ORIGIN_CURSOR', 'ORIGIN_CENTER_OF_MASS', 'ORIGIN_CENTER_OF_VOLUME'])
def origin_type(request):
    return request.param


@pytest.fixture(params=['MEDIAN', 'BOUNDS'])
def center(request):
    return request.param


def test_sanity():
    """If this fails, you are probably not setup, period ;P."""
    assert 1 + 1 == 2


def test_separate_parents(context, ops):
    # clear scene
    ops.object.select_all(action='SELECT')
    ops.object.delete(use_global=False, confirm=False)

    ops.mesh.primitive_cube_add()
    ops.mesh.primitive_monkey_add()
    ops.transform.translate(value=(0, 0, -5))

    # set parent
    context.scene.objects['Cube'].select_set(True)
    context.scene.objects['Suzanne'].select_set(True)
    context.view_layer.objects.active = context.scene.objects['Cube']
    ops.object.parent_set(type='OBJECT', keep_transform=False)
    ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
                                     TRANSFORM_OT_translate={"value": (-4.3952, -5.05493, 0)})

    ops.object.select_all(action='DESELECT')
    context.scene.objects['Cube'].select_set(False)
    context.scene.objects['Suzanne'].select_set(True)
    context.view_layer.objects.active = context.scene.objects['Suzanne']
    ops.object.editmode_toggle()
    ops.mesh.select_all(action='SELECT')
    ops.mesh.separate_with_instances(type='LOOSE')

    # (3 pieces) * 2 + 2 cubes == 8 meshes
    assert len(context.scene.objects) == 8

    # 4 (3 pieces + 1 cube) datablocks used
    assert len({obj.data for obj in context.scene.objects}) == 4

    # 4 matrices used (2 parents, 3 children per parent that share same location)
    assert len({str(obj.matrix_world.to_translation()) for obj in context.scene.objects}) == 4


def test_separate_instance_loose_parts(context, ops):
    # clear scene
    ops.object.select_all(action='SELECT')
    ops.object.delete(use_global=False, confirm=False)

    ops.mesh.primitive_monkey_add()

    # instance Suzanne a couple of times
    ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
                                     TRANSFORM_OT_translate={"value": (-2.97763, -5.86426, 0),
                                                             "orient_type": 'GLOBAL',
                                                             "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                                             "orient_matrix_type": 'GLOBAL'})
    bpy.ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
                                         TRANSFORM_OT_translate={"value": (5.13482, 12.2365, 0),
                                                                 "orient_type": 'GLOBAL',
                                                                 "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                                                 "orient_matrix_type": 'GLOBAL'})

    ops.object.editmode_toggle()
    ops.mesh.select_all(action='SELECT')

    ops.mesh.separate_with_instances(type='LOOSE')

    # (two eyes + head) * 3 == 9 meshes
    assert len(context.scene.objects) == 9

    # only 3 datablocks used
    assert len({obj.data for obj in context.scene.objects}) == 3

    # only 3 matrices used
    assert len({str(obj.location) for obj in context.scene.objects}) == 3


def test_separate_instance_selected(context, ops):
    # clear scene
    ops.object.select_all(action='SELECT')
    ops.object.delete(use_global=False, confirm=False)

    ops.mesh.primitive_cube_add()

    # instance a couple of times
    ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
                                     TRANSFORM_OT_translate={"value": (-2.97763, -5.86426, 0),
                                                             "orient_type": 'GLOBAL',
                                                             "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                                             "orient_matrix_type": 'GLOBAL'})
    ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
                                     TRANSFORM_OT_translate={"value": (5.13482, 12.2365, 0),
                                                             "orient_type": 'GLOBAL',
                                                             "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                                             "orient_matrix_type": 'GLOBAL'})

    ops.object.editmode_toggle()
    # only select some of the faces
    ops.mesh.select_random(ratio=0.25, seed=1)
    ops.mesh.separate_with_instances(type='SELECTED')

    # (two pieces) * 3 == 6 meshes
    assert len(context.scene.objects) == 6

    # only 2 datablocks used
    assert len({obj.data for obj in context.scene.objects}) == 2

    # only 3 matrices used
    assert len({str(obj.location) for obj in context.scene.objects}) == 3


def test_separate_instance_material(context, ops):
    # clear scene
    ops.object.select_all(action='SELECT')
    ops.object.delete(use_global=False, confirm=False)

    ops.mesh.primitive_cube_add()

    # add extra material slot and new material
    ops.object.material_slot_add()
    new_material = bpy.data.materials.new(name='test_material')
    context.object.data.materials.append(new_material)
    assert len(context.object.material_slots) == 2 and all(slot is not None for slot in context.object.material_slots)

    # assign random geometry to new material
    context.object.data.polygons[1].material_index = 1
    context.object.data.polygons[3].material_index = 1

    # instance a couple of times
    ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
                                     TRANSFORM_OT_translate={"value": (-2.97763, -5.86426, 0),
                                                             "orient_type": 'GLOBAL',
                                                             "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                                             "orient_matrix_type": 'GLOBAL'})
    ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
                                     TRANSFORM_OT_translate={"value": (5.13482, 12.2365, 0),
                                                             "orient_type": 'GLOBAL',
                                                             "orient_matrix": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
                                                             "orient_matrix_type": 'GLOBAL'})

    ops.object.editmode_toggle()
    ops.mesh.select_all(action='SELECT')
    ops.mesh.separate_with_instances(type='MATERIAL')

    # (two pieces) * 3 == 6 meshes
    assert len(context.scene.objects) == 6

    # only 2 datablocks used
    assert len({obj.data for obj in context.scene.objects}) == 2

    # only 3 matrices used
    assert len({str(obj.location) for obj in context.scene.objects}) == 3


def test_set_origin_shifted(context, ops, origin_type, center):
    # clear scene
    ops.object.select_all(action='SELECT')
    ops.object.delete(use_global=False, confirm=False)

    ops.mesh.primitive_monkey_add()

    # instance Suzanne a couple of times
    DISTANCE = 5.0
    ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
                                     TRANSFORM_OT_translate={"value": (-DISTANCE, 0, 0)})
    bpy.ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
                                         TRANSFORM_OT_translate={"value": (DISTANCE * 2, 0, 0)})

    ops.object.origin_set_with_instances(type=origin_type, center=center)

    objects = context.scene.objects
    # only 3 datablocks used
    assert len({obj.data for obj in objects}) == 1
    # 3 distinct matrices
    assert len({str(obj.location) for obj in objects}) == 3
    # origins align
    loc0, loc1, loc2 = objects['Suzanne'].location, objects['Suzanne.001'].location, objects['Suzanne.002'].location
    assert test_math_isclose(loc0[0], loc1[0] + DISTANCE) and test_math_isclose(loc0[0], loc2[0] - DISTANCE)
    assert test_math_isclose(loc0[1], loc1[1]) and test_math_isclose(loc1[1], loc2[1])
    assert test_math_isclose(loc0[2], loc1[2]) and test_math_isclose(loc1[2], loc2[2])


# UTILITY TESTS/FUNCTIONS


def get_init_version(filepath):
    with open(filepath, 'r') as f:
        node = ast.parse(f.read())

    n: ast.Module
    for n in ast.walk(node):
        for b in n.body:
            if isinstance(b, ast.Assign) and isinstance(b.value, ast.Dict) and (
                    any(t.id == 'bl_info' for t in b.targets)):
                bl_info_dict = ast.literal_eval(b.value)
                return bl_info_dict['version']

    raise AssertionError(filepath + ' has no version')


def get_extension_version(filepath):
    with open(filepath, 'r') as f:
        node = ast.parse(f.read())

    n: ast.Module
    for n in ast.walk(node):
        for b in n.body:
            if (isinstance(b, ast.Assign) and
                    isinstance(b.value, ast.Str) and
                    any(t.id == 'version' for t in b.targets)
            ):
                return tuple(map(int, str(ast.literal_eval(b.value)).split('.')))

    raise AssertionError(filepath + ' has no version')


def test_assert_version_parity_manifest():
    import ast

    root_folder = Path(__file__).parent.parent
    init = root_folder / '__init__.py'
    extension_manifest = root_folder / 'blender_manifest.toml'

    init_version, extension_version = get_init_version(init), get_extension_version(extension_manifest)
    assert init_version == extension_version
