from .import_base import NetworkInfoImportBase
import libsbmlnetworkeditor
import math


class NetworkInfoImportFromSBMLModel(NetworkInfoImportBase):
    def __init__(self):
        super().__init__()
        self.sbml_network_editor = None

    def extract_info(self, graph):
        super().extract_info(graph)
        self.sbml_network_editor = libsbmlnetworkeditor.LibSBMLNetworkEditor(graph)
        self.extract_layout_info()
        self.extract_render_info()

    def extract_layout_info(self):
        if not self.sbml_network_editor.getNumLayouts():
            self.sbml_network_editor.createDefaultLayout()
        self.extract_layout_features()

    def extract_render_info(self):
        self.extract_global_render_info()
        self.extract_global_render_features()
        self.extract_local_render_info()
        self.extract_local_render_features()

    def extract_layout_features(self):
        for c_index in range(self.sbml_network_editor.getNumCompartments()):
            self.add_compartment(self.sbml_network_editor.getNthCompartmentId(c_index))

        for s_index in range(self.sbml_network_editor.getNumSpecies()):
            self.add_species(self.sbml_network_editor.getNthSpeciesId(s_index))

        for r_index in range(self.sbml_network_editor.getNumReactions()):
            self.add_reaction(self.sbml_network_editor.getNthReactionId(r_index))

    def extract_global_render_info(self):
        if not self.sbml_network_editor.getNumGlobalRenderInformation() and\
            not self.sbml_network_editor.getNumLocalRenderInformation():
            self.sbml_network_editor.createDefaultGlobalRenderInformation()

    def extract_global_render_features(self):
        if self.sbml_network_editor.isSetBackgroundColor():
            self.background_color = self.sbml_network_editor.getBackgroundColor()

        # get colors info
        for c_index in range(self.sbml_network_editor.getNumGlobalColors()):
            self.add_color(self.sbml_network_editor.getNthGlobalColorId(c_index))

        # get gradients info
        for g_index in range(self.sbml_network_editor.getNumGlobalGradients()):
            self.add_gradient(self.sbml_network_editor.getNthGlobalGradientId(g_index))

        # get line ending info
        for le_index in range(self.sbml_network_editor.getNumGlobalLineEndings()):
            self.add_line_ending(self.sbml_network_editor.getNthGlobalLineEndingId(le_index))

    def extract_local_render_info(self):
        if self.sbml_network_editor.getNumGlobalRenderInformation():
            self.sbml_network_editor.createDefaultLocalRenderInformation()

    def extract_local_render_features(self):
        # get colors info
        for c_index in range(self.sbml_network_editor.getNumLocalColors()):
            self.add_color(self.sbml_network_editor.getNthLocalColorId(c_index))

        # get gradients info
        for g_index in range(self.sbml_network_editor.getNumLocalGradients()):
            self.add_gradient(self.sbml_network_editor.getNthLocalGradientId(g_index))

        # get line ending info
        for le_index in range(self.sbml_network_editor.getNumLocalLineEndings()):
            self.add_line_ending(self.sbml_network_editor.getNthLocalLineEndingId(le_index))

    def extract_extents(self, bounding_box_x, bounding_box_y, bounding_box_width, bounding_box_height):
        self.extents['minX'] = min(self.extents['minX'], bounding_box_x)
        self.extents['maxX'] = max(self.extents['maxX'], bounding_box_x + bounding_box_width)
        self.extents['minY'] = min(self.extents['minY'], bounding_box_y)
        self.extents['maxY'] = max(self.extents['maxY'], bounding_box_y + bounding_box_height)

    def add_compartment(self, compartment_id):
        for cg_index in range(self.sbml_network_editor.getNumCompartmentGlyphs(compartment_id)):
            compartment = self.extract_go_object_features(compartment_id, cg_index)
            self.compartments.append(compartment)

    def add_species(self, species_id):
        for sg_index in range(self.sbml_network_editor.getNumSpeciesGlyphs(species_id)):
            species = self.extract_go_object_features(species_id, sg_index)
            species['compartment'] = self.sbml_network_editor.getCompartmentId(species_id)
            self.species.append(species)

    def add_reaction(self, reaction_id):
        for rg_index in range(self.sbml_network_editor.getNumReactionGlyphs(reaction_id)):
            reaction = self.extract_go_object_features(reaction_id, rg_index)
            reaction['compartment'] = self.sbml_network_editor.getCompartmentId(reaction_id)
            reaction['speciesReferences'] = []
            for srg_index in range(self.sbml_network_editor.getNumSpeciesReferenceGlyphs(reaction_id, rg_index)):
                species_reference = {'reaction': reaction_id}
                species_reference['reaction_glyph_index'] = rg_index
                species_reference['species'] = self.sbml_network_editor.getSpeciesReferenceSpeciesId(reaction_id, rg_index, srg_index)
                species_reference['species_glyph_id'] = self.sbml_network_editor.getSpeciesReferenceSpeciesGlyphId(reaction_id, rg_index, srg_index)
                species_reference['species_reference_glyph_index'] = srg_index
                if self.sbml_network_editor.isSetSpeciesReferenceRole(reaction_id, rg_index, srg_index):
                    species_reference['role'] = self.sbml_network_editor.getSpeciesReferenceRole(reaction_id, rg_index, srg_index)
                reaction['speciesReferences'].append(species_reference)
            self.reactions.append(reaction)

    def add_color(self, color_id):
        self.colors.append({'id': color_id})

    def add_gradient(self, gradient_id):
        self.gradients.append({'id': gradient_id})

    def add_line_ending(self, line_ending_id):
        self.line_endings.append({'id': line_ending_id})

    def extract_go_object_features(self, entity_id, graphical_object_index):
        features = {'referenceId': entity_id, 'id': self.sbml_network_editor.getNthGraphicalObjectId(entity_id, graphical_object_index),
                    'index': graphical_object_index}
        if self.sbml_network_editor.getNthGraphicalObjectMetaId(entity_id, graphical_object_index):
            features['metaId'] = self.sbml_network_editor.getNthGraphicalObjectMetaId(entity_id, graphical_object_index)

        return features

    def extract_compartment_features(self, compartment):
        if compartment['referenceId']:
            compartment['features'] = self.extract_go_general_features(compartment['referenceId'], compartment['index'])
            compartment['texts'] = self.extract_go_text_features(compartment['referenceId'], compartment['index'])
            self.extract_extents(self.sbml_network_editor.getX(compartment['referenceId'], compartment['index']),
                                 self.sbml_network_editor.getY(compartment['referenceId'], compartment['index']),
                                 self.sbml_network_editor.getWidth(compartment['referenceId'], compartment['index']),
                                 self.sbml_network_editor.getHeight(compartment['referenceId'], compartment['index']))

    def extract_species_features(self, species):
        if species['referenceId']:
            species['features'] = self.extract_go_general_features(species['referenceId'], species['index'])
            species['texts'] = self.extract_go_text_features(species['referenceId'], species['index'])
            self.extract_extents(self.sbml_network_editor.getX(species['referenceId'], species['index']),
                                 self.sbml_network_editor.getY(species['referenceId'], species['index']),
                                 self.sbml_network_editor.getWidth(species['referenceId'], species['index']),
                                 self.sbml_network_editor.getHeight(species['referenceId'], species['index']))

    def extract_reaction_features(self, reaction):
        if reaction['referenceId']:
            reaction['features'] = self.extract_go_general_features(reaction['referenceId'], reaction['index'])
            self.extract_extents(self.sbml_network_editor.getX(reaction['referenceId'], reaction['index']),
                                 self.sbml_network_editor.getY(reaction['referenceId'], reaction['index']),
                                 self.sbml_network_editor.getWidth(reaction['referenceId'], reaction['index']),
                                 self.sbml_network_editor.getHeight(reaction['referenceId'], reaction['index']))
            if self.sbml_network_editor.isSetCurve(reaction['referenceId'], reaction['index']):
                curve = []
                for cs_index in range(self.sbml_network_editor.getNumCurveSegments(reaction['referenceId'], reaction['index'])):
                    curve_segment = {'startX': self.sbml_network_editor.getCurveSegmentStartPointX(reaction['referenceId'], reaction['index'], cs_index),
                                'startY': self.sbml_network_editor.getCurveSegmentStartPointY(reaction['referenceId'], reaction['index'], cs_index),
                                'endX': self.sbml_network_editor.getCurveSegmentEndPointX(reaction['referenceId'], reaction['index'], cs_index),
                                'endY': self.sbml_network_editor.getCurveSegmentEndPointY(reaction['referenceId'], reaction['index'], cs_index)}
                    if self.sbml_network_editor.isCurveSegmentCubicBezier(reaction['referenceId'], reaction['index'], cs_index):
                        curve_segment["basePoint1X"] = self.sbml_network_editor.getCurveSegmentBasePoint1X(reaction['referenceId'], reaction['index'], cs_index)
                        curve_segment["basePoint1Y"] = self.sbml_network_editor.getCurveSegmentBasePoint1Y(reaction['referenceId'], reaction['index'], cs_index)
                        curve_segment["basePoint2X"] = self.sbml_network_editor.getCurveSegmentBasePoint2X(reaction['referenceId'], reaction['index'], cs_index)
                        curve_segment["basePoint2Y"] = self.sbml_network_editor.getCurveSegmentBasePoint2Y(reaction['referenceId'], reaction['index'], cs_index)
                    curve.append(curve_segment)
                reaction['features']['curve'] = curve
                reaction['features']['graphicalCurve'] = self.extract_curve_features(reaction['referenceId'], reaction['index'])

    def extract_species_reference_features(self, species_reference):
        species_reference['features'] = {}
        if species_reference['reaction']:
            curve = []
            for cs_index in range(self.sbml_network_editor.getNumSpeciesReferenceCurveSegments(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'])):
                curve_segment = {'startX': self.sbml_network_editor.getSpeciesReferenceCurveSegmentStartPointX(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index),
                            'startY': self.sbml_network_editor.getSpeciesReferenceCurveSegmentStartPointY(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index),
                            'endX': self.sbml_network_editor.getSpeciesReferenceCurveSegmentEndPointX(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index),
                            'endY': self.sbml_network_editor.getSpeciesReferenceCurveSegmentEndPointY(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)}
                if self.sbml_network_editor.isSpeciesReferenceCurveSegmentCubicBezier(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index):
                    curve_segment["basePoint1X"] = self.sbml_network_editor.getSpeciesReferenceCurveSegmentBasePoint1X(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)
                    curve_segment["basePoint1Y"] = self.sbml_network_editor.getSpeciesReferenceCurveSegmentBasePoint1Y(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)
                    curve_segment["basePoint2X"] = self.sbml_network_editor.getSpeciesReferenceCurveSegmentBasePoint2X(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)
                    curve_segment["basePoint2Y"] = self.sbml_network_editor.getSpeciesReferenceCurveSegmentBasePoint2Y(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)

                if cs_index == 0:
                    species_reference['features']['startPoint'] = {'x': curve_segment['startX'], 'y': curve_segment['startY']}
                    if 'basePoint1X' in list(curve_segment.keys()) and not curve_segment['startX'] == curve_segment['basePoint1X']:
                        species_reference['features']['startSlope'] = math.atan2(curve_segment['startY'] - curve_segment['basePoint1Y'], curve_segment['startX'] - curve_segment['basePoint1X'])
                    else:
                        species_reference['features']['startSlope'] = math.atan2(curve_segment['startY'] - curve_segment['endY'], curve_segment['startX'] - curve_segment['endX'])
                if cs_index == self.sbml_network_editor.getNumSpeciesReferenceCurveSegments(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index']) - 1:
                    species_reference['features']['endPoint'] = {'x': curve_segment['endX'], 'y': curve_segment['endY']}
                    if 'basePoint2X' in list(curve_segment.keys()) and not curve_segment['endX'] == curve_segment['basePoint2X']:
                        species_reference['features']['endSlope'] = math.atan2(curve_segment['endY'] - curve_segment['basePoint2Y'], curve_segment['endX'] - curve_segment['basePoint2X'])
                    else:
                        species_reference['features']['endSlope'] = math.atan2(curve_segment['endY'] - curve_segment['startY'], curve_segment['endX'] - curve_segment['startX'])
                curve.append(curve_segment)
            species_reference['features']['curve'] = curve
            species_reference['features']['graphicalCurve'] = self.extract_species_reference_curve_features(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'])

    def extract_color_features(self, color):
        color['features'] = {}
        if self.sbml_network_editor.isSetColorValue(color['id']):
            color['features']['value'] = self.sbml_network_editor.getColorValue(color['id'])
        else:
            color['features']['value'] = "#ffffff"

    def extract_gradient_features(self, gradient):
        gradient['features'] = {}
        # get spread method
        if self.sbml_network_editor.isSetSpreadMethod(gradient['id']):
            gradient['features']['spreadMethod'] = self.sbml_network_editor.getSpreadMethod(gradient['id'])

        # get gradient stops
        stops_ = []
        for s_index in range(self.sbml_network_editor.getNumGradientStops(gradient['id'])):
            stop_ = {}
            # get offset
            if self.sbml_network_editor.isSetOffset(gradient['id'], s_index):
                stop_['offset'] = {'abs': 0, 'rel': self.sbml_network_editor.getOffset(gradient['id'], s_index)}

            # get stop color
            if self.sbml_network_editor.isSetStopColor(gradient['id'], s_index):
                stop_['color'] = self.sbml_network_editor.getStopColor(gradient['id'], s_index)
            stops_.append(stop_)
        gradient['features']['stops'] = stops_

        # linear gradient
        if self.sbml_network_editor.isLinearGradient(gradient['id']):
            gradient['features']['type'] = 'linear'
            # get start
            gradient['features']['start'] = \
                {'x': {'abs': 0.0,
                        'rel': self.sbml_network_editor.getLinearGradientX1(gradient['id'])},
                 'y': {'abs': 0.0,
                        'rel': self.sbml_network_editor.getLinearGradientY1(gradient['id'])}}
            # get end
            gradient['features']['end'] = \
                {'x': {'abs': 0.0,
                        'rel': self.sbml_network_editor.getLinearGradientX2(gradient['id'])},
                 'y': {'abs': 0.0,
                        'rel': self.sbml_network_editor.getLinearGradientY2(gradient['id'])}}
        # radial gradient
        elif self.sbml_network_editor.isRadialGradient(gradient['id']):
            gradient['features']['type'] = 'radial'
            # get center
            gradient['features']['center'] = \
                {'x': {'abs': 0.0,
                        'rel': self.sbml_network_editor.getRadialGradientCenterX(gradient['id'])},
                 'y': {'abs': 0.0,
                        'rel': self.sbml_network_editor.getRadialGradientCenterY(gradient['id'])}}
            # get focal
            gradient['features']['focalPoint'] = \
                {'x': {'abs': 0.0,
                        'rel': self.sbml_network_editor.getRadialGradientFocalX(gradient['id'])},
                 'y': {'abs': 0.0,
                        'rel': self.sbml_network_editor.getRadialGradientFocalY(gradient['id'])}}
            # get radius
            gradient['features']['radius'] = \
                {'abs': 0.0,
                    'rel': self.sbml_network_editor.getRadialGradientRadius(gradient['id'])}

    def extract_line_ending_features(self, line_ending):
        line_ending['features'] = {}
        line_ending['features']['boundingBox'] = {'x': self.sbml_network_editor.getLineEndingBoundingBoxX(line_ending['id']),
                                                  'y': self.sbml_network_editor.getLineEndingBoundingBoxY(line_ending['id']),
                                                  'width': self.sbml_network_editor.getLineEndingBoundingBoxWidth(line_ending['id']),
                                                  'height': self.sbml_network_editor.getLineEndingBoundingBoxHeight(line_ending['id'])}
        line_ending['features']['graphicalShape'] = self.extract_line_ending_graphical_shape_features(line_ending['id'])

    def extract_go_text_features(self, entity_id, graphical_object_index):
        text_features = []
        for tg_index in range(self.sbml_network_editor.getNumTextGlyphs(entity_id, graphical_object_index)):
            features = {'features': {'plainText': self.sbml_network_editor.getText(entity_id, graphical_object_index),
                                     'boundingBox': self.extract_bounding_box_features(entity_id,
                                                                                       graphical_object_index),
                                     'graphicalText': self.extract_text_features(entity_id, graphical_object_index)}}
            text_features.append(features)

        return text_features

    def extract_text_features(self, entity_id, graphical_object_index):
        features = {}
        # get stroke color
        if self.sbml_network_editor.isSetFontColor(entity_id, graphical_object_index):
            features['strokeColor'] = self.sbml_network_editor.getFontColor(entity_id, graphical_object_index)
        # get font family
        if self.sbml_network_editor.isSetFontFamily(entity_id, graphical_object_index):
            features['fontFamily'] = self.sbml_network_editor.getFontFamily(entity_id, graphical_object_index)
        # get font size
        if self.sbml_network_editor.isSetFontSize(entity_id, graphical_object_index):
            features['fontSize'] = {'abs': self.sbml_network_editor.getFontSize(entity_id, graphical_object_index),
                                     'rel': 0.0}
        # get font weight
        if self.sbml_network_editor.isSetFontWeight(entity_id, graphical_object_index):
            features['fontWeight'] = self.sbml_network_editor.getFontWeight(entity_id, graphical_object_index)
        # get font style
        if self.sbml_network_editor.isSetFontStyle(entity_id, graphical_object_index):
            features['fontStyle'] = self.sbml_network_editor.getFontStyle(entity_id, graphical_object_index)
        # get horizontal text anchor
        if self.sbml_network_editor.isSetTextHorizontalAlignment(entity_id, graphical_object_index):
            features['hTextAnchor'] = self.sbml_network_editor.getTextHorizontalAlignment(entity_id, graphical_object_index)
        # get vertical text anchor
        if self.sbml_network_editor.isSetTextVerticalAlignment(entity_id, graphical_object_index):
            features['vTextAnchor'] = self.sbml_network_editor.getTextVerticalAlignment(entity_id, graphical_object_index)

        return features

    def extract_go_general_features(self, entity_id, graphical_object_index):
        features = {'boundingBox': self.extract_bounding_box_features(entity_id, graphical_object_index),
                    'graphicalShape': self.extract_graphical_shape_features(entity_id, graphical_object_index)}

        return features

    def extract_bounding_box_features(self, entity_id, graphical_object_index):
        return {'x': self.sbml_network_editor.getX(entity_id, graphical_object_index), 'y': self.sbml_network_editor.getY(entity_id, graphical_object_index),
                'width': self.sbml_network_editor.getWidth(entity_id, graphical_object_index), 'height': self.sbml_network_editor.getHeight(entity_id, graphical_object_index)}

    def extract_graphical_shape_features(self, entity_id, graphical_object_index):
        graphical_shape_info = {}
        graphical_shape_info = self.extract_render_group_general_features(entity_id, graphical_object_index)
        graphical_shape_info['geometricShapes'] = self.extract_render_group_geometric_shapes(entity_id, graphical_object_index)

        return graphical_shape_info

    def extract_line_ending_graphical_shape_features(self, line_ending_id):
        line_ending_graphical_shape_info = {}
        line_ending_graphical_shape_info = self.extract_line_ending_render_group_general_features(line_ending_id)
        line_ending_graphical_shape_info['geometricShapes'] = self.extract_line_ending_render_group_geometric_shapes(line_ending_id)

        return line_ending_graphical_shape_info

    def extract_render_group_general_features(self, entity_id, graphical_object_index):
        render_group_general_features = {}
        # get stroke color
        if self.sbml_network_editor.isSetBorderColor(entity_id, graphical_object_index):
            render_group_general_features['strokeColor'] = self.sbml_network_editor.getBorderColor(entity_id, graphical_object_index)
        # get stroke width
        if self.sbml_network_editor.isSetBorderWidth(entity_id, graphical_object_index):
            render_group_general_features['strokeWidth'] = self.sbml_network_editor.getBorderWidth(entity_id, graphical_object_index)
        # get stroke dash array
        if self.sbml_network_editor.getNumBorderDashes(entity_id, graphical_object_index):
            dash_array = []
            for d_index in range(self.sbml_network_editor.getNumBorderDashes(entity_id, graphical_object_index)):
                dash_array.append(self.sbml_network_editor.getNthBorderDash(entity_id, graphical_object_index, d_index))
            render_group_general_features['strokeDashArray'] = tuple(dash_array)
        # get fill color
        if self.sbml_network_editor.isSetFillColor(entity_id, graphical_object_index):
            render_group_general_features['fillColor'] = self.sbml_network_editor.getFillColor(entity_id, graphical_object_index)
        # get fill rule
        if self.sbml_network_editor.isSetFillRule(entity_id, graphical_object_index):
            render_group_general_features['fillRule'] = self.sbml_network_editor.getFillRule(entity_id, graphical_object_index)

        return render_group_general_features

    def extract_line_ending_render_group_general_features(self, line_ending_id):
        line_ending_render_group_general_features = {}
        # get stroke color
        if self.sbml_network_editor.isSetLineEndingBorderColor(line_ending_id):
            line_ending_render_group_general_features['strokeColor'] = self.sbml_network_editor.getLineEndingBorderColor(line_ending_id)
        # get stroke width
        if self.sbml_network_editor.isSetLineEndingBorderWidth(line_ending_id):
            line_ending_render_group_general_features['strokeWidth'] = self.sbml_network_editor.getLineEndingBorderWidth(line_ending_id)
        # get stroke dash array
        if self.sbml_network_editor.getNumLineEndingBorderDashes(line_ending_id):
            dash_array = []
            for d_index in range(self.sbml_network_editor.getNumLineEndingBorderDashes(line_ending_id)):
                dash_array.append(self.sbml_network_editor.getLineEndingNthBorderDash(line_ending_id, d_index))
            line_ending_render_group_general_features['strokeDashArray'] = tuple(dash_array)
        # get fill color
        if self.sbml_network_editor.isSetLineEndingFillColor(line_ending_id):
            line_ending_render_group_general_features['fillColor'] = self.sbml_network_editor.getLineEndingFillColor(line_ending_id)
        # get fill rule
        if self.sbml_network_editor.isSetLineEndingFillRule(line_ending_id):
            line_ending_render_group_general_features['fillRule'] = self.sbml_network_editor.getLineEndingFillRule(line_ending_id)

        return line_ending_render_group_general_features

    def extract_render_group_geometric_shapes(self, entity_id, graphical_object_index):
        geometric_shapes = []
        for gs_index in range(self.sbml_network_editor.getNumGeometricShapes(entity_id, graphical_object_index)):
            geometric_shape = {}
            geometric_shape.update(self.extract_geometric_shape_general_features(entity_id, graphical_object_index, gs_index))
            geometric_shape.update(self.extract_geometric_shape_exclusive_features(entity_id, graphical_object_index, gs_index))
            geometric_shapes.append(geometric_shape)

        return geometric_shapes

    def extract_line_ending_render_group_geometric_shapes(self, line_ending_id):
        geometric_shapes = []
        for gs_index in range(self.sbml_network_editor.getNumLineEndingGeometricShapes(line_ending_id)):
            geometric_shape = {}
            geometric_shape.update(self.extract_line_ending_geometric_shape_general_features(line_ending_id, gs_index))
            geometric_shape.update(self.extract_line_ending_geometric_shape_exclusive_features(line_ending_id, gs_index))
            geometric_shapes.append(geometric_shape)

        return geometric_shapes

    def extract_geometric_shape_general_features(self, entity_id, graphical_object_index, geometric_shape_index):
        geometric_shape_general_features = {}
        # get stroke color
        if self.sbml_network_editor.isSetBorderColor(entity_id, graphical_object_index):
            geometric_shape_general_features['strokeColor'] = self.sbml_network_editor.getBorderColor(entity_id,
                                                                                                   graphical_object_index)

        # get stroke width
        if self.sbml_network_editor.isSetBorderWidth(entity_id, graphical_object_index):
            geometric_shape_general_features['strokeWidth'] = self.sbml_network_editor.getBorderWidth(entity_id,
                                                                                                   graphical_object_index)

        # get stroke dash array
        if self.sbml_network_editor.getNumBorderDashes(entity_id, graphical_object_index):
            dash_array = []
            for d_index in range(self.sbml_network_editor.getNumBorderDashes(entity_id, graphical_object_index)):
                dash_array.append(self.sbml_network_editor.getNthBorderDash(entity_id, graphical_object_index, d_index))
            geometric_shape_general_features['strokeDashArray'] = tuple(dash_array)

        return geometric_shape_general_features

    def extract_line_ending_geometric_shape_general_features(self, line_ending_id, geometric_shape_index):
        geometric_shape_general_features = {}
        # get stroke color
        if self.sbml_network_editor.isSetLineEndingBorderColor(line_ending_id):
            geometric_shape_general_features['strokeColor'] = self.sbml_network_editor.getLineEndingBorderColor(line_ending_id)

        # get stroke width
        if self.sbml_network_editor.isSetLineEndingBorderWidth(line_ending_id):
            geometric_shape_general_features['strokeWidth'] = self.sbml_network_editor.getLineEndingBorderWidth(line_ending_id)

        # get stroke dash array
        if self.sbml_network_editor.getNumLineEndingBorderDashes(line_ending_id):
            dash_array = []
            for d_index in range(self.sbml_network_editor.getNumLineEndingBorderDashes(line_ending_id)):
                dash_array.append(self.sbml_network_editor.getLineEndingNthBorderDash(line_ending_id, d_index))
            geometric_shape_general_features['strokeDashArray'] = tuple(dash_array)

        return geometric_shape_general_features

    def extract_geometric_shape_exclusive_features(self, entity_id, graphical_object_index, geometric_shape_index):
        if self.sbml_network_editor.isImage(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_image_shape_features(entity_id, geometric_shape_index, graphical_object_index)
        elif self.sbml_network_editor.isRenderCurve(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_curve_shape_features(entity_id, geometric_shape_index, graphical_object_index)
        elif self.sbml_network_editor.isText(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_text_shape_features(entity_id, geometric_shape_index, graphical_object_index)
        elif self.sbml_network_editor.isRectangle(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_rectangle_shape_features(entity_id, geometric_shape_index, graphical_object_index)
        elif self.sbml_network_editor.isEllipse(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_ellipse_shape_features(entity_id, geometric_shape_index, graphical_object_index)
        elif self.sbml_network_editor.isPolygon(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_polygon_shape_features(entity_id, geometric_shape_index, graphical_object_index)

        return {'shape': "None"}

    def extract_line_ending_geometric_shape_exclusive_features(self, line_ending_id, geometric_shape_index):
        if self.sbml_network_editor.isLineEndingImage(line_ending_id):
            return self.extract_line_ending_image_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network_editor.isLineEndingRenderCurve(line_ending_id):
            return self.extract_line_ending_curve_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network_editor.isLineEndingText(line_ending_id):
            return self.extract_line_ending_text_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network_editor.isLineEndingRectangle(line_ending_id):
            return self.extract_line_ending_rectangle_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network_editor.isLineEndingEllipse(line_ending_id):
            return self.extract_line_ending_ellipse_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network_editor.isLineEndingPolygon(line_ending_id):
            return self.extract_line_ending_polygon_shape_features(line_ending_id, geometric_shape_index)

    def extract_curve_features(self, entity_id, graphical_object_index):
        curve_features = {}
        # get stroke color
        if self.sbml_network_editor.isSetBorderColor(entity_id, graphical_object_index):
            curve_features['strokeColor'] = self.sbml_network_editor.getBorderColor(entity_id, graphical_object_index)

        # get stroke width
        if self.sbml_network_editor.isSetBorderWidth(entity_id, graphical_object_index):
            curve_features['strokeWidth'] = self.sbml_network_editor.getBorderWidth(entity_id, graphical_object_index)

        # get stroke dash array
        if self.sbml_network_editor.getNumBorderDashes(entity_id, graphical_object_index):
            dash_array = []
            for d_index in range(self.sbml_network_editor.getNumBorderDashes(entity_id, graphical_object_index)):
                dash_array.append(self.sbml_network_editor.getNthBorderDash(entity_id, graphical_object_index, d_index))
            curve_features['strokeDashArray'] = tuple(dash_array)

        # get heads
        curve_features['heads'] = {}
        if self.sbml_network_editor.isSetStartHead(entity_id, graphical_object_index):
            curve_features['heads']['start'] = self.sbml_network_editor.getStartHead(entity_id, graphical_object_index)
        elif self.sbml_network_editor.isSetEndHead(entity_id, graphical_object_index):
            curve_features['heads']['end'] = self.sbml_network_editor.getEndHead(entity_id, graphical_object_index)

        return curve_features

    def extract_species_reference_curve_features(self, reaction_id, reaction_glyph_index, species_reference_glyph_index):
        curve_features = {}
        # get stroke color
        if self.sbml_network_editor.isSetSpeciesReferenceBorderColor(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            curve_features['strokeColor'] = self.sbml_network_editor.getSpeciesReferenceBorderColor(reaction_id, reaction_glyph_index, species_reference_glyph_index)

        # get stroke width
        if self.sbml_network_editor.isSetSpeciesReferenceBorderWidth(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            curve_features['strokeWidth'] = self.sbml_network_editor.getSpeciesReferenceBorderWidth(reaction_id, reaction_glyph_index, species_reference_glyph_index)

        # get stroke dash array
        if self.sbml_network_editor.getNumSpeciesReferenceBorderDashes(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            dash_array = []
            for d_index in range(self.sbml_network_editor.getNumSpeciesReferenceBorderDashes(reaction_id, reaction_glyph_index, species_reference_glyph_index)):
                dash_array.append(self.sbml_network_editor.getSpeciesReferenceNthBorderDash(reaction_id, reaction_glyph_index, species_reference_glyph_index, d_index))
            curve_features['strokeDashArray'] = tuple(dash_array)

        # get heads
        curve_features['heads'] = {}
        if self.sbml_network_editor.isSetSpeciesReferenceStartHead(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            curve_features['heads']['start'] = self.sbml_network_editor.getSpeciesReferenceStartHead(reaction_id, reaction_glyph_index, species_reference_glyph_index)
        elif self.sbml_network_editor.isSetSpeciesReferenceEndHead(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            curve_features['heads']['end'] = self.sbml_network_editor.getSpeciesReferenceEndHead(reaction_id, reaction_glyph_index, species_reference_glyph_index)

        return curve_features

    def extract_image_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        image_shape_info = {'shape': "image"}

        # get position x
        if self.sbml_network_editor.isSetGeometricShapeX(entity_id, graphical_object_index):
            image_shape_info['x'] = {'abs': self.sbml_network_editor.getGeometricShapeX(entity_id, graphical_object_index),
                                     'rel': 0.0}

        # get position y
        if self.sbml_network_editor.isSetGeometricShapeY(entity_id, graphical_object_index):
            image_shape_info['y'] = {'abs': self.sbml_network_editor.getGeometricShapeY(entity_id, graphical_object_index),
                                     'rel': 0.0}

        # get dimension width
        if self.sbml_network_editor.isSetGeometricShapeWidth(entity_id, graphical_object_index):
            image_shape_info['width'] = {'abs': self.sbml_network_editor.getGeometricShapeWidth(entity_id, graphical_object_index),
                                        'rel': 0.0}

        # get dimension height
        if self.sbml_network_editor.isSetGeometricShapeHeight(entity_id, graphical_object_index):
            image_shape_info['height'] = {'abs': self.sbml_network_editor.getGeometricShapeHeight(entity_id, graphical_object_index),
                                         'rel': 0.0}

        # get href
        if self.sbml_network_editor.isSetGeometricShapeHref(entity_id, graphical_object_index):
            image_shape_info['href'] = self.sbml_network_editor.getGeometricShapeHref(entity_id, graphical_object_index)

        return image_shape_info

    def extract_line_ending_image_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        image_shape_info = {'shape': "image"}

        # get position x
        if self.sbml_network_editor.isSetLineEndingGeometricShapeX(line_ending_id):
            image_shape_info['x'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeX(line_ending_id),
                                     'rel': 0.0}

        # get position y
        if self.sbml_network_editor.isSetLineEndingGeometricShapeY(line_ending_id):
            image_shape_info['y'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeY(line_ending_id),
                                     'rel': 0.0}

        # get dimension width
        if self.sbml_network_editor.isSetLineEndingGeometricShapeWidth(line_ending_id):
            image_shape_info['width'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeWidth(line_ending_id),
                                        'rel': 0.0}

        # get dimension height
        if self.sbml_network_editor.isSetLineEndingGeometricShapeHeight(line_ending_id):
            image_shape_info['height'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeHeight(line_ending_id),
                                         'rel': 0.0}

        # get href
        if self.sbml_network_editor.isSetLineEndingGeometricShapeHref(line_ending_id):
            image_shape_info['href'] = self.sbml_network_editor.getLineEndingGeometricShapeHref(line_ending_id)

        return image_shape_info

    def extract_curve_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        curve_shape_info = {'shape': "renderCurve"}

        vertices_ = []
        for v_index in range(self.sbml_network_editor.getNumCurveSegments(entity_id, graphical_object_index)):
            vertex_ = {}
            vertex_['renderPointX'] = {'abs': self.sbml_network_editor.getCurveSegmentStartPointX(entity_id, graphical_object_index, v_index),
                                       'rel': 0.0}
            vertex_['renderPointY'] = {'abs': self.sbml_network_editor.getCurveSegmentStartPointY(entity_id, graphical_object_index, v_index),
                                       'rel': 0.0}
            if self.sbml_network_editor.isCurveSegmentCubicBezier(entity_id, graphical_object_index, v_index):
                vertex_['basePoint1X'] = {'abs': self.sbml_network_editor.getCurveSegmentBasePoint1X(entity_id, graphical_object_index, v_index),
                                          'rel': 0.0}
                vertex_['basePoint1Y'] = {'abs': self.sbml_network_editor.getCurveSegmentBasePoint1Y(entity_id, graphical_object_index, v_index),
                                          'rel': 0.0}
                vertex_['basePoint2X'] = {'abs': self.sbml_network_editor.getCurveSegmentBasePoint2X(entity_id, graphical_object_index, v_index),
                                          'rel': 0.0}
                vertex_['basePoint2Y'] = {'abs': self.sbml_network_editor.getCurveSegmentBasePoint2Y(entity_id, graphical_object_index, v_index),
                                          'rel': 0.0}
            vertices_.append(vertex_)
        curve_shape_info['vertices'] = vertices_

        return curve_shape_info

    def extract_line_ending_curve_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        curve_shape_info = {'shape': "renderCurve"}

        vertices_ = []
        for v_index in range(self.sbml_network_editor.getNumLineEndingCurveSegments(line_ending_id)):
            vertex_ = {}
            vertex_['renderPointX'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentStartPointX(line_ending_id, v_index),
                                       'rel': 0.0}
            vertex_['renderPointY'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentStartPointY(line_ending_id, v_index),
                                       'rel': 0.0}
            if self.sbml_network_editor.isLineEndingGeometricShapeSegmentCubicBezier(line_ending_id, v_index):
                vertex_['basePoint1X'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentBasePoint1X(line_ending_id, v_index),
                                          'rel': 0.0}
                vertex_['basePoint1Y'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentBasePoint1Y(line_ending_id, v_index),
                                          'rel': 0.0}
                vertex_['basePoint2X'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentBasePoint2X(line_ending_id, v_index),
                                          'rel': 0.0}
                vertex_['basePoint2Y'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentBasePoint2Y(line_ending_id, v_index),
                                          'rel': 0.0}
            vertices_.append(vertex_)
        curve_shape_info['vertices'] = vertices_

        return curve_shape_info

    def extract_text_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        text_shape_info = {'shape': "text"}

        # get position x
        if self.sbml_network_editor.isSetGeometricShapeX(entity_id, graphical_object_index):
            text_shape_info['x'] = {'abs': self.sbml_network_editor.getGeometricShapeX(entity_id, graphical_object_index),
                                    'rel': 0.0}

        # get position y
        if self.sbml_network_editor.isSetGeometricShapeY(entity_id, graphical_object_index):
            text_shape_info['y'] = {'abs': self.sbml_network_editor.getGeometricShapeY(entity_id, graphical_object_index),
                                    'rel': 0.0}

        # get font family
        if self.sbml_network_editor.isSetFontFamily(entity_id, graphical_object_index):
            text_shape_info['fontFamily'] = self.sbml_network_editor.getFontFamily(entity_id, graphical_object_index)

        # get font size
        if self.sbml_network_editor.isSetFontSize(entity_id, graphical_object_index):
            text_shape_info['fontSize'] = {'abs': self.sbml_network_editor.getFontSize(entity_id, graphical_object_index),
                                          'rel': 0.0}

        # get font weight
        if self.sbml_network_editor.isSetFontWeight(entity_id, graphical_object_index):
            text_shape_info['fontWeight'] = self.sbml_network_editor.getFontWeight(entity_id, graphical_object_index)

        # get font style
        if self.sbml_network_editor.isSetFontStyle(entity_id, graphical_object_index):
            text_shape_info['fontStyle'] = self.sbml_network_editor.getFontStyle(entity_id, graphical_object_index)

        # get horizontal text anchor
        if self.sbml_network_editor.isSetHorizontalAlignment(entity_id, graphical_object_index):
            text_shape_info['hTextAnchor'] = self.sbml_network_editor.getHorizontalAlignment(entity_id, graphical_object_index)

        # get vertical text anchor
        if self.sbml_network_editor.isSetVerticalAlignment(entity_id, graphical_object_index):
            text_shape_info['vTextAnchor'] = self.sbml_network_editor.getVerticalAlignment(entity_id, graphical_object_index)

        return text_shape_info

    def extract_line_ending_text_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        text_shape_info = {'shape': "text"}

        # get position x
        if self.sbml_network_editor.isSetLineEndingGeometricShapeX(line_ending_id):
            text_shape_info['x'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeX(line_ending_id),
                                    'rel': 0.0}

        # get position y
        if self.sbml_network_editor.isSetLineEndingGeometricShapeY(line_ending_id):
            text_shape_info['y'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeY(line_ending_id),
                                    'rel': 0.0}

        # get font family
        if self.sbml_network_editor.isSetLineEndingFontFamily(line_ending_id):
            text_shape_info['fontFamily'] = self.sbml_network_editor.getLineEndingFontFamily(line_ending_id)

        # get font size
        if self.sbml_network_editor.isSetLineEndingFontSize(line_ending_id):
            text_shape_info['fontSize'] = {'abs': self.sbml_network_editor.getLineEndingFontSize(line_ending_id),
                                          'rel': 0.0}

        # get font weight
        if self.sbml_network_editor.isSetLineEndingFontWeight(line_ending_id):
            text_shape_info['fontWeight'] = self.sbml_network_editor.getLineEndingFontWeight(line_ending_id)

        # get font style
        if self.sbml_network_editor.isSetLineEndingFontStyle(line_ending_id):
            text_shape_info['fontStyle'] = self.sbml_network_editor.getLineEndingFontStyle(line_ending_id)

        # get horizontal text anchor
        if self.sbml_network_editor.isSetLineEndingHorizontalAlignment(line_ending_id):
            text_shape_info['hTextAnchor'] = self.sbml_network_editor.getLineEndingHorizontalAlignment(line_ending_id)

        # get vertical text anchor
        if self.sbml_network_editor.isSetLineEndingVerticalAlignment(line_ending_id):
            text_shape_info['vTextAnchor'] = self.sbml_network_editor.getLineEndingVerticalAlignment(line_ending_id)

        return text_shape_info

    def extract_rectangle_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        rectangle_shape_info = {'shape': "rectangle"}

        # get fill color
        if self.sbml_network_editor.isSetFillColor(entity_id, graphical_object_index):
            rectangle_shape_info['fillColor'] = self.sbml_network_editor.getFillColor(entity_id, graphical_object_index)

        # get position x
        if self.sbml_network_editor.isSetGeometricShapeX(entity_id, graphical_object_index):
            rectangle_shape_info['x'] = {'abs': self.sbml_network_editor.getGeometricShapeX(entity_id, graphical_object_index),
                                        'rel': 0.0}

        # get position y
        if self.sbml_network_editor.isSetGeometricShapeY(entity_id, graphical_object_index):
            rectangle_shape_info['y'] = {'abs': self.sbml_network_editor.getGeometricShapeY(entity_id, graphical_object_index),
                                        'rel': 0.0}

        # get dimension width
        if self.sbml_network_editor.isSetGeometricShapeWidth(entity_id, graphical_object_index):
            rectangle_shape_info['width'] = {'abs': self.sbml_network_editor.getGeometricShapeWidth(entity_id, graphical_object_index),
                                            'rel': 0.0}

        # get dimension height
        if self.sbml_network_editor.isSetGeometricShapeHeight(entity_id, graphical_object_index):
            rectangle_shape_info['height'] = {'abs': self.sbml_network_editor.getGeometricShapeHeight(entity_id, graphical_object_index),
                                             'rel': 0.0}

        # get corner curvature radius rx
        if self.sbml_network_editor.isSetGeometricShapeBorderRadiusX(entity_id, graphical_object_index):
            rectangle_shape_info['rx'] = {'abs': self.sbml_network_editor.getGeometricShapeBorderRadiusX(entity_id, graphical_object_index),
                                          'rel': 0.0}

        # get corner curvature radius ry
        if self.sbml_network_editor.isSetGeometricShapeBorderRadiusY(entity_id, graphical_object_index):
            rectangle_shape_info['ry'] = {'abs': self.sbml_network_editor.getGeometricShapeBorderRadiusY(entity_id, graphical_object_index),
                                          'rel': 0.0}

        # get width/height ratio
        if self.sbml_network_editor.isSetGeometricShapeRatio(entity_id, graphical_object_index):
            rectangle_shape_info['ratio'] = self.sbml_network_editor.getGeometricShapeRatio(entity_id, graphical_object_index)

        return rectangle_shape_info

    def extract_line_ending_rectangle_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        rectangle_shape_info = {'shape': "rectangle"}

        # get fill color
        if self.sbml_network_editor.isSetLineEndingFillColor(line_ending_id):
            rectangle_shape_info['fillColor'] = self.sbml_network_editor.getLineEndingFillColor(line_ending_id)

        # get position x
        if self.sbml_network_editor.isSetLineEndingGeometricShapeX(line_ending_id):
            rectangle_shape_info['x'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeX(line_ending_id),
                                        'rel': 0.0}

        # get position y
        if self.sbml_network_editor.isSetLineEndingGeometricShapeY(line_ending_id):
            rectangle_shape_info['y'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeY(line_ending_id),
                                        'rel': 0.0}

        # get dimension width
        if self.sbml_network_editor.isSetLineEndingGeometricShapeWidth(line_ending_id):
            rectangle_shape_info['width'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeWidth(line_ending_id),
                                            'rel': 0.0}

        # get dimension height
        if self.sbml_network_editor.isSetLineEndingGeometricShapeHeight(line_ending_id):
            rectangle_shape_info['height'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeHeight(line_ending_id),
                                             'rel': 0.0}

        # get corner curvature radius rx
        if self.sbml_network_editor.isSetLineEndingGeometricShapeBorderRadiusX(line_ending_id):
            rectangle_shape_info['rx'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeBorderRadiusX(line_ending_id),
                                          'rel': 0.0}

        # get corner curvature radius ry
        if self.sbml_network_editor.isSetLineEndingGeometricShapeBorderRadiusY(line_ending_id):
            rectangle_shape_info['ry'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeBorderRadiusY(line_ending_id),
                                          'rel': 0.0}

        # get width/height ratio
        if self.sbml_network_editor.isSetLineEndingGeometricShapeRatio(line_ending_id):
            rectangle_shape_info['ratio'] = self.sbml_network_editor.getLineEndingGeometricShapeRatio(line_ending_id)

        return rectangle_shape_info

    def extract_ellipse_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        ellipse_shape_info = {'shape': "ellipse"}

        # get fill color
        if self.sbml_network_editor.isSetFillColor(entity_id, graphical_object_index):
            ellipse_shape_info['fillColor'] = self.sbml_network_editor.getFillColor(entity_id, graphical_object_index)

        # get position cx
        if self.sbml_network_editor.isSetGeometricShapeCenterX(entity_id, graphical_object_index):
            ellipse_shape_info['cx'] = {'abs': self.sbml_network_editor.getGeometricShapeCenterX(entity_id, graphical_object_index),
                                        'rel': 0.0}

        # get position cy
        if self.sbml_network_editor.isSetGeometricShapeCenterY(entity_id, graphical_object_index):
            ellipse_shape_info['cy'] = {'abs': self.sbml_network_editor.getGeometricShapeCenterY(entity_id, graphical_object_index),
                                        'rel': 0.0}

        # get dimension rx
        if self.sbml_network_editor.isSetGeometricShapeRadiusX(entity_id, graphical_object_index):
            ellipse_shape_info['rx'] = {'abs': self.sbml_network_editor.getGeometricShapeRadiusX(entity_id, graphical_object_index),
                                        'rel': 0.0}

        # get dimension ry
        if self.sbml_network_editor.isSetGeometricShapeRadiusY(entity_id, graphical_object_index):
            ellipse_shape_info['ry'] = {'abs': self.sbml_network_editor.getGeometricShapeRadiusY(entity_id, graphical_object_index),
                                        'rel': 0.0}

        # get radius ratio
        if self.sbml_network_editor.isSetGeometricShapeRatio(entity_id, graphical_object_index):
            ellipse_shape_info['ratio'] = self.sbml_network_editor.getGeometricShapeRatio(entity_id, graphical_object_index)

        return ellipse_shape_info

    def extract_line_ending_ellipse_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        ellipse_shape_info = {'shape': "ellipse"}

        # get fill color
        if self.sbml_network_editor.isSetLineEndingFillColor(line_ending_id):
            ellipse_shape_info['fillColor'] = self.sbml_network_editor.getLineEndingFillColor(line_ending_id)

        # get position cx
        if self.sbml_network_editor.isSetLineEndingGeometricShapeCenterX(line_ending_id):
            ellipse_shape_info['cx'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeCenterX(line_ending_id),
                                        'rel': 0.0}

        # get position cy
        if self.sbml_network_editor.isSetLineEndingGeometricShapeCenterY(line_ending_id):
            ellipse_shape_info['cy'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeCenterY(line_ending_id),
                                        'rel': 0.0}

        # get dimension rx
        if self.sbml_network_editor.isSetLineEndingGeometricShapeRadiusX(line_ending_id):
            ellipse_shape_info['rx'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeRadiusX(line_ending_id),
                                        'rel': 0.0}

        # get dimension ry
        if self.sbml_network_editor.isSetLineEndingGeometricShapeRadiusY(line_ending_id):
            ellipse_shape_info['ry'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeRadiusY(line_ending_id),
                                        'rel': 0.0}

        # get radius ratio
        if self.sbml_network_editor.isSetLineEndingGeometricShapeRatio(line_ending_id):
            ellipse_shape_info['ratio'] = self.sbml_network_editor.getLineEndingGeometricShapeRatio(line_ending_id)

        return ellipse_shape_info

    def extract_polygon_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        polygon_shape_info = {'shape': "polygon"}

        # get fill color
        if self.sbml_network_editor.isSetFillColor(entity_id, graphical_object_index):
            polygon_shape_info['fillColor'] = self.sbml_network_editor.getFillColor(entity_id, graphical_object_index)

        # get fill rule
        if self.sbml_network_editor.isSetFillRule(entity_id, graphical_object_index):
            polygon_shape_info['fillRule'] = self.sbml_network_editor.getFillRule(entity_id, graphical_object_index)

        vertices_ = []
        for v_index in range(self.sbml_network_editor.getGeometricShapeNumSegments(entity_id, graphical_object_index)):
            vertex_ = {}
            vertex_['renderPointX'] = {'abs': self.sbml_network_editor.getGeometricShapeSegmentX(entity_id, v_index, graphical_object_index),
                                       'rel': 0.0}
            vertex_['renderPointY'] = {'abs': self.sbml_network_editor.getGeometricShapeSegmentY(entity_id, v_index, graphical_object_index),
                                       'rel': 0.0}
            if self.sbml_network_editor.isGeometricShapeSegmentCubicBezier(entity_id, v_index, graphical_object_index):
                vertex_['basePoint1X'] = {'abs': self.sbml_network_editor.getGeometricShapeSegmentBasePoint1X(entity_id, v_index, graphical_object_index),
                                          'rel': 0.0}
                vertex_['basePoint1Y'] = {'abs': self.sbml_network_editor.getGeometricShapeSegmentBasePoint1Y(entity_id, v_index, graphical_object_index),
                                          'rel': 0.0}
                vertex_['basePoint2X'] = {'abs': self.sbml_network_editor.getGeometricShapeSegmentBasePoint2X(entity_id, v_index, graphical_object_index),
                                          'rel': 0.0}
                vertex_['basePoint2Y'] = {'abs': self.sbml_network_editor.getGeometricShapeSegmentBasePoint2Y(entity_id, v_index, graphical_object_index),
                                          'rel': 0.0}
            vertices_.append(vertex_)
        polygon_shape_info['vertices'] = vertices_
        return polygon_shape_info

    def extract_line_ending_polygon_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        polygon_shape_info = {'shape': "polygon"}

        # get fill color
        if self.sbml_network_editor.isSetLineEndingFillColor(line_ending_id):
            polygon_shape_info['fillColor'] = self.sbml_network_editor.getLineEndingFillColor(line_ending_id)

        # get fill rule
        if self.sbml_network_editor.isSetLineEndingFillRule(line_ending_id):
            polygon_shape_info['fillRule'] = self.sbml_network_editor.getLineEndingFillRule(line_ending_id)

        vertices_ = []
        for v_index in range(self.sbml_network_editor.getLineEndingGeometricShapeNumSegments(line_ending_id)):
            vertex_ = {}
            vertex_['renderPointX'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeSegmentX(line_ending_id, v_index),
                                       'rel': 0.0}
            vertex_['renderPointY'] = {'abs': self.sbml_network_editor.getLineEndingGeometricShapeSegmentY(line_ending_id, v_index),
                                       'rel': 0.0}
            if self.sbml_network_editor.isLineEndingGeometricShapeSegmentCubicBezier(line_ending_id, v_index):
                vertex_['basePoint1X'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentBasePoint1X(line_ending_id, v_index),
                                          'rel': 0.0}
                vertex_['basePoint1Y'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentBasePoint1Y(line_ending_id, v_index),
                                          'rel': 0.0}
                vertex_['basePoint2X'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentBasePoint2X(line_ending_id, v_index),
                                          'rel': 0.0}
                vertex_['basePoint2Y'] = {'abs': self.sbml_network_editor.getLineEndingCurveSegmentBasePoint2Y(line_ending_id, v_index),
                                          'rel': 0.0}
            vertices_.append(vertex_)
        polygon_shape_info['vertices'] = vertices_

        return polygon_shape_info