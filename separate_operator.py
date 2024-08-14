import bpy


class MESH_OT_Separate_With_Instances(bpy.types.Operator):
    bl_idname = 'mesh.separate_with_instances'
    bl_label = 'Separate with Instances'
    bl_description = 'Separates geometry and re-adding them to other instances'
    bl_options = {'REGISTER', 'UNDO'}

    type: bpy.props.EnumProperty(
        name='Type',
        items=(
            ('SELECTED', 'Selection', ''),
            ('MATERIAL', 'By Material', ''),
            ('LOOSE', 'By Loose Parts', ''),
        ),
        default='SELECTED',
    )

    @classmethod
    def poll(cls, context):
        return bpy.ops.mesh.separate.poll()

    def execute(self, context):
        bpy.ops.object.editmode_toggle()

        initial_obj = context.active_object
        bpy.ops.object.select_all(action='DESELECT')

        context.view_layer.objects.active = initial_obj
        initial_obj.select_set(True)

        bpy.ops.object.editmode_toggle()

        bpy.ops.mesh.separate(type=self.type)

        # active object is initial mesh,
        # other selected objects are new objects

        new_objs = context.selected_objects[1:]

        linked_objects = [
            scene_obj
            for scene_obj in context.scene.objects
            if scene_obj != initial_obj and scene_obj.data == initial_obj.data
        ]

        for new_obj in new_objs:
            for linked_scene_object in linked_objects:
                # get linked scene object matrix, and instance new_obj to its location
                new_parent = linked_scene_object.parent
                new_matrix = linked_scene_object.matrix_world.copy()

                bpy.ops.object.editmode_toggle()

                with context.temp_override(selected_objects=[new_obj]):
                    bpy.ops.object.duplicate(linked=True)

                bpy.ops.object.editmode_toggle()
                new_obj.parent = new_parent
                new_obj.matrix_world = new_matrix
                new_obj.select_set(True)

        return {'FINISHED'}
