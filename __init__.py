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

from .separate_operator import SeparateOperator, SetOriginOperator

bl_info = {
    'name': 'Separate with Instances',
    'author': 'Spencer Magnusson',
    'version': (0, 0, 3),
    'blender': (3, 6, 0),
    'description': '',
    'location': '',
    'support': 'COMMUNITY',
    'category': 'Mesh',
    'doc_url': 'https://github.com/semagnum/separate_with_instances',
    'tracker_url': 'https://github.com/semagnum/separate_with_instances/issues',
}

classes_to_register = (SeparateOperator, SetOriginOperator,)
addon_keymaps = []


def draw_menu(self, context):
    layout = self.layout
    layout.operator_menu_enum('object.origin_set_with_instances', text='Set Origin + Instances', property='type')


def register():
    """Registers operators."""
    for cls in classes_to_register:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_object.append(draw_menu)

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

    bpy.types.VIEW3D_MT_object.remove(draw_menu)

    for cls in classes_to_register:
        bpy.utils.unregister_class(cls)
