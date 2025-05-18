import bpy


class SeparateOperator(bpy.types.Operator):
    bl_idname = 'mesh.separate_with_instances'
    bl_label = 'Separate + Instances'
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


class SetOriginOperator(bpy.types.Operator):
    bl_idname = 'object.origin_set_with_instances'
    bl_label = 'Set Origin + Instances'
    bl_options = {'REGISTER', 'UNDO'}

    type: bpy.props.EnumProperty(
        name='Type',
        items=(
            ('GEOMETRY_ORIGIN', 'Geometry to Origin', ''),
            ('ORIGIN_GEOMETRY', 'Origin to Geometry', ''),
            ('ORIGIN_CURSOR', 'Origin to 3D Cursor', ''),
            ('ORIGIN_CENTER_OF_MASS', 'Origin to Center of Mass (Surface)', ''),
            ('ORIGIN_CENTER_OF_VOLUME', 'Origin to Center of Mass (Volume)', ''),
        ),
        default='ORIGIN_GEOMETRY',
    )

    center: bpy.props.EnumProperty(
        name='Center',
        items=(
            ('MEDIAN', 'Median', ''),
            ('BOUNDS', 'Bounds', ''),
        ),
        default='MEDIAN',
    )

    @classmethod
    def poll(cls, context):
        return bpy.ops.object.origin_set.poll()

    def execute(self, context):
        prev_cursor_location = context.scene.cursor.location.copy()
        prev_active_object = context.view_layer.objects.active
        selection = context.selected_objects[:]
        selection_to_other_instances = {
            obj: [
                scene_obj
                for scene_obj in context.scene.objects
                if scene_obj != obj and scene_obj.data == obj.data
            ]
            for obj in selection
        }

        def force_selection(selected_objects):
            bpy.ops.object.select_all(action='DESELECT')
            for obj in selected_objects:
                obj.select_set(True)
            context.view_layer.objects.active = selected_objects[0]

        for initial_obj in selection:
            linked_objects = selection_to_other_instances[initial_obj]

            prev_location = initial_obj.location.copy()
            obj_data_name = initial_obj.data.name
            force_selection([initial_obj])
            bpy.ops.object.make_single_user(object=False, obdata=True, material=False, animation=False)
            bpy.ops.object.origin_set(type=self.type, center=self.center)
            initial_obj.data.name = obj_data_name

            location_diff = initial_obj.location - prev_location

            for obj in linked_objects:
                force_selection([obj])
                bpy.ops.object.make_single_user(object=False, obdata=True, material=False, animation=False)
                context.scene.cursor.location = obj.location + location_diff
                bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
                obj.data = initial_obj.data

        bpy.ops.object.select_all(action='DESELECT')
        for obj in selection:
            obj.select_set(True)
        context.view_layer.objects.active = prev_active_object
        context.scene.cursor.location = prev_cursor_location

        return {'FINISHED'}
