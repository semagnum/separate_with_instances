import os
from pathlib import Path
import pytest

import bpy
import addon_utils


def get_zip_file_in_parent_dir():
    """Gets first zip file it can find.

    Since this will be in the tests/ folder,
    we need to go up a folder to find the zip file that compress.py builds.
    """
    parent_dir = Path(os.getcwd()).parent
    for root, dirs, files in os.walk(parent_dir):
        for file in files:
            if file.endswith(".zip"):
                return os.path.join(root, file)

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


def test_sanity():
    """If this fails, you are probably not setup, period ;P."""
    assert 1 + 1 == 2


def test_separate_instance_loose_parts(context, ops):
    # clear scene
    ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)

    ops.mesh.primitive_monkey_add()

    # instance Suzanne a couple of times
    bpy.ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
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
    bpy.ops.object.delete(use_global=False, confirm=False)

    ops.mesh.primitive_cube_add()


    # instance a couple of times
    bpy.ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
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
    # only select some of the faces
    bpy.ops.mesh.select_random(ratio=0.25, seed=1)
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
    bpy.ops.object.duplicate_move_linked(OBJECT_OT_duplicate={"linked": True, "mode": 'TRANSLATION'},
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
    ops.mesh.separate_with_instances(type='MATERIAL')

    # (two pieces) * 3 == 6 meshes
    assert len(context.scene.objects) == 6

    # only 2 datablocks used
    assert len({obj.data for obj in context.scene.objects}) == 2

    # only 3 matrices used
    assert len({str(obj.location) for obj in context.scene.objects}) == 3

