from .import_base import NetworkInfoImportBase
import libsbmlnetworkeditor
import libsbml
import math


class NetworkInfoImportFromSBMLModel(NetworkInfoImportBase):
    def __init__(self):
        super().__init__()
        self.document = None
        self.layout = None
        self.global_render = None
        self.local_render = None

    def extract_info(self, graph):
        super().extract_info(graph)

        self.document = libsbmlnetworkeditor.readSBML(graph)
        self.extract_layout_info(self.document)
        self.extract_render_info(self.document)

    def extract_layout_info(self, document):
        if not libsbmlnetworkeditor.getNumLayouts(document):
            libsbmlnetworkeditor.createDefaultLayout(document)
        self.layout = libsbmlnetworkeditor.getLayout(document)
        self.extract_layout_features()

    def extract_render_info(self, document):
        self.extract_global_render_info(document)
        self.extract_global_render_features()
        self.extract_local_render_info(document)
        self.assign_graphical_object_styles()

    def extract_global_render_info(self, document):
        if not libsbmlnetworkeditor.getNumGlobalRenderInformation(document):
            libsbmlnetworkeditor.createDefaultGlobalRenderInformation(document)
        self.global_render = libsbmlnetworkeditor.getGlobalRenderInformation(document)

    def extract_local_render_info(self, document):
        if not libsbmlnetworkeditor.getNumLocalRenderInformation(self.layout):
            libsbmlnetworkeditor.createDefaultLocalRenderInformation(document)
        self.local_render = libsbmlnetworkeditor.getLocalRenderInformation(self.layout)

    def extract_layout_features(self):
        for c_index in range(libsbmlnetworkeditor.getNumCompartmentGlyphs(self.layout)):
            self.add_compartment(libsbmlnetworkeditor.getCompartmentGlyph(self.layout, c_index))

        for s_index in range(libsbmlnetworkeditor.getNumSpeciesGlyphs(self.layout)):
            self.add_species(libsbmlnetworkeditor.getSpeciesGlyph(self.layout, s_index))

        for r_index in range(libsbmlnetworkeditor.getNumReactionGlyphs(self.layout)):
            self.add_reaction(libsbmlnetworkeditor.getReactionGlyph(self.layout, r_index))

    def extract_global_render_features(self):
        if libsbmlnetworkeditor.isSetBackgroundColor(self.global_render):
            self.background_color = libsbmlnetworkeditor.getBackgroundColor(self.global_render)

        # get colors info
        for c_index in range(libsbmlnetworkeditor.getNumColorDefinitions(self.global_render)):
            self.add_color(libsbmlnetworkeditor.getColorDefinition(self.global_render, c_index))

        # get gradients info
        for g_index in range(libsbmlnetworkeditor.getNumGradientDefinitions(self.global_render)):
            self.add_gradient(libsbmlnetworkeditor.getGradientDefinition(self.global_render, g_index))

        # get line ending info
        for le_index in range(libsbmlnetworkeditor.getNumLineEndings(self.global_render)):
            self.add_line_ending(libsbmlnetworkeditor.getLineEnding(self.global_render, le_index))

    def extract_extents(self, bounding_box):
        self.extents['minX'] = 0.0
        self.extents['maxX'] = max(self.extents['maxX'], bounding_box['x'] + bounding_box['width'])
        self.extents['minY'] = 0.0
        self.extents['maxY'] = max(self.extents['maxY'], bounding_box['y'] + bounding_box['height'])

    def add_compartment(self, compartment_object):
        compartment = self.extract_go_object_features(compartment_object)
        compartment['SBMLObject'] = self.get_sbml_compartment_object(compartment_object)
        self.compartments.append(compartment)

    def add_species(self, species_object):
        species = self.extract_go_object_features(species_object)
        species['SBMLObject'] = self.get_sbml_species_object(species_object)

        # set the compartment
        s_compartment = libsbmlnetworkeditor.getCompartmentId(self.document, species_object)
        if s_compartment:
            for c in self.compartments:
                if s_compartment == c['referenceId']:
                    species['compartment'] = c['referenceId']
                    break

        self.species.append(species)

    def add_reaction(self, reaction_object):
        reaction = self.extract_go_object_features(reaction_object)
        reaction['SBMLObject'] = self.get_sbml_reaction_object(reaction_object)

        # set the compartment
        r_compartment = libsbmlnetworkeditor.getCompartmentId(self.document, reaction_object)
        if r_compartment:
            for c in self.compartments:
                if r_compartment == c['referenceId']:
                    reaction['compartment'] = c['referenceId']
                    break

        # species references
        reaction['speciesReferences'] = []
        for sr_index in range(libsbmlnetworkeditor.getNumSpeciesReferenceGlyphs(reaction_object)):
            species_reference_object = libsbmlnetworkeditor.getSpeciesReferenceGlyph(reaction_object, sr_index)
            species_reference = self.extract_go_object_features(species_reference_object)
            species_reference['species'] = libsbmlnetworkeditor.getSBMLObjectId(self.layout,
                libsbmlnetworkeditor.getSpeciesGlyphId(species_reference_object))
            species_reference['speciesGlyph'] = \
                libsbmlnetworkeditor.getSpeciesGlyphId(species_reference_object)
            species_reference['SBMLObject'] = self.get_sbml_species_reference_object(species_reference_object, reaction_object)
            if libsbmlnetworkeditor.isSetRole(species_reference_object):
                species_reference['role'] = libsbmlnetworkeditor.getRole(species_reference_object)
            reaction['speciesReferences'].append(species_reference)

        self.reactions.append(reaction)

    def add_color(self, color_object):
        color_ = {}
        color_['colorDefinition'] = color_object
        color_['id'] = libsbmlnetworkeditor.getId(color_object)
        self.colors.append(color_)

    def add_gradient(self, gradient_object):
        gradeint_ = {}
        gradeint_['gradientDefinition'] = gradient_object
        gradeint_['id'] = libsbmlnetworkeditor.getId(gradient_object)
        self.gradient.append(gradeint_)

    def add_line_ending(self, line_ending_object):
        line_ending_ = {}
        line_ending_['lineEnding'] = line_ending_object
        line_ending_['id'] = libsbmlnetworkeditor.getId(line_ending_object)
        self.line_endings.append(line_ending_)

    def assign_graphical_object_styles(self):
        # get compartments style from veneer
        for compartment in self.compartments:
            style = libsbmlnetworkeditor.getStyle(self.local_render, compartment['glyphObject'])
            if not style:
                style = libsbmlnetworkeditor.getStyle(self.global_render, compartment['glyphObject'])
            compartment['style'] = style

            # get compartment text style from veneer
            if 'texts' in list(compartment.keys()):
                for text in compartment['texts']:
                    style = libsbmlnetworkeditor.getStyle(self.local_render, text['glyphObject'])
                    if not style:
                        style = libsbmlnetworkeditor.getStyle(self.global_render, text['glyphObject'])
                    text['style'] = style

        # get species style from veneer
        for species in self.species:
            style = libsbmlnetworkeditor.getStyle(self.local_render, species['glyphObject'])
            if not style:
                style = libsbmlnetworkeditor.getStyle(self.global_render, species['glyphObject'])
            species['style'] = style

            # get species text style from veneer
            if 'texts' in list(species.keys()):
                for text in species['texts']:
                    style = libsbmlnetworkeditor.getStyle(self.local_render, text['glyphObject'])
                    if not style:
                        style = libsbmlnetworkeditor.getStyle(self.global_render, text['glyphObject'])
                    text['style'] = style

        # get reactions style from veneer
        for reaction in self.reactions:
            style = libsbmlnetworkeditor.getStyle(self.local_render, reaction['glyphObject'])
            if not style:
                style = libsbmlnetworkeditor.getStyle(self.global_render, reaction['glyphObject'])
            reaction['style'] = style

            # get reaction text style from veneer
            if 'texts' in list(reaction.keys()):
                for text in reaction['texts']:
                    style = libsbmlnetworkeditor.getStyle(self.local_render, text['glyphObject'])
                    if not style:
                        style = libsbmlnetworkeditor.getStyle(self.global_render, text['glyphObject'])
                    text['style'] = style

            # get species references style from veneer
            if 'speciesReferences' in list(reaction.keys()):
                for species_reference in reaction['speciesReferences']:
                    style = libsbmlnetworkeditor.getStyle(self.local_render, species_reference['glyphObject'])
                    if not style:
                        style = libsbmlnetworkeditor.getStyle(self.global_render, species_reference['glyphObject'])
                    species_reference['style'] = style

    def get_sbml_compartment_object(self, compartment_object):
        compartment_id = libsbmlnetworkeditor.getSBMLObjectId(self.layout, compartment_object)
        libsbmlnetworkeditor.getCompartment(self.document, compartment_id)

    def get_sbml_species_object(self, species_object):
        species_id = libsbmlnetworkeditor.getSBMLObjectId(self.layout, species_object)
        return libsbmlnetworkeditor.getSpecies(self.document, species_id)

    def get_sbml_reaction_object(self, reaction_object):
        reaction_id = libsbmlnetworkeditor.getSBMLObjectId(self.layout, reaction_object)
        return libsbmlnetworkeditor.getReaction(self.document, reaction_id)

    def get_sbml_species_reference_object(self, species_reference_object, reaction_object):
        reaction_id = libsbmlnetworkeditor.getSBMLObjectId(self.layout, reaction_object)
        species_id = libsbmlnetworkeditor.getSBMLObjectId(self.layout, libsbmlnetworkeditor.getSpeciesGlyphId(species_reference_object))
        if libsbmlnetworkeditor.getRole(species_reference_object) == "modifier":
            return libsbmlnetworkeditor.getModifierSpeciesReference(self.document, reaction_id, species_id)
        else:
            return libsbmlnetworkeditor.getSpeciesReference(self.document, reaction_id, species_id)

    def extract_go_object_features(self, go_object):
        features = {'glyphObject': go_object, 'referenceId': libsbmlnetworkeditor.getSBMLObjectId(self.layout, go_object),
                    'id': libsbmlnetworkeditor.getId(go_object)}

        if libsbmlnetworkeditor.getMetaId(go_object):
            features['metaId'] = libsbmlnetworkeditor.getMetaId(go_object)
        # text
        features['texts'] = []
        for text_index in range(libsbmlnetworkeditor.getNumTextGlyphs(self.layout, go_object)):
            features['texts'].append(self.extract_text_object_features(libsbmlnetworkeditor.getTextGlyph(self.layout, go_object, text_index)))

        return features

    def extract_text_object_features(self, text_object):
        text = {'glyphObject': text_object, 'id': libsbmlnetworkeditor.getId(text_object)}
        if libsbmlnetworkeditor.isSetOriginOfTextId(text_object):
            text['graphicalObject'] = \
                libsbmlnetworkeditor.getGraphicalObject(self.layout, libsbmlnetworkeditor.getOriginOfTextId(text_object))
        elif libsbmlnetworkeditor.isSetGraphicalObjectId(text_object):
            graphical_object_id = libsbmlnetworkeditor.getGraphicalObjectId(text_object)
            text['graphicalObject'] = \
                libsbmlnetworkeditor.getGraphicalObject(self.layout, libsbmlnetworkeditor.getSBMLObjectId(self.layout, graphical_object_id))
        return text

    def extract_compartment_features(self, compartment):
        compartment['features'] = self.extract_go_general_features(compartment)
        if compartment['glyphObject']:
            self.extract_extents(compartment['features']['boundingBox'])

    def extract_species_features(self, species):
        species['features'] = self.extract_go_general_features(species)

    def extract_reaction_features(self, reaction):
        reaction['features'] = self.extract_go_general_features(reaction)
        if reaction['glyphObject']:
            # get curve features
            if libsbmlnetworkeditor.isSetCurve(reaction['glyphObject']):
                crv = libsbmlnetworkeditor.getCurve(reaction['glyphObject'])
                if libsbmlnetworkeditor.getNumCurveSegments(crv):
                    curve_ = []
                    for e_index in range(libsbmlnetworkeditor.getNumCurveSegments(crv)):
                        element_ = {'startX': libsbmlnetworkeditor.getCurveSegmentStartPointX(crv, e_index),
                                    'startY': libsbmlnetworkeditor.getCurveSegmentStartPointY(crv, e_index),
                                    'endX': libsbmlnetworkeditor.getCurveSegmentEndPointX(crv, e_index),
                                    'endY': libsbmlnetworkeditor.getCurveSegmentEndPointY(crv, e_index)}
                        if libsbmlnetworkeditor.isCubicBezier(crv, e_index):
                            element_["basePoint1X"] = libsbmlnetworkeditor.getCurveSegmentBasePoint1X(crv, e_index)
                            element_["basePoint1Y"] = libsbmlnetworkeditor.getCurveSegmentBasePoint1Y(crv, e_index)
                            element_["basePoint2X"] = libsbmlnetworkeditor.getCurveSegmentBasePoint2X(crv, e_index)
                            element_["basePoint2Y"] = libsbmlnetworkeditor.getCurveSegmentBasePoint2Y(crv, e_index)
                        curve_.append(element_)
                    reaction['features']['curve'] = curve_

                    ## extract extent box features might be needed here

            # get curve features
            if 'style' in list(reaction.keys()):
                if 'curve' in list(reaction['features'].keys()):
                    reaction['features']['graphicalCurve'] = \
                        self.extract_curve_features(libsbmlnetworkeditor.getRenderGroup(reaction['style']))

    def extract_species_reference_features(self, species_reference):
        species_reference['features'] = {}
        if species_reference['glyphObject']:
            # get curve features
            if libsbmlnetworkeditor.isSetCurve(species_reference['glyphObject']):
                crv = libsbmlnetworkeditor.getCurve(species_reference['glyphObject'])
                if libsbmlnetworkeditor.getNumCurveSegments(crv):
                    curve_ = []
                    for e_index in range(libsbmlnetworkeditor.getNumCurveSegments(crv)):
                        element_ = {'startX': libsbmlnetworkeditor.getCurveSegmentStartPointX(crv, e_index),
                                    'startY': libsbmlnetworkeditor.getCurveSegmentStartPointY(crv, e_index),
                                    'endX': libsbmlnetworkeditor.getCurveSegmentEndPointX(crv, e_index),
                                    'endY': libsbmlnetworkeditor.getCurveSegmentEndPointY(crv, e_index)}
                        if libsbmlnetworkeditor.isCubicBezier(crv, e_index):
                            element_['basePoint1X'] = libsbmlnetworkeditor.getCurveSegmentBasePoint1X(crv, e_index)
                            element_['basePoint1Y'] = libsbmlnetworkeditor.getCurveSegmentBasePoint1Y(crv, e_index)
                            element_['basePoint2X'] = libsbmlnetworkeditor.getCurveSegmentBasePoint2X(crv, e_index)
                            element_['basePoint2Y'] = libsbmlnetworkeditor.getCurveSegmentBasePoint2Y(crv, e_index)

                        # set start point and slope
                        if e_index == 0:
                            # start point
                            species_reference['features']['startPoint'] = {'x': element_['startX'],
                                                                           'y': element_['startY']}

                            # start slope
                            if 'basePoint1X' in list(element_.keys()) \
                                    and not element_['startX'] == element_['basePoint1X']:
                                species_reference['features']['startSlope'] = \
                                    math.atan2(element_['startY'] - element_['basePoint1Y'],
                                               element_['startX'] - element_['basePoint1X'])
                            else:
                                species_reference['features']['startSlope'] = \
                                    math.atan2(element_['startY'] - element_['endY'],
                                               element_['startX'] - element_['endX'])

                        # set end point and slope
                        if e_index == libsbmlnetworkeditor.getNumCurveSegments(crv) - 1:
                            species_reference['features']['endPoint'] = {'x': element_['endX'],
                                                                         'y': element_['endY']}

                            # end slope
                            if 'basePoint2X' in list(element_.keys()) \
                                    and not element_['endX'] == element_['basePoint2X']:
                                species_reference['features']['endSlope'] = \
                                    math.atan2(element_['endY'] - element_['basePoint2Y'],
                                               element_['endX'] - element_['basePoint2X'])
                            else:
                                species_reference['features']['endSlope'] = \
                                    math.atan2(element_['endY'] - element_['startY'],
                                               element_['endX'] - element_['startX'])

                        curve_.append(element_)

                    species_reference['features']['curve'] = curve_

            # get group features
            if 'style' in list(species_reference.keys()):
                species_reference['features']['graphicalCurve'] = \
                    self.extract_curve_features(libsbmlnetworkeditor.getRenderGroup(species_reference['style']))

    @staticmethod
    def extract_color_features(color):
        pass

    @staticmethod
    def extract_gradient_features(gradient):
        pass

    def extract_line_ending_features(self, line_ending):
        line_ending['features'] = {}
        if line_ending['lineEnding']:
            # get bounding box features
            bbox = libsbmlnetworkeditor.getBoundingBoxOfLineEnding(line_ending['lineEnding'])
            line_ending['features']['boundingBox'] = {'x': libsbmlnetworkeditor.getPositionX(bbox), 'y': libsbmlnetworkeditor.getPositionY(bbox),
                                                      'width': libsbmlnetworkeditor.getDimensionWidth(bbox),
                                                      'height': libsbmlnetworkeditor.getDimensionHeight(bbox)}

            line_ending['features']['graphicalShape'] = \
                self.extract_graphical_shape_features(libsbmlnetworkeditor.getRenderGroup(line_ending['lineEnding']))

            # get enable rotation
            if libsbmlnetworkeditor.isSetEnableRotationalMapping(line_ending['lineEnding']):
                line_ending['features']['enableRotation'] = libsbmlnetworkeditor.getEnableRotationalMapping(line_ending['lineEnding'])

    def extract_go_general_features(self, go):
        features = {}
        if go['glyphObject']:
            # get bounding box features
            features['boundingBox'] = self.extract_bounding_box_features(libsbmlnetworkeditor.getBoundingBox(go['glyphObject']))

            # get group features
            if 'style' in list(go.keys()):
                features['graphicalShape'] = \
                    self.extract_graphical_shape_features(libsbmlnetworkeditor.getRenderGroup(go['style']))

            # get text features
            if 'texts' in list(go.keys()):
                for text in go['texts']:
                    text['features'] = self.extract_go_text_features(text)


        return features

    def extract_go_text_features(self, text):
        text_features = {}
        # get plain text
        if libsbmlnetworkeditor.isSetText(text['glyphObject']):
            text_features['plainText'] = libsbmlnetworkeditor.getText(text['glyphObject'])
        elif 'graphicalObject' in list(text.keys()):
            if libsbmlnetworkeditor.isSetName(text['graphicalObject']):
                text_features['plainText'] = libsbmlnetworkeditor.getName(text['graphicalObject'])
            elif libsbmlnetworkeditor.getSBMLObjectId(self.layout, text['graphicalObject']):
                text_features['plainText'] = libsbmlnetworkeditor.getSBMLObjectId(self.layout, text['graphicalObject'])
            else:
                text_features['plainText'] = libsbmlnetworkeditor.getId(text['graphicalObject'])
        if 'plainText' not in list(text_features.keys()):
            if 'text-name' in list(text_features.keys()):
                text_features['plainText'] = text_features['text-name']
            elif 'text-id' in list(text_features.keys()):
                text_features['plainText'] = text_features['text-id']
        # get bounding box features of the text glyph
        text_features['boundingBox'] = self.extract_bounding_box_features(libsbmlnetworkeditor.getBoundingBox(text['glyphObject']))

        # get group features
        if 'style' in list(text.keys()):
            text_features['graphicalText'] = self.extract_text_features(libsbmlnetworkeditor.getRenderGroup(text['style']))
        return text_features

    @staticmethod
    def extract_color_features(color):
        color['features'] = {}
        if color['colorDefinition']:
            # get color value
            if libsbmlnetworkeditor.isSetValue(color['colorDefinition']):
                color['features']['value'] = libsbmlnetworkeditor.getValue(color['colorDefinition'])

    @staticmethod
    def extract_gradient_features(gradient):
        gradient['features'] = {}
        if gradient['gradientBase']:
            # get spread method
            if libsbmlnetworkeditor.isSetSpreadMethod(gradient['gradientBase']):
                gradient['features']['spreadMethod'] = libsbmlnetworkeditor.getSpreadMethod(gradient['gradientBase'])

            # get gradient stops
            stops_ = []
            for s_index in range(libsbmlnetworkeditor.getNumGradientStops(gradient['gradientBase'])):
                stop_ = {'gradientStop': libsbmlnetworkeditor.getGradientStop(gradient['gradientBase'], s_index)}

                # get offset
                if libsbmlnetworkeditor.isSetOffset(stop_['gradientStop']):
                    stop_['offset'] = \
                        {'abs': 0, 'rel': libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getOffset(stop_['gradientStop']))}

                # get stop color
                if libsbmlnetworkeditor.isSetStopColor(stop_['gradientStop']):
                    stop_['color'] = libsbmlnetworkeditor.getStopColor(stop_['gradientStop'])
                stops_.append(stop_)
            gradient['features']['stops'] = stops_

            # for linear gradient
            if libsbmlnetworkeditor.isLinearGradient(gradient['gradientBase']):
                # get start
                gradient['features']['start'] = \
                    {'x': {'abs':
                               libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getLinearGradientX1(gradient['gradientBase'])),
                           'rel':
                               libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getLinearGradientX1(gradient['gradientBase']))},
                     'y': {'abs':
                               libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getLinearGradientY1(gradient['gradientBase'])),
                           'rel':
                               libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getLinearGradientY1(gradient['gradientBase']))}}

                # get end
                gradient['features']['end'] = \
                    {'x': {'abs':
                               libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getLinearGradientX2(gradient['gradientBase'])),
                           'rel':
                               libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getLinearGradientX2(gradient['gradientBase']))},
                     'y': {'abs':
                               libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getLinearGradientY2(gradient['gradientBase'])),
                           'rel':
                               libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getLinearGradientY2(gradient['gradientBase']))}}

            # for radial gradient
            elif libsbmlnetworkeditor.isLinearGradient(gradient['gradientBase']):
                # get center
                gradient['features']['center'] = \
                    {'x': {'abs':
                               libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getRadialGradientCx(gradient['gradientBase'])),
                           'rel':
                               libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getRadialGradientCx(gradient['gradientBase']))},
                     'y': {'abs':
                               libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getRadialGradientCy(gradient['gradientBase'])),
                           'rel':
                               libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getRadialGradientCy(gradient['gradientBase']))}}

                # get focal
                gradient['features']['focalPoint'] = \
                    {'x': {'abs':
                               libsbmlnetworkeditor.ne_rav_getAbsoluteValue(libsbmlnetworkeditor.getRadialGradientFx(gradient['gradientBase'])),
                           'rel':
                               libsbmlnetworkeditor.ne_rav_getRelativeValue(libsbmlnetworkeditor.getRadialGradientFx(gradient['gradientBase']))},
                     'y': {'abs':
                               libsbmlnetworkeditor.ne_rav_getAbsoluteValue(libsbmlnetworkeditor.getRadialGradientFy(gradient['gradientBase'])),
                           'rel':
                               libsbmlnetworkeditor.ne_rav_getRelativeValue(libsbmlnetworkeditor.getRadialGradientFy(gradient['gradientBase']))}}

                # get radius
                gradient['features']['radius'] = \
                    {'abs': libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getRadialGradientR(gradient['gradientBase'])),
                     'rel': libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getRadialGradientR(gradient['gradientBase']))}

    def extract_line_ending_features(self, line_ending):
        line_ending['features'] = {}
        if line_ending['lineEnding']:
            # get bounding box features
            line_ending['features']['boundingBox'] = self.extract_bounding_box_features(libsbmlnetworkeditor.getBoundingBoxOfLineEnding(line_ending['lineEnding']))

            # get group features
            line_ending['features']['graphicalShape'] = \
                self.extract_graphical_shape_features(libsbmlnetworkeditor.getRenderGroup(line_ending['lineEnding']))

            # get enable rotation
            if libsbmlnetworkeditor.isSetEnableRotationalMapping(line_ending['lineEnding']):
                line_ending['features']['enableRotation'] = libsbmlnetworkeditor.getEnableRotationalMapping(line_ending['lineEnding'])

    def extract_graphical_shape_features(self, group):
        graphical_shape_info = {}
        if group:
            graphical_shape_info = self.extract_render_group_general_features(group)
            graphical_shape_info['geometricShapes'] = self.extract_render_group_geometric_shapes(group)
        return graphical_shape_info

    @staticmethod
    def extract_render_group_general_features(group):
        render_group_general_features = {}
        # get stroke color
        if libsbmlnetworkeditor.isSetStrokeColor(group):
            render_group_general_features['strokeColor'] = libsbmlnetworkeditor.getStrokeColor(group)

        # get stroke width
        if libsbmlnetworkeditor.isSetStrokeWidth(group):
            render_group_general_features['strokeWidth'] = libsbmlnetworkeditor.getStrokeWidth(group)

        # get stroke dash array
        if libsbmlnetworkeditor.isSetStrokeDashArray(group):
            dash_array = []
            for d_index in range(libsbmlnetworkeditor.getNumStrokeDashes(group)):
                dash_array.append(libsbmlnetworkeditor.getStrokeDash(group, d_index))
            render_group_general_features['strokeDashArray'] = tuple(dash_array)

        # get fill color
        if libsbmlnetworkeditor.isSetFillColor(group):
            render_group_general_features['fillColor'] = libsbmlnetworkeditor.getFillColor(group)

        # get fill rule
        if libsbmlnetworkeditor.isSetFillRule(group):
            render_group_general_features['fillRule'] = libsbmlnetworkeditor.getFillRule(group)
        return render_group_general_features

    def extract_render_group_geometric_shapes(self, group):
        geometric_shapes = []
        if libsbmlnetworkeditor.getNumGeometricShapes(group):
            for gs_index in range(libsbmlnetworkeditor.getNumGeometricShapes(group)):
                gs = libsbmlnetworkeditor.getGeometricShape(group, gs_index)
                geometric_shape = {}
                geometric_shape.update(self.extract_geometric_shape_general_features(gs))
                geometric_shape.update(self.extract_geometric_shape_exclusive_features(gs))
                geometric_shapes.append(geometric_shape)

        return geometric_shapes

    @staticmethod
    def extract_geometric_shape_general_features(gs):
        geometric_shape_general_features = {}
        # get stroke color
        if libsbmlnetworkeditor.isSetStrokeColor(gs):
            geometric_shape_general_features['strokeColor'] = libsbmlnetworkeditor.getStrokeColor(gs)

        # get stroke width
        if libsbmlnetworkeditor.isSetStrokeWidth(gs):
            geometric_shape_general_features['strokeWidth'] = libsbmlnetworkeditor.getStrokeWidth(gs)

        # get stroke dash array
        if libsbmlnetworkeditor.isSetStrokeDashArray(gs):
            dash_array = []
            for d_index in range(libsbmlnetworkeditor.getNumStrokeDashes(gs)):
                dash_array.append(libsbmlnetworkeditor.getStrokeDash(gs, d_index))
            geometric_shape_general_features['strokeDashArray'] = tuple(dash_array)
        return geometric_shape_general_features

    def extract_geometric_shape_exclusive_features(self, gs):
        if libsbmlnetworkeditor.isImage(gs):
            return self.extract_image_shape_features(gs)
        elif libsbmlnetworkeditor.isRenderCurve(gs):
            return self.extract_curve_shape_features(gs)
        elif libsbmlnetworkeditor.isText(gs):
            return self.extract_text_shape_features(gs)
        elif libsbmlnetworkeditor.isRectangle(gs):
            return self.extract_rectangle_shape_features(gs)
        elif libsbmlnetworkeditor.isEllipse(gs):
            return self.extract_ellipse_shape_features(gs)
        elif libsbmlnetworkeditor.isPolygon(gs):
            return self.extract_polygon_shape_features(gs)

    @staticmethod
    def extract_curve_features(group):
        curve_info = {}
        if group:
            # get stroke color
            if libsbmlnetworkeditor.isSetStrokeColor(group):
                curve_info['strokeColor'] = libsbmlnetworkeditor.getStrokeColor(group)

            # get stroke width
            if libsbmlnetworkeditor.isSetStrokeWidth(group):
                curve_info['strokeWidth'] = libsbmlnetworkeditor.getStrokeWidth(group)

            # get stroke dash array
            if libsbmlnetworkeditor.isSetStrokeDashArray(group):
                dash_array = []
                for d_index in range(libsbmlnetworkeditor.getNumStrokeDashes(group)):
                    dash_array.append(libsbmlnetworkeditor.getStrokeDash(group, d_index))
                curve_info['strokeDashArray'] = tuple(dash_array)

            # get heads
            heads_ = {}
            if libsbmlnetworkeditor.isSetStartHead(group):
                heads_['start'] = libsbmlnetworkeditor.getStartHead(group)
            if libsbmlnetworkeditor.isSetEndHead(group):
                heads_['end'] = libsbmlnetworkeditor.getEndHead(group)
            if heads_:
                curve_info['heads'] = heads_
        return curve_info

    @staticmethod
    def extract_text_features(group):
        text_info = {}
        if group:
            # get stroke color
            if libsbmlnetworkeditor.isSetFontColor(group):
                text_info['strokeColor'] = libsbmlnetworkeditor.getFontColor(group)

            # get font family
            if libsbmlnetworkeditor.isSetFontFamily(group):
                text_info['fontFamily'] = libsbmlnetworkeditor.getFontFamily(group)

            # get font size
            if libsbmlnetworkeditor.isSetFontSize(group):
                rel_abs_vec = libsbmlnetworkeditor.getFontSize(group)
                text_info['fontSize'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                         'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

            # get font weight
            if libsbmlnetworkeditor.isSetFontWeight(group):
                text_info['fontWeight'] = libsbmlnetworkeditor.getFontWeight(group)

            # get font style
            if libsbmlnetworkeditor.isSetFontStyle(group):
                text_info['fontStyle'] = libsbmlnetworkeditor.getFontStyle(group)

            # get horizontal text anchor
            if libsbmlnetworkeditor.isSetTextAnchor(group):
                text_info['hTextAnchor'] = libsbmlnetworkeditor.getTextAnchor(group)

            # get vertical text anchor
            if libsbmlnetworkeditor.isSetVTextAnchor(group):
                text_info['vTextAnchor'] = libsbmlnetworkeditor.getVTextAnchor(group)

            # get geometric shapes
            if libsbmlnetworkeditor.getNumGeometricShapes(group):
                geometric_shapes = []
                for gs_index in range(libsbmlnetworkeditor.getNumGeometricShapes(group)):
                    gs = libsbmlnetworkeditor.getGeometricShape(group, gs_index)

                    if libsbmlnetworkeditor.isText(gs):
                        geometric_shape_features = {}

                        # get stroke color
                        if libsbmlnetworkeditor.isSetFontColor(gs):
                            geometric_shape_features['strokeColor'] = libsbmlnetworkeditor.getFontColor(gs)

                        # get geometric shape specific features
                        get_geometric_shape_exclusive_features(gs, geometric_shape_features)
                        geometric_shapes.append(geometric_shape_features)

                text_info['geometricShapes'] = geometric_shapes
        return text_info

    @staticmethod
    def extract_image_shape_features(image_shape):
        # set shape
        image_shape_info = {'shape': "image"}

        # get position x
        if libsbmlnetworkeditor.isSetGeometricShapeX(image_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeX(image_shape)
            image_shape_info['x'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                     'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get position y
        if libsbmlnetworkeditor.isSetGeometricShapeY(image_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeY(image_shape)
            image_shape_info['y'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                     'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get dimension width
        if libsbmlnetworkeditor.isSetGeometricShapeWidth(image_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeWidth(image_shape)
            image_shape_info['width'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                         'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get dimension height
        if libsbmlnetworkeditor.isSetGeometricShapeHeight(image_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeHeight(image_shape)
            image_shape_info['height'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                          'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get href
        if libsbmlnetworkeditor.isSetGeometricShapeHref(image_shape):
            image_shape_info['href'] = libsbmlnetworkeditor.getGeometricShapeHref(image_shape)

        return image_shape_info

    @staticmethod
    def extract_curve_shape_features(curve_shape):
        # set shape
        curve_shape_info = {'shape': "renderCurve"}

        vertices_ = []
        for v_index in range(libsbmlnetworkeditor.getGeometricShapeNumElements(curve_shape)):
            vertex_ = {}
            vertex_['renderPointX'] = dict(
                abs=libsbmlnetworkeditor.getAbsoluteValue(
                    libsbmlnetworkeditor.getGeometricShapeElementX(curve_shape, v_index)),
                rel=libsbmlnetworkeditor.getRelativeValue(
                    libsbmlnetworkeditor.getGeometricShapeElementX(curve_shape, v_index)))
            vertex_['renderPointY'] = dict(
                abs=libsbmlnetworkeditor.getAbsoluteValue(
                    libsbmlnetworkeditor.getGeometricShapeElementY(curve_shape, v_index)),
                rel=libsbmlnetworkeditor.getRelativeValue(
                    libsbmlnetworkeditor.getGeometricShapeElementY(curve_shape, v_index)))

            if sbne.isRenderCubicBezier(curve_shape, v_index):
                vertex_['basePoint1X'] = dict(
                    abs=libsbmlnetworkeditor.getAbsoluteValue(
                        libsbmlnetworkeditor.getGeometricShapeBasePoint1X(curve_shape, v_index)),
                    rel=libsbmlnetworkeditor.getRelativeValue(
                        libsbmlnetworkeditor.getGeometricShapeBasePoint1X(curve_shape, v_index)))
                vertex_['basePoint1Y'] = dict(
                    abs=libsbmlnetworkeditor.getAbsoluteValue(
                        libsbmlnetworkeditor.getGeometricShapeBasePoint1Y(curve_shape, v_index)),
                    rel=libsbmlnetworkeditor.getRelativeValue(
                        libsbmlnetworkeditor.getGeometricShapeBasePoint1Y(curve_shape, v_index)))
                vertex_['basePoint2X'] = dict(
                    abs=libsbmlnetworkeditor.getAbsoluteValue(
                        libsbmlnetworkeditor.getGeometricShapeBasePoint2X(curve_shape, v_index)),
                    rel=libsbmlnetworkeditor.getRelativeValue(
                        libsbmlnetworkeditor.getGeometricShapeBasePoint2X(curve_shape, v_index)))
                vertex_['basePoint2Y'] = dict(
                    abs=libsbmlnetworkeditor.getAbsoluteValue(
                        libsbmlnetworkeditor.getGeometricShapeBasePoint2Y(curve_shape, v_index)),
                    rel=libsbmlnetworkeditor.getRelativeValue(
                        libsbmlnetworkeditor.getGeometricShapeBasePoint2Y(curve_shape, v_index)))

            vertices_.append(vertex_)

        curve_shape_info['vertices'] = vertices_

        return curve_shape_info

    @staticmethod
    def extract_text_shape_features(text_shape):
        # set shape
        text_shape_info = {'shape': "text"}

        # get position x
        if libsbmlnetworkeditor.isSetGeometricShapeX(text_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeX(text_shape)
            text_shape_info['x'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                    'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get position y
        if libsbmlnetworkeditor.isSetGeometricShapeY(text_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeY(text_shape)
            text_shape_info['y'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                    'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get font family
        if libsbmlnetworkeditor.isSetFontFamily(text_shape):
            text_shape_info['fontFamily'] = libsbmlnetworkeditor.getFontFamily(text_shape)

        # get font size
        if libsbmlnetworkeditor.isSetFontSize(text_shape):
            rel_abs_vec = libsbmlnetworkeditor.getFontSize(gs)
            text_shape_info['fontSize'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                           'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get font weight
        if libsbmlnetworkeditor.isSetFontWeight(text_shape):
            text_shape_info['fontWeight'] = libsbmlnetworkeditor.getFontWeight(text_shape)

        # get font style
        if libsbmlnetworkeditor.isSetFontStyle(text_shape):
            text_shape_info['fontStyle'] = libsbmlnetworkeditor.getFontStyle(text_shape)

        # get horizontal text anchor
        if libsbmlnetworkeditor.isSetTextAnchor(text_shape):
            text_shape_info['hTextAnchor'] = libsbmlnetworkeditor.getTextAnchor(text_shape)

        # get vertical text anchor
        if libsbmlnetworkeditor.isSetVTextAnchor(text_shape):
            text_shape_info['vTextAnchor'] = libsbmlnetworkeditor.getVTextAnchor(text_shape)

        return text_shape_info

    @staticmethod
    def extract_rectangle_shape_features(rectangle_shape):
        # set shape
        rectangle_shape_info = {'shape': "rectangle"}

        # get fill color
        if libsbmlnetworkeditor.isSetFillColor(rectangle_shape):
            rectangle_shape_info['fillColor'] = libsbmlnetworkeditor.getFillColor(rectangle_shape)

        # get position x
        if libsbmlnetworkeditor.isSetGeometricShapeX(rectangle_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeX(rectangle_shape)
            rectangle_shape_info['x'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                         'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get position y
        if libsbmlnetworkeditor.isSetGeometricShapeY(rectangle_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeY(rectangle_shape)
            rectangle_shape_info['y'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                         'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get dimension width
        if libsbmlnetworkeditor.isSetGeometricShapeWidth(rectangle_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeWidth(rectangle_shape)
            rectangle_shape_info['width'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                             'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get dimension height
        if libsbmlnetworkeditor.isSetGeometricShapeHeight(rectangle_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeHeight(rectangle_shape)
            rectangle_shape_info['height'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                              'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get corner curvature radius rx
        if libsbmlnetworkeditor.isSetGeometricShapeCornerCurvatureRadiusX(rectangle_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeCornerCurvatureRadiusX(rectangle_shape)
            rectangle_shape_info['rx'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                          'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get corner curvature radius ry
        if libsbmlnetworkeditor.isSetGeometricShapeCornerCurvatureRadiusY(rectangle_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeCornerCurvatureRadiusY(rectangle_shape)
            rectangle_shape_info['ry'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                          'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get width/height ratio
        if libsbmlnetworkeditor.isSetGeometricShapeRatio(rectangle_shape):
            rectangle_shape_info['ratio'] = libsbmlnetworkeditor.getGeometricShapeRatio(rectangle_shape)

        return rectangle_shape_info

    @staticmethod
    def extract_ellipse_shape_features(ellipse_shape):
        # set shape
        ellipse_shape_info = {'shape': "ellipse"}

        # get fill color
        if libsbmlnetworkeditor.isSetFillColor(ellipse_shape):
            ellipse_shape_info['fillColor'] = libsbmlnetworkeditor.getFillColor(ellipse_shape)

        # get position cx
        if libsbmlnetworkeditor.isSetGeometricShapeCenterX(ellipse_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeCenterX(ellipse_shape)
            ellipse_shape_info['cx'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                        'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get position cy
        if libsbmlnetworkeditor.isSetGeometricShapeCenterY(ellipse_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeCenterY(ellipse_shape)
            ellipse_shape_info['cy'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                        'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get dimension rx
        if libsbmlnetworkeditor.isSetGeometricShapeRadiusX(ellipse_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeRadiusX(ellipse_shape)
            ellipse_shape_info['rx'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                        'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get dimension ry
        if libsbmlnetworkeditor.isSetGeometricShapeRadiusY(ellipse_shape):
            rel_abs_vec = libsbmlnetworkeditor.getGeometricShapeRadiusY(ellipse_shape)
            ellipse_shape_info['ry'] = {'abs': libsbmlnetworkeditor.getAbsoluteValue(rel_abs_vec),
                                        'rel': libsbmlnetworkeditor.getRelativeValue(rel_abs_vec)}

        # get radius ratio
        if libsbmlnetworkeditor.isSetGeometricShapeRatio(ellipse_shape):
            ellipse_shape_info['ratio'] = libsbmlnetworkeditor.getGeometricShapeRatio(ellipse_shape)

        return ellipse_shape_info

    @staticmethod
    def extract_polygon_shape_features(polygon_shape):
        # set shape
        polygon_shape_info = {'shape': "polygon"}

        # get fill color
        if libsbmlnetworkeditor.isSetFillColor(polygon_shape):
            polygon_shape_info['fillColor'] = libsbmlnetworkeditor.getFillColor(polygon_shape)

        # get fill rule
        if libsbmlnetworkeditor.isSetFillRule(polygon_shape):
            polygon_shape_info['fillRule'] = libsbmlnetworkeditor.getFillRule(polygon_shape)

        vertices_ = []
        for v_index in range(libsbmlnetworkeditor.getGeometricShapeNumElements(polygon_shape)):
            vertex_ = {}
            vertex_['renderPointX'] = dict(
                abs=libsbmlnetworkeditor.getAbsoluteValue(
                    libsbmlnetworkeditor.getGeometricShapeElementX(polygon_shape, v_index)),
                rel=libsbmlnetworkeditor.getRelativeValue(
                    libsbmlnetworkeditor.getGeometricShapeElementX(polygon_shape, v_index)))
            vertex_['renderPointY'] = dict(
                abs=libsbmlnetworkeditor.getAbsoluteValue(
                    libsbmlnetworkeditor.getGeometricShapeElementY(polygon_shape, v_index)),
                rel=libsbmlnetworkeditor.getRelativeValue(
                    libsbmlnetworkeditor.getGeometricShapeElementY(polygon_shape, v_index)))

            if libsbmlnetworkeditor.isRenderCubicBezier(polygon_shape, v_index):
                vertex_['basePoint1X'] = dict(
                    abs=libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getGeometricShapeBasePoint1X(polygon_shape, v_index)),
                    rel=libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getGeometricShapeBasePoint1X(polygon_shape, v_index)))
                vertex_['basePoint1Y'] = dict(
                    abs=libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getGeometricShapeBasePoint1Y(polygon_shape, v_index)),
                    rel=libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getGeometricShapeBasePoint1Y(polygon_shape, v_index)))
                vertex_['basePoint2X'] = dict(
                    abs=libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getGeometricShapeBasePoint2X(polygon_shape, v_index)),
                    rel=libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getGeometricShapeBasePoint2X(polygon_shape, v_index)))
                vertex_['basePoint2Y'] = dict(
                    abs=libsbmlnetworkeditor.getAbsoluteValue(libsbmlnetworkeditor.getGeometricShapeBasePoint2Y(polygon_shape, v_index)),
                    rel=libsbmlnetworkeditor.getRelativeValue(libsbmlnetworkeditor.getGeometricShapeBasePoint2Y(polygon_shape, v_index)))

            vertices_.append(vertex_)

        polygon_shape_info['vertices'] = vertices_

        return polygon_shape_info

    @staticmethod
    def extract_bounding_box_features(bounding_box):
        return {'x': libsbmlnetworkeditor.getPositionX(bounding_box), 'y': libsbmlnetworkeditor.getPositionY(bounding_box),
                        'width': libsbmlnetworkeditor.getDimensionWidth(bounding_box), 'height': libsbmlnetworkeditor.getDimensionHeight(bounding_box)}