from .import_base import NetworkInfoImportBase
import libsbmlnetwork
import math


class NetworkInfoImportFromSBMLModel(NetworkInfoImportBase):
    def __init__(self, display_compartments_text_label=True,
                 display_species_text_label=True, display_reactions_text_label =False):
        super().__init__()
        self.sbml_network = None
        self.display_compartments_text_label = display_compartments_text_label
        self.display_species_text_label = display_species_text_label
        self.display_reactions_text_label = display_reactions_text_label
        self.empty_species_ids = []

    def extract_info(self, graph):
        super().extract_info(graph)
        if isinstance(graph, libsbmlnetwork.LibSBMLNetwork):
            self.sbml_network = graph
        else:
            self.sbml_network = libsbmlnetwork.LibSBMLNetwork(graph)
        self.extract_layout_info()
        self.extract_render_info()

    def extract_layout_info(self):
        if not self.sbml_network.getNumLayouts():
            self.sbml_network.createDefaultLayout()
        self.extract_layout_features()

    def extract_render_info(self):
        self.extract_global_render_info()
        self.extract_global_render_features()
        self.extract_local_render_info()
        self.extract_local_render_features()

    def extract_layout_features(self):
        for c_index in range(self.sbml_network.getNumCompartments()):
            self.add_compartment(self.sbml_network.getCompartmentId(c_index))

        for s_index in range(self.sbml_network.getNumSpecies()):
            self.add_species(self.sbml_network.getSpeciesId(s_index))

        for r_index in range(self.sbml_network.getNumReactions()):
            self.add_reaction(self.sbml_network.getReactionId(r_index))

        for a_go_index in range(self.sbml_network.getNumAllAdditionalGraphicalObjects()):
            self.add_additional_graphical_object(self.sbml_network.getAdditionalGraphicalObjectId(a_go_index))

    def extract_global_render_info(self):
        if not self.sbml_network.getNumGlobalRenderInformation() and\
            not self.sbml_network.getNumLocalRenderInformation():
            self.sbml_network.createDefaultGlobalRenderInformation()

    def extract_global_render_features(self):
        if self.sbml_network.isSetBackgroundColor():
            self.background_color = self.sbml_network.getBackgroundColor()

        # get colors info
        for c_index in range(self.sbml_network.getNumGlobalColors()):
            self.add_color(self.sbml_network.getGlobalColorId(c_index))

        # get gradients info
        for g_index in range(self.sbml_network.getNumGlobalGradients()):
            self.add_gradient(self.sbml_network.getGlobalGradientId(g_index))

        # get line ending info
        for le_index in range(self.sbml_network.getNumGlobalLineEndings()):
            self.add_line_ending(self.sbml_network.getGlobalLineEndingId(le_index))

    def extract_local_render_info(self):
        if self.sbml_network.getNumGlobalRenderInformation():
            self.sbml_network.createDefaultLocalRenderInformation()

    def extract_local_render_features(self):
        # get colors info
        for c_index in range(self.sbml_network.getNumLocalColors()):
            self.add_color(self.sbml_network.getLocalColorId(c_index))

        # get gradients info
        for g_index in range(self.sbml_network.getNumLocalGradients()):
            self.add_gradient(self.sbml_network.getLocalGradientId(g_index))

        # get line ending info
        for le_index in range(self.sbml_network.getNumLocalLineEndings()):
            self.add_line_ending(self.sbml_network.getLocalLineEndingId(le_index))

    def extract_extents(self, bounding_box_x, bounding_box_y, bounding_box_width, bounding_box_height):
        self.extents['minX'] = min(self.extents['minX'], bounding_box_x)
        self.extents['minY'] = min(self.extents['minY'], bounding_box_y)
        self.extents['maxX'] = self.extents['minX'] + self.sbml_network.getCanvasWidth()
        self.extents['maxY'] = self.extents['minY'] + self.sbml_network.getCanvasHeight()

    def add_compartment(self, compartment_id):
        for cg_index in range(self.sbml_network.getNumCompartmentGlyphs(compartment_id)):
            compartment = self.extract_go_object_features(compartment_id, cg_index)
            self.compartments.append(compartment)

    def add_species(self, species_id):
        for sg_index in range(self.sbml_network.getNumSpeciesGlyphs(species_id)):
            species = self.extract_go_object_features(species_id, sg_index)
            species['compartment'] = self.sbml_network.getGraphicalObjectCompartmentId(species_id)
            self.species.append(species)

    def add_empty_species(self, empty_species_id):
        self.empty_species_ids.append(empty_species_id)
        species = self.extract_go_object_features(empty_species_id, 0)
        self.species.append(species)

    def add_reaction(self, reaction_id):
        for rg_index in range(self.sbml_network.getNumReactionGlyphs(reaction_id)):
            reaction = self.extract_go_object_features(reaction_id, rg_index)
            reaction['compartment'] = self.sbml_network.getGraphicalObjectCompartmentId(reaction_id)
            reaction['speciesReferences'] = []
            for srg_index in range(self.sbml_network.getNumSpeciesReferences(reaction_id, rg_index)):
                species_reference = {'reaction': reaction_id}
                species_reference['reaction_glyph_index'] = rg_index
                species_reference['species'] = self.sbml_network.getSpeciesReferenceSpeciesId(reaction_id, rg_index, srg_index)
                species_reference['species_glyph_id'] = self.sbml_network.getSpeciesReferenceSpeciesGlyphId(reaction_id, rg_index, srg_index)
                species_reference['species_reference_glyph_index'] = srg_index
                species_reference['id'] = self.sbml_network.getSpeciesReferenceId(reaction_id, rg_index, srg_index)
                species_reference['referenceId'] = self.sbml_network.getSpeciesReferenceId(reaction_id, rg_index, srg_index)
                if self.sbml_network.isSetSpeciesReferenceRole(reaction_id, rg_index, srg_index):
                    species_reference['role'] = self.sbml_network.getSpeciesReferenceRole(reaction_id, rg_index, srg_index)
                if self.sbml_network.isSetSpeciesReferenceEmptySpeciesGlyph(reaction_id, rg_index, srg_index):
                    empty_species_id = self.sbml_network.getSpeciesReferenceEmptySpeciesGlyphId(reaction_id, rg_index, srg_index)
                    if empty_species_id == species_reference['species_glyph_id']:
                        self.add_empty_species(empty_species_id)
                reaction['speciesReferences'].append(species_reference)
            self.reactions.append(reaction)

    def add_additional_graphical_object(self, additional_graphical_object_id):
        graphical_object = self.extract_go_object_features(additional_graphical_object_id, 0)
        self.additional_graphical_objects.append(graphical_object)

    def add_color(self, color_id):
        self.colors.append({'id': color_id})

    def add_gradient(self, gradient_id):
        self.gradients.append({'id': gradient_id})

    def add_line_ending(self, line_ending_id):
        self.line_endings.append({'id': line_ending_id})

    def extract_go_object_features(self, entity_id, graphical_object_index):
        features = {'referenceId': entity_id, 'id': self.sbml_network.getId(entity_id, graphical_object_index),
                    'index': graphical_object_index}
        if self.sbml_network.isSetMetaId(entity_id, graphical_object_index):
            features['metaId'] = self.sbml_network.getMetaId(entity_id, graphical_object_index)

        return features

    def extract_compartment_features(self, compartment):
        if compartment['referenceId']:
            compartment['features'] = self.extract_go_general_features(compartment['referenceId'], compartment['index'])
            if self.display_compartments_text_label:
                compartment['texts'] = self.extract_go_text_features(compartment['referenceId'], compartment['index'])
            self.extract_extents(self.sbml_network.getX(compartment['referenceId'], compartment['index']),
                                 self.sbml_network.getY(compartment['referenceId'], compartment['index']),
                                 self.sbml_network.getWidth(compartment['referenceId'], compartment['index']),
                                 self.sbml_network.getHeight(compartment['referenceId'], compartment['index']))

    def extract_species_features(self, species):
        if species['referenceId']:
            species['features'] = self.extract_go_general_features(species['referenceId'], species['index'])
            if self.display_species_text_label and not species['referenceId'] in self.empty_species_ids:
                species['texts'] = self.extract_go_text_features(species['referenceId'], species['index'])
            self.extract_extents(self.sbml_network.getX(species['referenceId'], species['index']),
                                 self.sbml_network.getY(species['referenceId'], species['index']),
                                 self.sbml_network.getWidth(species['referenceId'], species['index']),
                                 self.sbml_network.getHeight(species['referenceId'], species['index']))

    def extract_reaction_features(self, reaction):
        if reaction['referenceId']:
            reaction['features'] = self.extract_go_general_features(reaction['referenceId'], reaction['index'])
            if self.display_reactions_text_label:
                reaction['texts'] = self.extract_go_text_features(reaction['referenceId'], reaction['index'])
            self.extract_extents(self.sbml_network.getX(reaction['referenceId'], reaction['index']),
                                 self.sbml_network.getY(reaction['referenceId'], reaction['index']),
                                 self.sbml_network.getWidth(reaction['referenceId'], reaction['index']),
                                 self.sbml_network.getHeight(reaction['referenceId'], reaction['index']))
            if self.sbml_network.isSetCurve(reaction['referenceId'], reaction['index']):
                curve = []
                for cs_index in range(self.sbml_network.getNumCurveSegments(reaction['referenceId'], reaction['index'])):
                    curve_segment = {'startX': self.sbml_network.getCurveSegmentStartPointX(reaction['referenceId'], reaction['index'], cs_index),
                                'startY': self.sbml_network.getCurveSegmentStartPointY(reaction['referenceId'], reaction['index'], cs_index),
                                'endX': self.sbml_network.getCurveSegmentEndPointX(reaction['referenceId'], reaction['index'], cs_index),
                                'endY': self.sbml_network.getCurveSegmentEndPointY(reaction['referenceId'], reaction['index'], cs_index)}
                    if self.sbml_network.isCurveSegmentCubicBezier(reaction['referenceId'], reaction['index'], cs_index):
                        curve_segment["basePoint1X"] = self.sbml_network.getCurveSegmentBasePoint1X(reaction['referenceId'], reaction['index'], cs_index)
                        curve_segment["basePoint1Y"] = self.sbml_network.getCurveSegmentBasePoint1Y(reaction['referenceId'], reaction['index'], cs_index)
                        curve_segment["basePoint2X"] = self.sbml_network.getCurveSegmentBasePoint2X(reaction['referenceId'], reaction['index'], cs_index)
                        curve_segment["basePoint2Y"] = self.sbml_network.getCurveSegmentBasePoint2Y(reaction['referenceId'], reaction['index'], cs_index)
                    curve.append(curve_segment)
                if curve:
                    reaction['features']['curve'] = curve
                    reaction['features']['graphicalCurve'] = self.extract_curve_features(reaction['referenceId'], reaction['index'])

    def extract_species_reference_features(self, species_reference):
        species_reference['features'] = {}
        if species_reference['reaction']:
            curve = []
            for cs_index in range(self.sbml_network.getNumSpeciesReferenceCurveSegments(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'])):
                curve_segment = {'startX': self.sbml_network.getSpeciesReferenceCurveSegmentStartPointX(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index),
                            'startY': self.sbml_network.getSpeciesReferenceCurveSegmentStartPointY(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index),
                            'endX': self.sbml_network.getSpeciesReferenceCurveSegmentEndPointX(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index),
                            'endY': self.sbml_network.getSpeciesReferenceCurveSegmentEndPointY(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)}
                if self.sbml_network.isSpeciesReferenceCurveSegmentCubicBezier(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index):
                    curve_segment["basePoint1X"] = self.sbml_network.getSpeciesReferenceCurveSegmentBasePoint1X(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)
                    curve_segment["basePoint1Y"] = self.sbml_network.getSpeciesReferenceCurveSegmentBasePoint1Y(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)
                    curve_segment["basePoint2X"] = self.sbml_network.getSpeciesReferenceCurveSegmentBasePoint2X(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)
                    curve_segment["basePoint2Y"] = self.sbml_network.getSpeciesReferenceCurveSegmentBasePoint2Y(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'], cs_index)

                if cs_index == 0:
                    species_reference['features']['startPoint'] = {'x': curve_segment['startX'],
                                                                   'y': curve_segment['startY']}
                    if 'basePoint1X' in list(curve_segment.keys()) and (
                            not curve_segment['startX'] == curve_segment['basePoint1X'] or not curve_segment[
                                                                                                   'startY'] ==
                                                                                               curve_segment[
                                                                                                   'basePoint1Y']):
                        species_reference['features']['startSlope'] = math.atan2(
                            curve_segment['startY'] - curve_segment['basePoint1Y'],
                            curve_segment['startX'] - curve_segment['basePoint1X'])
                    elif 'basePoint2X' in list(curve_segment.keys()) and (
                            not curve_segment['startX'] == curve_segment['basePoint2X'] or not curve_segment[
                                                                                                   'startY'] ==
                                                                                               curve_segment[
                                                                                                   'basePoint2Y']):
                        species_reference['features']['startSlope'] = math.atan2(
                            curve_segment['startY'] - curve_segment['basePoint2Y'],
                            curve_segment['startX'] - curve_segment['basePoint2X'])
                    else:
                        species_reference['features']['startSlope'] = math.atan2(
                            curve_segment['startY'] - curve_segment['endY'],
                            curve_segment['startX'] - curve_segment['endX'])
                if cs_index == self.sbml_network.getNumSpeciesReferenceCurveSegments(species_reference['reaction'],
                                                                                     species_reference[
                                                                                         'reaction_glyph_index'],
                                                                                     species_reference[
                                                                                         'species_reference_glyph_index']) - 1:
                    species_reference['features']['endPoint'] = {'x': curve_segment['endX'], 'y': curve_segment['endY']}
                    if 'basePoint2X' in list(curve_segment.keys()) and (
                            not curve_segment['endX'] == curve_segment['basePoint2X'] or not curve_segment['endY'] ==
                                                                                             curve_segment[
                                                                                                 'basePoint2Y']):
                        species_reference['features']['endSlope'] = math.atan2(
                            curve_segment['endY'] - curve_segment['basePoint2Y'],
                            curve_segment['endX'] - curve_segment['basePoint2X'])
                    elif 'basePoint1X' in list(curve_segment.keys()) and (
                            not curve_segment['endX'] == curve_segment['basePoint1X'] or not curve_segment['endY'] ==
                                                                                             curve_segment[
                                                                                                 'basePoint1Y']):
                        species_reference['features']['endSlope'] = math.atan2(
                            curve_segment['endY'] - curve_segment['basePoint1Y'],
                            curve_segment['endX'] - curve_segment['basePoint1X'])
                    else:
                        species_reference['features']['endSlope'] = math.atan2(
                            curve_segment['endY'] - curve_segment['startY'],
                            curve_segment['endX'] - curve_segment['startX'])
                curve.append(curve_segment)
            if curve:
                species_reference['features']['curve'] = curve
                species_reference['features']['graphicalCurve'] = self.extract_species_reference_curve_features(species_reference['reaction'], species_reference['reaction_glyph_index'], species_reference['species_reference_glyph_index'])

    def extract_additional_graphical_object_features(self, additional_graphical_object):
        if additional_graphical_object['referenceId']:
            additional_graphical_object['features'] = self.extract_go_general_features(additional_graphical_object['referenceId'], additional_graphical_object['index'])
            additional_graphical_object['texts'] = self.extract_go_text_features(additional_graphical_object['referenceId'], additional_graphical_object['index'])
            self.extract_extents(self.sbml_network.getX(additional_graphical_object['referenceId'], additional_graphical_object['index']),
                                 self.sbml_network.getY(additional_graphical_object['referenceId'], additional_graphical_object['index']),
                                 self.sbml_network.getWidth(additional_graphical_object['referenceId'], additional_graphical_object['index']),
                                 self.sbml_network.getHeight(additional_graphical_object['referenceId'], additional_graphical_object['index']))

    def extract_color_features(self, color):
        color['features'] = {}
        if self.sbml_network.isSetColorValue(color['id']):
            color['features']['value'] = self.sbml_network.getColorValue(color['id'])
        else:
            color['features']['value'] = "#ffffff"

    def extract_gradient_features(self, gradient):
        gradient['features'] = {}
        # get spread method
        if self.sbml_network.isSetSpreadMethod(gradient['id']):
            gradient['features']['spreadMethod'] = self.sbml_network.getSpreadMethod(gradient['id'])

        # get gradient stops
        stops_ = []
        for s_index in range(self.sbml_network.getNumGradientStops(gradient['id'])):
            stop_ = {}
            # get offset
            if self.sbml_network.isSetOffset(gradient['id'], s_index):
                stop_['offset'] = {'abs': 0, 'rel': self.sbml_network.getOffset(gradient['id'], s_index)}

            # get stop color
            if self.sbml_network.isSetStopColor(gradient['id'], s_index):
                stop_['color'] = self.sbml_network.getStopColor(gradient['id'], s_index)
            stops_.append(stop_)
        gradient['features']['stops'] = stops_

        # linear gradient
        if self.sbml_network.isLinearGradient(gradient['id']):
            gradient['features']['type'] = 'linear'
            # get start
            gradient['features']['start'] = \
                {'x': {'abs': 0.0,
                        'rel': self.sbml_network.getLinearGradientX1(gradient['id'])},
                 'y': {'abs': 0.0,
                        'rel': self.sbml_network.getLinearGradientY1(gradient['id'])}}
            # get end
            gradient['features']['end'] = \
                {'x': {'abs': 0.0,
                        'rel': self.sbml_network.getLinearGradientX2(gradient['id'])},
                 'y': {'abs': 0.0,
                        'rel': self.sbml_network.getLinearGradientY2(gradient['id'])}}
        # radial gradient
        elif self.sbml_network.isRadialGradient(gradient['id']):
            gradient['features']['type'] = 'radial'
            # get center
            gradient['features']['center'] = \
                {'x': {'abs': 0.0,
                        'rel': self.sbml_network.getRadialGradientCenterX(gradient['id'])},
                 'y': {'abs': 0.0,
                        'rel': self.sbml_network.getRadialGradientCenterY(gradient['id'])}}
            # get focal
            gradient['features']['focalPoint'] = \
                {'x': {'abs': 0.0,
                        'rel': self.sbml_network.getRadialGradientFocalX(gradient['id'])},
                 'y': {'abs': 0.0,
                        'rel': self.sbml_network.getRadialGradientFocalY(gradient['id'])}}
            # get radius
            gradient['features']['radius'] = \
                {'abs': self.sbml_network.getRadialGradientRadius(gradient['id']),
                 'rel': 0.0}

    def extract_line_ending_features(self, line_ending):
        line_ending['features'] = {}
        line_ending['features']['boundingBox'] = {'x': self.sbml_network.getLineEndingBoundingBoxX(line_ending['id']),
                                                  'y': self.sbml_network.getLineEndingBoundingBoxY(line_ending['id']),
                                                  'width': self.sbml_network.getLineEndingBoundingBoxWidth(line_ending['id']),
                                                  'height': self.sbml_network.getLineEndingBoundingBoxHeight(line_ending['id'])}
        line_ending['features']['graphicalShape'] = self.extract_line_ending_graphical_shape_features(line_ending['id'])

    def extract_go_text_features(self, entity_id, graphical_object_index):
        text_features = []
        for text_glyph_index in range(self.sbml_network.getNumTextGlyphs(entity_id, graphical_object_index)):
            features = {'features': {'plainText': self.sbml_network.getText(entity_id,
                                                                            graphical_object_index=graphical_object_index,
                                                                            text_glyph_index=text_glyph_index),
                                     'boundingBox': self.extract_text_bounding_box_features(entity_id,
                                                                                            graphical_object_index,
                                                                                            text_glyph_index),
                                     'graphicalText': self.extract_text_features(entity_id,
                                                                                 graphical_object_index, text_glyph_index)}}
            text_features.append(features)

        return text_features

    def extract_text_features(self, entity_id, graphical_object_index, text_glyph_index):
        features = {}
        # get stroke color
        if self.sbml_network.isSetFontColor(entity_id, graphical_object_index, text_glyph_index):
            features['strokeColor'] = self.sbml_network.getFontColor(entity_id, graphical_object_index, text_glyph_index)
        # get font family
        if self.sbml_network.isSetFontFamily(entity_id, graphical_object_index, text_glyph_index):
            features['fontFamily'] = self.sbml_network.getFontFamily(entity_id, graphical_object_index, text_glyph_index)
        # get font size
        if self.sbml_network.isSetFontSize(entity_id, graphical_object_index, text_glyph_index):
            features['fontSize'] = {'abs': self.sbml_network.getFontSize(entity_id, graphical_object_index, text_glyph_index),
                                     'rel': 0.0}
        # get font weight
        if self.sbml_network.isSetFontWeight(entity_id, graphical_object_index, text_glyph_index):
            features['fontWeight'] = self.sbml_network.getFontWeight(entity_id, graphical_object_index, text_glyph_index)
        # get font style
        if self.sbml_network.isSetFontStyle(entity_id, graphical_object_index, text_glyph_index):
            features['fontStyle'] = self.sbml_network.getFontStyle(entity_id, graphical_object_index, text_glyph_index)
        # get horizontal text anchor
        if self.sbml_network.isSetTextHorizontalAlignment(entity_id, graphical_object_index, text_glyph_index):
            features['hTextAnchor'] = self.sbml_network.getTextHorizontalAlignment(entity_id, graphical_object_index, text_glyph_index)
        # get vertical text anchor
        if self.sbml_network.isSetTextVerticalAlignment(entity_id, graphical_object_index, text_glyph_index):
            features['vTextAnchor'] = self.sbml_network.getTextVerticalAlignment(entity_id, graphical_object_index, text_glyph_index)

        return features

    def extract_go_general_features(self, entity_id, graphical_object_index):
        features = {'boundingBox': self.extract_bounding_box_features(entity_id, graphical_object_index),
                    'graphicalShape': self.extract_graphical_shape_features(entity_id, graphical_object_index)}

        return features

    def extract_bounding_box_features(self, entity_id, graphical_object_index):
        return {'x': self.sbml_network.getX(entity_id, graphical_object_index), 'y': self.sbml_network.getY(entity_id, graphical_object_index),
                'width': self.sbml_network.getWidth(entity_id, graphical_object_index), 'height': self.sbml_network.getHeight(entity_id, graphical_object_index)}

    def extract_text_bounding_box_features(self, entity_id, graphical_object_index, text_glyph_index):
        return {'x': self.sbml_network.getTextX(entity_id, graphical_object_index, text_glyph_index),
                'y': self.sbml_network.getTextY(entity_id, graphical_object_index, text_glyph_index),
                'width': self.sbml_network.getTextWidth(entity_id, graphical_object_index, text_glyph_index),
                'height': self.sbml_network.getTextHeight(entity_id, graphical_object_index, text_glyph_index)}

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
        if self.sbml_network.isSetBorderColor(entity_id, graphical_object_index):
            render_group_general_features['strokeColor'] = self.sbml_network.getBorderColor(entity_id, graphical_object_index)
        # get stroke width
        if self.sbml_network.isSetBorderWidth(entity_id, graphical_object_index):
            render_group_general_features['strokeWidth'] = self.sbml_network.getBorderWidth(entity_id, graphical_object_index)
        # get stroke dash array
        if self.sbml_network.getNumBorderDashes(entity_id, graphical_object_index):
            dash_array = []
            for d_index in range(self.sbml_network.getNumBorderDashes(entity_id, graphical_object_index)):
                dash_array.append(self.sbml_network.getBorderDash(entity_id, graphical_object_index, d_index))
            render_group_general_features['strokeDashArray'] = tuple(dash_array)
        # get fill color
        if self.sbml_network.isSetFillColor(entity_id, graphical_object_index):
            render_group_general_features['fillColor'] = self.sbml_network.getFillColor(entity_id, graphical_object_index)
        # get fill rule
        if self.sbml_network.isSetFillRule(entity_id, graphical_object_index):
            render_group_general_features['fillRule'] = self.sbml_network.getFillRule(entity_id, graphical_object_index)

        return render_group_general_features

    def extract_line_ending_render_group_general_features(self, line_ending_id):
        line_ending_render_group_general_features = {}
        # get stroke color
        if self.sbml_network.isSetLineEndingBorderColor(line_ending_id):
            line_ending_render_group_general_features['strokeColor'] = self.sbml_network.getLineEndingBorderColor(line_ending_id)
        # get stroke width
        if self.sbml_network.isSetLineEndingBorderWidth(line_ending_id):
            line_ending_render_group_general_features['strokeWidth'] = self.sbml_network.getLineEndingBorderWidth(line_ending_id)
        # get stroke dash array
        if self.sbml_network.getNumLineEndingBorderDashes(line_ending_id):
            dash_array = []
            for d_index in range(self.sbml_network.getNumLineEndingBorderDashes(line_ending_id)):
                dash_array.append(self.sbml_network.getLineEndingBorderDash(line_ending_id, d_index))
            line_ending_render_group_general_features['strokeDashArray'] = tuple(dash_array)
        # get fill color
        if self.sbml_network.isSetLineEndingFillColor(line_ending_id):
            line_ending_render_group_general_features['fillColor'] = self.sbml_network.getLineEndingFillColor(line_ending_id)
        # get fill rule
        if self.sbml_network.isSetLineEndingFillRule(line_ending_id):
            line_ending_render_group_general_features['fillRule'] = self.sbml_network.getLineEndingFillRule(line_ending_id)

        return line_ending_render_group_general_features

    def extract_render_group_geometric_shapes(self, entity_id, graphical_object_index):
        geometric_shapes = []
        for gs_index in range(self.sbml_network.getNumGeometricShapes(entity_id, graphical_object_index)):
            geometric_shape = {}
            geometric_shape.update(self.extract_geometric_shape_general_features(entity_id, graphical_object_index, gs_index))
            geometric_shape.update(self.extract_geometric_shape_exclusive_features(entity_id, graphical_object_index, gs_index))
            geometric_shapes.append(geometric_shape)

        return geometric_shapes

    def extract_line_ending_render_group_geometric_shapes(self, line_ending_id):
        geometric_shapes = []
        for gs_index in range(self.sbml_network.getNumLineEndingGeometricShapes(line_ending_id)):
            geometric_shape = {}
            geometric_shape.update(self.extract_line_ending_geometric_shape_general_features(line_ending_id, gs_index))
            geometric_shape.update(self.extract_line_ending_geometric_shape_exclusive_features(line_ending_id, gs_index))
            geometric_shapes.append(geometric_shape)

        return geometric_shapes

    def extract_geometric_shape_general_features(self, entity_id, graphical_object_index, geometric_shape_index):
        geometric_shape_general_features = {}
        # get stroke color
        if self.sbml_network.isSetGeometricShapeBorderColor(entity_id, geometric_shape_index, graphical_object_index):
            geometric_shape_general_features['strokeColor'] = self.sbml_network.getGeometricShapeBorderColor(entity_id,
                                                                                                             geometric_shape_index,
                                                                                                             graphical_object_index)

        # get stroke width
        if self.sbml_network.isSetGeometricShapeBorderWidth(entity_id, geometric_shape_index, graphical_object_index):
            geometric_shape_general_features['strokeWidth'] = self.sbml_network.getGeometricShapeBorderWidth(entity_id,
                                                                                                             geometric_shape_index,
                                                                                                             graphical_object_index)

        # get stroke dash array
        if self.sbml_network.getNumBorderDashes(entity_id, graphical_object_index):
            dash_array = []
            for d_index in range(self.sbml_network.getNumBorderDashes(entity_id, graphical_object_index)):
                dash_array.append(self.sbml_network.getBorderDash(entity_id, graphical_object_index, d_index))
            geometric_shape_general_features['strokeDashArray'] = tuple(dash_array)

        return geometric_shape_general_features

    def extract_line_ending_geometric_shape_general_features(self, line_ending_id, geometric_shape_index):
        geometric_shape_general_features = {}
        # get stroke color
        if self.sbml_network.isSetLineEndingBorderColor(line_ending_id):
            geometric_shape_general_features['strokeColor'] = self.sbml_network.getLineEndingBorderColor(line_ending_id)

        # get stroke width
        if self.sbml_network.isSetLineEndingBorderWidth(line_ending_id):
            geometric_shape_general_features['strokeWidth'] = self.sbml_network.getLineEndingBorderWidth(line_ending_id)

        # get stroke dash array
        if self.sbml_network.getNumLineEndingBorderDashes(line_ending_id):
            dash_array = []
            for d_index in range(self.sbml_network.getNumLineEndingBorderDashes(line_ending_id)):
                dash_array.append(self.sbml_network.getLineEndingBorderDash(line_ending_id, d_index))
            geometric_shape_general_features['strokeDashArray'] = tuple(dash_array)

        return geometric_shape_general_features

    def extract_geometric_shape_exclusive_features(self, entity_id, graphical_object_index, geometric_shape_index):
        if self.sbml_network.isImage(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_image_shape_features(entity_id, graphical_object_index, geometric_shape_index)
        elif self.sbml_network.isRenderCurve(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_curve_shape_features(entity_id, graphical_object_index, geometric_shape_index)
        elif self.sbml_network.isText(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_text_shape_features(entity_id, graphical_object_index, geometric_shape_index)
        elif self.sbml_network.isRectangle(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_rectangle_shape_features(entity_id, graphical_object_index, geometric_shape_index)
        elif self.sbml_network.isEllipse(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_ellipse_shape_features(entity_id, graphical_object_index, geometric_shape_index)
        elif self.sbml_network.isPolygon(entity_id, geometric_shape_index, graphical_object_index):
            return self.extract_polygon_shape_features(entity_id, graphical_object_index, geometric_shape_index)

        return {'shape': "None"}

    def extract_line_ending_geometric_shape_exclusive_features(self, line_ending_id, geometric_shape_index):
        if self.sbml_network.isLineEndingImage(line_ending_id):
            return self.extract_line_ending_image_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network.isLineEndingRenderCurve(line_ending_id, geometric_shape_index):
            return self.extract_line_ending_curve_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network.isLineEndingText(line_ending_id, geometric_shape_index):
            return self.extract_line_ending_text_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network.isLineEndingRectangle(line_ending_id, geometric_shape_index):
            return self.extract_line_ending_rectangle_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network.isLineEndingEllipse(line_ending_id, geometric_shape_index):
            return self.extract_line_ending_ellipse_shape_features(line_ending_id, geometric_shape_index)
        elif self.sbml_network.isLineEndingPolygon(line_ending_id, geometric_shape_index):
            return self.extract_line_ending_polygon_shape_features(line_ending_id, geometric_shape_index)

    def extract_curve_features(self, entity_id, graphical_object_index):
        curve_features = {}
        # get stroke color
        if self.sbml_network.isSetLineColor(entity_id, graphical_object_index):
            curve_features['strokeColor'] = self.sbml_network.getLineColor(entity_id, graphical_object_index)

        # get stroke width
        if self.sbml_network.isSetLineWidth(entity_id, graphical_object_index):
            curve_features['strokeWidth'] = self.sbml_network.getLineWidth(entity_id, graphical_object_index)

        # get stroke dash array
        if self.sbml_network.getNumLineDashes(entity_id, graphical_object_index):
            dash_array = []
            for d_index in range(self.sbml_network.getNumLineDashes(entity_id, graphical_object_index)):
                dash_array.append(self.sbml_network.getLineDash(entity_id, graphical_object_index, d_index))
            curve_features['strokeDashArray'] = tuple(dash_array)

        # get heads
        curve_features['heads'] = {}
        if self.sbml_network.isSetStartHead(entity_id, graphical_object_index):
            curve_features['heads']['start'] = self.sbml_network.getStartHead(entity_id, graphical_object_index)
        elif self.sbml_network.isSetEndHead(entity_id, graphical_object_index):
            curve_features['heads']['end'] = self.sbml_network.getEndHead(entity_id, graphical_object_index)

        return curve_features

    def extract_species_reference_curve_features(self, reaction_id, reaction_glyph_index, species_reference_glyph_index):
        curve_features = {}
        # get stroke color
        if self.sbml_network.isSetSpeciesReferenceLineColor(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            curve_features['strokeColor'] = self.sbml_network.getSpeciesReferenceLineColor(reaction_id, reaction_glyph_index, species_reference_glyph_index)

        # get stroke width
        if self.sbml_network.isSetSpeciesReferenceLineWidth(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            curve_features['strokeWidth'] = self.sbml_network.getSpeciesReferenceLineWidth(reaction_id, reaction_glyph_index, species_reference_glyph_index)

        # get stroke dash array
        if self.sbml_network.getNumSpeciesReferenceLineDashes(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            dash_array = []
            for d_index in range(self.sbml_network.getNumSpeciesReferenceLineDashes(reaction_id, reaction_glyph_index, species_reference_glyph_index)):
                dash_array.append(self.sbml_network.getSpeciesReferenceLineDash(reaction_id, reaction_glyph_index, species_reference_glyph_index, d_index))
            curve_features['strokeDashArray'] = tuple(dash_array)

        # get heads
        curve_features['heads'] = {}
        if self.sbml_network.isSetSpeciesReferenceStartHead(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            curve_features['heads']['start'] = self.sbml_network.getSpeciesReferenceStartHead(reaction_id, reaction_glyph_index, species_reference_glyph_index)
        elif self.sbml_network.isSetSpeciesReferenceEndHead(reaction_id, reaction_glyph_index, species_reference_glyph_index):
            curve_features['heads']['end'] = self.sbml_network.getSpeciesReferenceEndHead(reaction_id, reaction_glyph_index, species_reference_glyph_index)

        return curve_features

    def extract_image_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        image_shape_info = {'shape': "image"}

        # get position x
        if self.sbml_network.isSetGeometricShapeX(entity_id, graphical_object_index):
            image_shape_info['x'] = {'abs': self.sbml_network.getGeometricShapeX(entity_id, graphical_object_index),
                                     'rel': 0.0}

        # get position y
        if self.sbml_network.isSetGeometricShapeY(entity_id, graphical_object_index):
            image_shape_info['y'] = {'abs': self.sbml_network.getGeometricShapeY(entity_id, graphical_object_index),
                                     'rel': 0.0}

        # get dimension width
        if self.sbml_network.isSetGeometricShapeWidth(entity_id, graphical_object_index):
            image_shape_info['width'] = {'abs': self.sbml_network.getGeometricShapeWidth(entity_id, graphical_object_index),
                                        'rel': 0.0}

        # get dimension height
        if self.sbml_network.isSetGeometricShapeHeight(entity_id, graphical_object_index):
            image_shape_info['height'] = {'abs': self.sbml_network.getGeometricShapeHeight(entity_id, graphical_object_index),
                                         'rel': 0.0}

        # get href
        if self.sbml_network.isSetGeometricShapeHref(entity_id, graphical_object_index):
            image_shape_info['href'] = self.sbml_network.getGeometricShapeHref(entity_id, graphical_object_index)

        return image_shape_info

    def extract_line_ending_image_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        image_shape_info = {'shape': "image"}

        # get position x
        if self.sbml_network.isSetLineEndingGeometricShapeX(line_ending_id):
            image_shape_info['x'] = {'abs': self.sbml_network.getLineEndingGeometricShapeX(line_ending_id),
                                     'rel': 0.0}

        # get position y
        if self.sbml_network.isSetLineEndingGeometricShapeY(line_ending_id):
            image_shape_info['y'] = {'abs': self.sbml_network.getLineEndingGeometricShapeY(line_ending_id),
                                     'rel': 0.0}

        # get dimension width
        if self.sbml_network.isSetLineEndingGeometricShapeWidth(line_ending_id):
            image_shape_info['width'] = {'abs': self.sbml_network.getLineEndingGeometricShapeWidth(line_ending_id),
                                        'rel': 0.0}

        # get dimension height
        if self.sbml_network.isSetLineEndingGeometricShapeHeight(line_ending_id):
            image_shape_info['height'] = {'abs': self.sbml_network.getLineEndingGeometricShapeHeight(line_ending_id),
                                         'rel': 0.0}

        # get href
        if self.sbml_network.isSetLineEndingGeometricShapeHref(line_ending_id):
            image_shape_info['href'] = self.sbml_network.getLineEndingGeometricShapeHref(line_ending_id)

        return image_shape_info

    def extract_curve_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        curve_shape_info = {'shape': "renderCurve"}
        vertices_ = []
        for v_index in range(self.sbml_network.getGeometricShapeNumSegments(entity_id, geometric_shape_index, graphical_object_index)):
            vertex_ = {}
            vertex_['renderPointX'] = {'abs': self.sbml_network.getGeometricShapeSegmentX(entity_id, v_index, geometric_shape_index, graphical_object_index),
                                       'rel': 0.0}
            vertex_['renderPointY'] = {'abs': self.sbml_network.getGeometricShapeSegmentY(entity_id, v_index, geometric_shape_index, graphical_object_index),
                                       'rel': 0.0}
            if self.sbml_network.isGeometricShapeSegmentCubicBezier(entity_id, v_index, geometric_shape_index, graphical_object_index):
                vertex_['basePoint1X'] = {'abs': self.sbml_network.getGeometricShapeSegmentBasePoint1X(entity_id, v_index, geometric_shape_index, graphical_object_index),
                                          'rel': 0.0}
                vertex_['basePoint1Y'] = {'abs': self.sbml_network.getGeometricShapeSegmentBasePoint1Y(entity_id, v_index, geometric_shape_index, graphical_object_index),
                                          'rel': 0.0}
                vertex_['basePoint2X'] = {'abs': self.sbml_network.getGeometricShapeSegmentBasePoint2X(entity_id, v_index, geometric_shape_index, graphical_object_index),
                                          'rel': 0.0}
                vertex_['basePoint2Y'] = {'abs': self.sbml_network.getGeometricShapeSegmentBasePoint2Y(entity_id, v_index, geometric_shape_index, graphical_object_index),
                                          'rel': 0.0}
            vertices_.append(vertex_)
        curve_shape_info['vertices'] = vertices_

        return curve_shape_info

    def extract_line_ending_curve_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        curve_shape_info = {'shape': "renderCurve"}

        vertices_ = []
        for v_index in range(
                self.sbml_network.getLineEndingGeometricShapeNumSegments(line_ending_id, index=geometric_shape_index)):
            vertex_ = {}
            vertex_['renderPointX'] = {
                'abs': self.sbml_network.getLineEndingGeometricShapeSegmentX(line_ending_id, segment_index=v_index,
                                                                             index=geometric_shape_index),
                'rel': 0.0}
            vertex_['renderPointY'] = {
                'abs': self.sbml_network.getLineEndingGeometricShapeSegmentY(line_ending_id, segment_index=v_index,
                                                                             index=geometric_shape_index),
                'rel': 0.0}
            if self.sbml_network.isLineEndingGeometricShapeSegmentCubicBezier(line_ending_id, segment_index=v_index,
                                                                              index=geometric_shape_index):
                vertex_['basePoint1X'] = {
                    'abs': self.sbml_network.getLineEndingGeometricShapeSegmentBasePoint1X(line_ending_id,
                                                                                           segment_index=v_index,
                                                                                           index=geometric_shape_index),
                    'rel': 0.0}
                vertex_['basePoint1Y'] = {
                    'abs': self.sbml_network.getLineEndingGeometricShapeSegmentBasePoint1Y(line_ending_id,
                                                                                           segment_index=v_index,
                                                                                           index=geometric_shape_index),
                    'rel': 0.0}
                vertex_['basePoint2X'] = {
                    'abs': self.sbml_network.getLineEndingGeometricShapeSegmentBasePoint2X(line_ending_id,
                                                                                           segment_index=v_index,
                                                                                           index=geometric_shape_index),
                    'rel': 0.0}
                vertex_['basePoint2Y'] = {
                    'abs': self.sbml_network.getLineEndingGeometricShapeSegmentBasePoint2Y(line_ending_id,
                                                                                           segment_index=v_index,
                                                                                           index=geometric_shape_index),
                    'rel': 0.0}
            vertices_.append(vertex_)
        curve_shape_info['vertices'] = vertices_

        return curve_shape_info

    def extract_text_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        text_shape_info = {'shape': "text"}

        # get position x
        if self.sbml_network.isSetGeometricShapeX(entity_id, graphical_object_index):
            text_shape_info['x'] = {'abs': self.sbml_network.getGeometricShapeX(entity_id, graphical_object_index),
                                    'rel': 0.0}

        # get position y
        if self.sbml_network.isSetGeometricShapeY(entity_id, graphical_object_index):
            text_shape_info['y'] = {'abs': self.sbml_network.getGeometricShapeY(entity_id, graphical_object_index),
                                    'rel': 0.0}

        # get font family
        if self.sbml_network.isSetFontFamily(entity_id, graphical_object_index):
            text_shape_info['fontFamily'] = self.sbml_network.getFontFamily(entity_id, graphical_object_index)

        # get font size
        if self.sbml_network.isSetFontSize(entity_id, graphical_object_index):
            text_shape_info['fontSize'] = {'abs': self.sbml_network.getFontSize(entity_id, graphical_object_index),
                                          'rel': 0.0}

        # get font weight
        if self.sbml_network.isSetFontWeight(entity_id, graphical_object_index):
            text_shape_info['fontWeight'] = self.sbml_network.getFontWeight(entity_id, graphical_object_index)

        # get font style
        if self.sbml_network.isSetFontStyle(entity_id, graphical_object_index):
            text_shape_info['fontStyle'] = self.sbml_network.getFontStyle(entity_id, graphical_object_index)

        # get horizontal text anchor
        if self.sbml_network.isSetTextHorizontalAlignment(entity_id, graphical_object_index):
            text_shape_info['hTextAnchor'] = self.sbml_network.getTextHorizontalAlignment(entity_id, graphical_object_index)

        # get vertical text anchor
        if self.sbml_network.isSetTextVerticalAlignment(entity_id, graphical_object_index):
            text_shape_info['vTextAnchor'] = self.sbml_network.getTextVerticalAlignment(entity_id, graphical_object_index)

        return text_shape_info

    def extract_line_ending_text_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        text_shape_info = {'shape': "text"}

        # get position x
        if self.sbml_network.isSetLineEndingGeometricShapeX(line_ending_id):
            text_shape_info['x'] = {'abs': self.sbml_network.getLineEndingGeometricShapeX(line_ending_id),
                                    'rel': 0.0}

        # get position y
        if self.sbml_network.isSetLineEndingGeometricShapeY(line_ending_id):
            text_shape_info['y'] = {'abs': self.sbml_network.getLineEndingGeometricShapeY(line_ending_id),
                                    'rel': 0.0}

        # get font family
        if self.sbml_network.isSetLineEndingFontFamily(line_ending_id):
            text_shape_info['fontFamily'] = self.sbml_network.getLineEndingFontFamily(line_ending_id)

        # get font size
        if self.sbml_network.isSetLineEndingFontSize(line_ending_id):
            text_shape_info['fontSize'] = {'abs': self.sbml_network.getLineEndingFontSize(line_ending_id),
                                          'rel': 0.0}

        # get font weight
        if self.sbml_network.isSetLineEndingFontWeight(line_ending_id):
            text_shape_info['fontWeight'] = self.sbml_network.getLineEndingFontWeight(line_ending_id)

        # get font style
        if self.sbml_network.isSetLineEndingFontStyle(line_ending_id):
            text_shape_info['fontStyle'] = self.sbml_network.getLineEndingFontStyle(line_ending_id)

        # get horizontal text anchor
        if self.sbml_network.isSetLineEndingHorizontalAlignment(line_ending_id):
            text_shape_info['hTextAnchor'] = self.sbml_network.getLineEndingHorizontalAlignment(line_ending_id)

        # get vertical text anchor
        if self.sbml_network.isSetLineEndingVerticalAlignment(line_ending_id):
            text_shape_info['vTextAnchor'] = self.sbml_network.getLineEndingVerticalAlignment(line_ending_id)

        return text_shape_info

    def extract_rectangle_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        rectangle_shape_info = {'shape': "rectangle"}

        # get fill color
        if self.sbml_network.isSetGeometricShapeFillColor(entity_id, graphical_object_index=graphical_object_index):
            rectangle_shape_info['fillColor'] = self.sbml_network.getGeometricShapeFillColor(entity_id, graphical_object_index=graphical_object_index)

        # get position x
        if self.sbml_network.isSetGeometricShapeX(entity_id, graphical_object_index=graphical_object_index):
            rectangle_shape_info['x'] = {'abs': self.sbml_network.getGeometricShapeX(entity_id, graphical_object_index=graphical_object_index),
                                        'rel': 0.0}

        # get position y
        if self.sbml_network.isSetGeometricShapeY(entity_id, graphical_object_index=graphical_object_index):
            rectangle_shape_info['y'] = {'abs': self.sbml_network.getGeometricShapeY(entity_id, graphical_object_index=graphical_object_index),
                                        'rel': 0.0}

        # get dimension width
        if self.sbml_network.isSetGeometricShapeWidth(entity_id, graphical_object_index=graphical_object_index):
            rectangle_shape_info['width'] = {'abs': self.sbml_network.getGeometricShapeWidth(entity_id, graphical_object_index=graphical_object_index),
                                            'rel': 0.0}

        # get dimension height
        if self.sbml_network.isSetGeometricShapeHeight(entity_id, graphical_object_index=graphical_object_index):
            rectangle_shape_info['height'] = {'abs': self.sbml_network.getGeometricShapeHeight(entity_id, graphical_object_index=graphical_object_index),
                                             'rel': 0.0}

        # get corner curvature radius rx
        if self.sbml_network.isSetGeometricShapeBorderRadiusX(entity_id, graphical_object_index=graphical_object_index):
            rectangle_shape_info['rx'] = {'abs': self.sbml_network.getGeometricShapeBorderRadiusX(entity_id, graphical_object_index=graphical_object_index),
                                          'rel': 0.0}

        # get corner curvature radius ry
        if self.sbml_network.isSetGeometricShapeBorderRadiusY(entity_id, graphical_object_index=graphical_object_index):
            rectangle_shape_info['ry'] = {'abs': self.sbml_network.getGeometricShapeBorderRadiusY(entity_id, graphical_object_index=graphical_object_index),
                                          'rel': 0.0}

        # get width/height ratio
        if self.sbml_network.isSetGeometricShapeRatio(entity_id, graphical_object_index=graphical_object_index):
            rectangle_shape_info['ratio'] = self.sbml_network.getGeometricShapeRatio(entity_id, graphical_object_index=graphical_object_index)

        return rectangle_shape_info

    def extract_line_ending_rectangle_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        rectangle_shape_info = {'shape': "rectangle"}

        # get fill color
        if self.sbml_network.isSetLineEndingFillColor(line_ending_id):
            rectangle_shape_info['fillColor'] = self.sbml_network.getLineEndingFillColor(line_ending_id)

        # get position x
        if self.sbml_network.isSetLineEndingGeometricShapeX(line_ending_id):
            rectangle_shape_info['x'] = {'abs': self.sbml_network.getLineEndingGeometricShapeX(line_ending_id),
                                        'rel': 0.0}

        # get position y
        if self.sbml_network.isSetLineEndingGeometricShapeY(line_ending_id):
            rectangle_shape_info['y'] = {'abs': self.sbml_network.getLineEndingGeometricShapeY(line_ending_id),
                                        'rel': 0.0}

        # get dimension width
        if self.sbml_network.isSetLineEndingGeometricShapeWidth(line_ending_id):
            rectangle_shape_info['width'] = {'abs': self.sbml_network.getLineEndingGeometricShapeWidth(line_ending_id),
                                            'rel': 0.0}

        # get dimension height
        if self.sbml_network.isSetLineEndingGeometricShapeHeight(line_ending_id):
            rectangle_shape_info['height'] = {'abs': self.sbml_network.getLineEndingGeometricShapeHeight(line_ending_id),
                                             'rel': 0.0}

        # get corner curvature radius rx
        if self.sbml_network.isSetLineEndingGeometricShapeBorderRadiusX(line_ending_id):
            rectangle_shape_info['rx'] = {'abs': self.sbml_network.getLineEndingGeometricShapeBorderRadiusX(line_ending_id),
                                          'rel': 0.0}

        # get corner curvature radius ry
        if self.sbml_network.isSetLineEndingGeometricShapeBorderRadiusY(line_ending_id):
            rectangle_shape_info['ry'] = {'abs': self.sbml_network.getLineEndingGeometricShapeBorderRadiusY(line_ending_id),
                                          'rel': 0.0}

        # get width/height ratio
        if self.sbml_network.isSetLineEndingGeometricShapeRatio(line_ending_id):
            rectangle_shape_info['ratio'] = self.sbml_network.getLineEndingGeometricShapeRatio(line_ending_id)

        return rectangle_shape_info

    def extract_ellipse_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        ellipse_shape_info = {'shape': "ellipse"}

        # get fill color
        if self.sbml_network.isSetGeometricShapeFillColor(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index):
            ellipse_shape_info['fillColor'] = self.sbml_network.getGeometricShapeFillColor(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index)

        # get position cx
        if self.sbml_network.isSetGeometricShapeCenterX(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index):
            ellipse_shape_info['cx'] = {'abs': self.sbml_network.getGeometricShapeCenterX(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index),
                                        'rel': 0.0}

        # get position cy
        if self.sbml_network.isSetGeometricShapeCenterY(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index):
            ellipse_shape_info['cy'] = {'abs': self.sbml_network.getGeometricShapeCenterY(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index),
                                        'rel': 0.0}

        # get dimension rx
        if self.sbml_network.isSetGeometricShapeRadiusX(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index):
            ellipse_shape_info['rx'] = {'abs': self.sbml_network.getGeometricShapeRadiusX(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index),
                                        'rel': 0.0}

        # get dimension ry
        if self.sbml_network.isSetGeometricShapeRadiusY(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index):
            ellipse_shape_info['ry'] = {'abs': self.sbml_network.getGeometricShapeRadiusY(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index),
                                        'rel': 0.0}

        # get radius ratio
        if self.sbml_network.isSetGeometricShapeRatio(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index):
            ellipse_shape_info['ratio'] = self.sbml_network.getGeometricShapeRatio(id=entity_id, geometric_shape_index=geometric_shape_index, graphical_object_index=graphical_object_index)

        return ellipse_shape_info

    def extract_line_ending_ellipse_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        ellipse_shape_info = {'shape': "ellipse"}

        # get fill color
        if self.sbml_network.isSetLineEndingFillColor(line_ending_id):
            ellipse_shape_info['fillColor'] = self.sbml_network.getLineEndingFillColor(line_ending_id)

        # get position cx
        if self.sbml_network.isSetLineEndingGeometricShapeCenterX(line_ending_id):
            ellipse_shape_info['cx'] = {'abs': self.sbml_network.getLineEndingGeometricShapeCenterX(line_ending_id),
                                        'rel': 0.0}

        # get position cy
        if self.sbml_network.isSetLineEndingGeometricShapeCenterY(line_ending_id):
            ellipse_shape_info['cy'] = {'abs': self.sbml_network.getLineEndingGeometricShapeCenterY(line_ending_id),
                                        'rel': 0.0}

        # get dimension rx
        if self.sbml_network.isSetLineEndingGeometricShapeRadiusX(line_ending_id):
            ellipse_shape_info['rx'] = {'abs': self.sbml_network.getLineEndingGeometricShapeRadiusX(line_ending_id),
                                        'rel': 0.0}

        # get dimension ry
        if self.sbml_network.isSetLineEndingGeometricShapeRadiusY(line_ending_id):
            ellipse_shape_info['ry'] = {'abs': self.sbml_network.getLineEndingGeometricShapeRadiusY(line_ending_id),
                                        'rel': 0.0}

        # get radius ratio
        if self.sbml_network.isSetLineEndingGeometricShapeRatio(line_ending_id):
            ellipse_shape_info['ratio'] = self.sbml_network.getLineEndingGeometricShapeRatio(line_ending_id)

        return ellipse_shape_info

    def extract_polygon_shape_features(self, entity_id, graphical_object_index, geometric_shape_index):
        # set shape
        polygon_shape_info = {'shape': "polygon"}

        # get fill color
        if self.sbml_network.isSetGeometricShapeFillColor(entity_id, graphical_object_index=graphical_object_index):
            polygon_shape_info['fillColor'] = self.sbml_network.getGeometricShapeFillColor(entity_id, graphical_object_index=graphical_object_index)

        # get fill rule
        if self.sbml_network.isSetFillRule(entity_id, graphical_object_index=graphical_object_index):
            polygon_shape_info['fillRule'] = self.sbml_network.getFillRule(entity_id, graphical_object_index=graphical_object_index)

        vertices_ = []
        for v_index in range(self.sbml_network.getGeometricShapeNumSegments(entity_id, graphical_object_index=graphical_object_index)):
            vertex_ = {}
            vertex_['renderPointX'] = {'abs': self.sbml_network.getGeometricShapeSegmentX(entity_id, v_index, graphical_object_index=graphical_object_index),
                                       'rel': 0.0}
            vertex_['renderPointY'] = {'abs': self.sbml_network.getGeometricShapeSegmentY(entity_id, v_index, graphical_object_index=graphical_object_index),
                                       'rel': 0.0}
            if self.sbml_network.isGeometricShapeSegmentCubicBezier(entity_id, v_index, graphical_object_index=graphical_object_index):
                vertex_['basePoint1X'] = {'abs': self.sbml_network.getGeometricShapeSegmentBasePoint1X(entity_id, v_index, graphical_object_index=graphical_object_index),
                                          'rel': 0.0}
                vertex_['basePoint1Y'] = {'abs': self.sbml_network.getGeometricShapeSegmentBasePoint1Y(entity_id, v_index, graphical_object_index=graphical_object_index),
                                          'rel': 0.0}
                vertex_['basePoint2X'] = {'abs': self.sbml_network.getGeometricShapeSegmentBasePoint2X(entity_id, v_index, graphical_object_index=graphical_object_index),
                                          'rel': 0.0}
                vertex_['basePoint2Y'] = {'abs': self.sbml_network.getGeometricShapeSegmentBasePoint2Y(entity_id, v_index, graphical_object_index=graphical_object_index),
                                          'rel': 0.0}
            vertices_.append(vertex_)
        polygon_shape_info['vertices'] = vertices_
        return polygon_shape_info

    def extract_line_ending_polygon_shape_features(self, line_ending_id, geometric_shape_index):
        # set shape
        polygon_shape_info = {'shape': "polygon"}

        # get fill color
        if self.sbml_network.isSetLineEndingFillColor(line_ending_id):
            polygon_shape_info['fillColor'] = self.sbml_network.getLineEndingFillColor(line_ending_id)

        # get fill rule
        if self.sbml_network.isSetLineEndingFillRule(line_ending_id):
            polygon_shape_info['fillRule'] = self.sbml_network.getLineEndingFillRule(line_ending_id)

        vertices_ = []
        for v_index in range(self.sbml_network.getLineEndingGeometricShapeNumSegments(line_ending_id)):
            vertex_ = {}
            vertex_['renderPointX'] = {'abs': self.sbml_network.getLineEndingGeometricShapeSegmentX(line_ending_id, v_index),
                                       'rel': 0.0}
            vertex_['renderPointY'] = {'abs': self.sbml_network.getLineEndingGeometricShapeSegmentY(line_ending_id, v_index),
                                       'rel': 0.0}
            if self.sbml_network.isLineEndingGeometricShapeSegmentCubicBezier(line_ending_id, v_index):
                vertex_['basePoint1X'] = {'abs': self.sbml_network.getLineEndingCurveSegmentBasePoint1X(line_ending_id, v_index),
                                          'rel': 0.0}
                vertex_['basePoint1Y'] = {'abs': self.sbml_network.getLineEndingCurveSegmentBasePoint1Y(line_ending_id, v_index),
                                          'rel': 0.0}
                vertex_['basePoint2X'] = {'abs': self.sbml_network.getLineEndingCurveSegmentBasePoint2X(line_ending_id, v_index),
                                          'rel': 0.0}
                vertex_['basePoint2Y'] = {'abs': self.sbml_network.getLineEndingCurveSegmentBasePoint2Y(line_ending_id, v_index),
                                          'rel': 0.0}
            vertices_.append(vertex_)
        polygon_shape_info['vertices'] = vertices_

        return polygon_shape_info