#     Separate with Instances, Blender add-on that creates lights based on where the user paints.
#     Copyright (C) 2024 Spencer Magnusson
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <https://www.gnu.org/licenses/>.

if 'bpy' in locals():  # already reloaded
    import importlib
    importlib.reload(locals()['separate_operator'])

import bpy

from .separate_operator import MESH_OT_Separate_With_Instances

bl_info = {
    'name': 'Separate with Instances',
    'author': 'Spencer Magnusson',
    'version': (0, 0, 2),
    'blender': (3, 6, 0),
    'description': '',
    'location': '',
    'support': 'COMMUNITY',
    'category': 'Mesh',
    'doc_url': '',
    'tracker_url': '',
}

classes_to_register = (MESH_OT_Separate_With_Instances,)
addon_keymaps = []

def register():
    """Registers operators."""
    for cls in classes_to_register:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    if wm.keyconfigs.addon:
        km = wm.keyconfigs.addon.keymaps.new(name='Mesh', space_type='EMPTY')
        kmi = km.keymap_items.new('mesh.separate_with_instances', 'P', 'PRESS')
        addon_keymaps.append((km, kmi))


def unregister():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)

    for cls in classes_to_register:
        bpy.utils.unregister_class(cls)
