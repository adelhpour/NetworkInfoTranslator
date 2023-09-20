import sys
import libsbne as sbne
import numpy as np
import math
import json
from pathlib import Path as pathlib
import libsbml
import webcolors


class SBMLGraphInfoImportBase:
    def __init__(self):
        self.compartments = []
        self.species = []
        self.reactions = []
        self.colors = []
        self.gradients = []
        self.line_endings = []
        self.extents = {}
        self.background_color = ""

    def reset_info(self):
        self.compartments.clear()
        self.species.clear()
        self.reactions.clear()
        self.colors.clear()
        self.gradients.clear()
        self.line_endings.clear()
        self.extents = {'minX': 0, 'maxX': 0, 'minY': 0, 'maxY': 0}
        self.background_color = "white"

    def find_compartment(self, compartment_reference_id):
        for compartment in self.compartments:
            if compartment_reference_id == compartment['referenceId']:
                return compartment

        return None

    def find_species(self, species_reference_id):
        for species in self.species:
            if species_reference_id == species['referenceId']:
                return species

        return None

    def find_reaction(self, reaction_reference_id):
        for reaction in self.reactions:
            if reaction_reference_id == reaction['referenceId']:
                return reaction

        return None

    def find_color(self, color_id):
        for color in self.colors:
            if color_id == color['id']:
                return color

        return None

    def find_color_value(self, color_id, search_among_gradients=True):
        # search among the gradients
        if search_among_gradients:
            for gradient in self.gradients:
                if color_id == gradient['id'] and 'stops' in list(gradient['features'].keys()):
                    stop_colors = []
                    for stop in gradient['features']['stops']:
                        if 'color' in list(stop.keys()):
                            stop_colors.append(mcolors.to_rgb(
                                find_color_value(graph_info,
                                                 stop['color'])))
                    if len(stop_colors):
                        return mcolors.to_hex(np.average(np.array(stop_colors), axis=0).tolist())

        # search among the colors
        for color in self.colors:
            if color_id == color['id'] and \
                    'value' in list(color['features'].keys()):
                return color['features']['value']

        return color_id

    def find_color_unique_id(self):
        color_id = "color"
        k = 0
        color_found = True
        while color_found:
            color_found = False
            k = k + 1
            for color in self.colors:
                if color_id + str(k) == color['id']:
                    color_found = True
                    break

        return color_id + str(k)

    def find_line_ending(self, line_ending_id):
        for line_ending in self.line_endings:
            if line_ending_id == line_ending['id']:
                return line_ending

        return None

    def extract_info(self, graph):
        self.reset_info()

    def extract_entity_features(self):
        # compartments
        for compartment in self.compartments:
            self.extract_compartment_features(compartment)

        # species
        for species in self.species:
            self.extract_species_features(species)

        # reactions
        for reaction in self.reactions:
            self.extract_reaction_features(reaction)

            # species references
            if 'speciesReferences' in list(reaction.keys()):
                species_references = reaction['speciesReferences']
                for species_reference in species_references:
                    self.extract_species_reference_features(species_reference)

        # line endings
        for line_ending in self.line_endings:
            self.extract_line_ending_features(line_ending)

        # colors
        for color in self.colors:
            self.extract_color_features(color)

        # gradients
        for gradient in self.gradients:
            self.extract_gradient_features(gradient)


class SBMLGraphInfoImportFromSBMLModel(SBMLGraphInfoImportBase):
    def __init__(self):
        super().__init__()
        self.is_layout_modified = False

    def extract_info(self, graph):
        super().extract_info(graph)

        sbml_document = sbne.ne_doc_readSBML(graph)
        if sbml_document:
            li = sbne.ne_doc_processLayoutInfo(sbml_document)
            network = sbne.ne_li_getNetwork(li)
            if network:
                # if layout is not specified
                if not sbne.ne_net_isLayoutSpecified(network):
                    # implement layout algorithm
                    sbne.ne_li_addLayoutFeaturesToNetowrk(li)
                    # set its flag to modified
                    self.is_layout_modified = True
                # extract layout package info
                self.extract_layout_package_info(network)

                # render package info
                ri = sbne.ne_doc_processRenderInfo(sbml_document)
                veneer = sbne.ne_ri_getVeneer(ri)
                # if render package is not specified
                if not sbne.ne_ven_isRenderSpecified(veneer):
                    # implement render algorithm
                    sbne.ne_ri_addDefaultRenderFeaturesToVeneer(ri)
                # extract render package info
                self.extract_render_package_info(veneer)

                # assign the render styles to each entity
                self.assign_entity_styles(veneer)

    def extract_layout_package_info(self, network):
        if sbne.ne_net_isLayoutSpecified(network):
            # get compartments info
            for c_index in range(sbne.ne_net_getNumCompartments(network)):
                self.add_compartment(network, sbne.ne_net_getCompartment(network, c_index))

            # get species info
            for s_index in range(sbne.ne_net_getNumSpecies(network)):
                self.add_species(network, sbne.ne_net_getSpecies(network, s_index))

            # get reactions info
            for r_index in range(sbne.ne_net_getNumReactions(network)):
                self.add_reaction(network, sbne.ne_net_getReaction(network, r_index))

    def extract_render_package_info(self, veneer):
        if sbne.ne_ven_isRenderSpecified(veneer):
            # get background color
            if sbne.ne_ven_isSetBackgroundColor:
                self.background_color = sbne.ne_ven_getBackgroundColor(veneer)

            # get colors info
            for c_index in range(sbne.ne_ven_getNumColors(veneer)):
                self.add_color(sbne.ne_ven_getColor(veneer, c_index))

            # get gradients info
            for g_index in range(sbne.ne_ven_getNumGradients(veneer)):
                self.add_gradient(sbne.ne_ven_getGradient(veneer, g_index))

            # get line ending info
            for le_index in range(sbne.ne_ven_getNumLineEndings(veneer)):
                self.add_line_ending(sbne.ne_ven_getLineEnding(veneer, le_index))

    def extract_extents(self, bounding_box):
        self.extents['minX'] = 0.0
        self.extents['maxX'] = max(self.extents['maxX'], bounding_box['x'] + bounding_box['width'])
        self.extents['minY'] = 0.0
        self.extents['maxY'] = max(self.extents['maxY'], bounding_box['y'] + bounding_box['height'])

    def add_compartment(self, network, compartment_object):
        if sbne.ne_go_isSetGlyphId(compartment_object):
            compartment = self.extract_go_object_features(network, compartment_object)
            self.compartments.append(compartment)

    def add_species(self, network, species_object):
        if sbne.ne_go_isSetGlyphId(species_object):
            species = self.extract_go_object_features(network, species_object)

            # set the compartment
            s_compartment = sbne.ne_spc_getCompartment(species_object)
            if s_compartment:
                for c in self.compartments:
                    if s_compartment == c['referenceId']:
                        species['compartment'] = c['referenceId']
                        break

            self.species.append(species)

    def add_reaction(self, network, reaction_object):
        if sbne.ne_go_isSetGlyphId(reaction_object):
            reaction = self.extract_go_object_features(network, reaction_object)

            # set the compartment
            r_compartment = sbne.ne_rxn_findCompartment(reaction_object)
            if r_compartment:
                for c in self.compartments:
                    if r_compartment == c['referenceId']:
                        reaction['compartment'] = c['referenceId']
                        break

            # species references
            reaction['speciesReferences'] = []
            for sr_index in range(sbne.ne_rxn_getNumSpeciesReferences(reaction_object)):
                species_reference_object = sbne.ne_rxn_getSpeciesReference(reaction_object, sr_index)
                if sbne.ne_go_isSetGlyphId(species_reference_object):
                    species_reference = self.extract_go_object_features(network, species_reference_object)
                    if sbne.ne_sr_isSetSpecies(species_reference_object):
                        species_reference['species'] = sbne.ne_ne_getId(sbne.ne_sr_getSpecies(species_reference_object))
                        species_reference['speciesGlyph'] = \
                            sbne.ne_go_getGlyphId(sbne.ne_sr_getSpecies(species_reference_object))
                    if sbne.ne_sr_isSetRole(species_reference_object):
                        species_reference['role'] = sbne.ne_sr_getRoleAsString(species_reference_object)
                    reaction['speciesReferences'].append(species_reference)

            self.reactions.append(reaction)

    def add_color(self, color_object):
        color_ = {}
        if sbne.ne_ve_isSetId(color_object):
            color_['colorDefinition'] = color_object
            color_['id'] = sbne.ne_ve_getId(color_object)
            self.colors.append(color_)

    def add_gradient(self, gradient_object):
        gradient_ = {}
        if sbne.ne_ve_isSetId(gradient_object):
            gradient_['gradientBase'] = gradient_object
            gradient_['id'] = sbne.ne_ve_getId(gradient_object)
            self.gradients.append(gradient_)

    def add_line_ending(self, line_ending_object):
        line_ending_ = {}
        if sbne.ne_ve_isSetId(line_ending_object):
            line_ending_['lineEnding'] = line_ending_object
            line_ending_['id'] = sbne.ne_ve_getId(line_ending_object)
            self.line_endings.append(line_ending_)

    def assign_entity_styles(self, veneer):
        # get compartments style from veneer
        for compartment in self.compartments:
            compartment['style'] = sbne.ne_ven_findStyle(veneer, compartment['glyphObject'])

            # get compartment text style from veneer
            if 'texts' in list(compartment.keys()):
                for text in compartment['texts']:
                    if 'glyphObject' in list(text.keys()):
                        text['style'] = sbne.ne_ven_findStyle(veneer, text['glyphObject'], sbne.ST_TYPE_COMP)

        # get species style from veneer
        for species in self.species:
            species['style'] = sbne.ne_ven_findStyle(veneer, species['glyphObject'])

            # get species text style from veneer
            if 'texts' in list(species.keys()):
                for text in species['texts']:
                    if 'glyphObject' in list(text.keys()):
                        text['style'] = sbne.ne_ven_findStyle(veneer, text['glyphObject'], sbne.ST_TYPE_TXT)

        # get reactions style from veneer
        for reaction in self.reactions:
            reaction['style'] = sbne.ne_ven_findStyle(veneer, reaction['glyphObject'])

            # get reaction text style from veneer
            if 'texts' in list(reaction.keys()):
                for text in reaction['texts']:
                    if 'glyphObject' in list(text.keys()):
                        text['style'] = sbne.ne_ven_findStyle(veneer, text['glyphObject'], sbne.ST_TYPE_TXT)

            # get species references style from veneer
            if 'speciesReferences' in list(reaction.keys()):
                for species_reference in reaction['speciesReferences']:
                    species_reference['style'] = sbne.ne_ven_findStyle(veneer,
                                                                       species_reference['glyphObject'])

    def extract_go_object_features(self, network, go_object):
        features = {'glyphObject': go_object, 'referenceId': sbne.ne_ne_getId(go_object),
                    'id': sbne.ne_go_getGlyphId(go_object)}
        if sbne.ne_ne_isSetMetaId(go_object):
            features['metaId'] = sbne.ne_ne_getMetaId(go_object)
        # text
        features['texts'] = []
        for text_index in range(sbne.ne_go_getNumTexts(go_object)):
            text_object = sbne.ne_go_getText(go_object, text_index)
            if sbne.ne_go_isSetGlyphId(text_object):
                features['texts'].append(self.extract_text_object_features(network, text_object))
        return features

    @staticmethod
    def extract_text_object_features(network, text_object):
        text = {'glyphObject': text_object, 'id': sbne.ne_go_getGlyphId(text_object)}
        if sbne.ne_gtxt_isSetGraphicalObjectId(text_object):
            text['graphicalObject'] = \
                sbne.ne_net_getNetworkElement(network,
                                              sbne.ne_gtxt_getGraphicalObjectId(text_object))
        elif sbne.ne_gtxt_isSetOriginOfTextId(text_object):
            text['graphicalObject'] = \
                sbne.ne_net_getNetworkElement(network,
                                              sbne.ne_gtxt_getOriginOfTextId(text_object))
        return text

    def extract_compartment_features(self, compartment):
        compartment['features'] = self.extract_go_general_features(compartment)
        if compartment['glyphObject'] and sbne.ne_go_isSetBoundingBox(compartment['glyphObject']):
            self.extract_extents(compartment['features']['boundingBox'])

    def extract_species_features(self, species):
        species['features'] = self.extract_go_general_features(species)
        if species['glyphObject'] and 'text' in list(species.keys()) and self.is_layout_modified:
            self.fit_text_to_bbox(species['text']['features'])

    def extract_reaction_features(self, reaction):
        reaction['features'] = self.extract_go_general_features(reaction)
        if reaction['glyphObject']:
            # get curve features
            if sbne.ne_rxn_isSetCurve(reaction['glyphObject']):
                crv = sbne.ne_rxn_getCurve(reaction['glyphObject'])

                if sbne.ne_crv_getNumElements(crv):
                    curve_ = []
                    for e_index in range(sbne.ne_crv_getNumElements(crv)):
                        element = sbne.ne_crv_getElement(crv, e_index)
                        start_point = sbne.ne_ls_getStart(element)
                        end_point = sbne.ne_ls_getEnd(element)
                        if start_point and end_point:
                            element_ = {'startX': sbne.ne_point_getX(start_point),
                                        'startY': sbne.ne_point_getY(start_point),
                                        'endX': sbne.ne_point_getX(end_point),
                                        'endY': sbne.ne_point_getY(end_point)}
                            if sbne.ne_ls_isCubicBezier(element):
                                base_point1 = sbne.ne_cb_getBasePoint1(element)
                                base_point2 = sbne.ne_cb_getBasePoint2(element)
                                if base_point1 and base_point2:
                                    element_["basePoint1X"] = sbne.ne_point_getX(base_point1)
                                    element_["basePoint1Y"] = sbne.ne_point_getY(base_point1)
                                    element_["basePoint2X"] = sbne.ne_point_getX(base_point2)
                                    element_["basePoint1Y"] = sbne.ne_point_getY(base_point2)
                            curve_.append(element_)
                    reaction['features']['curve'] = curve_

                    # get extent box
                    bbox = sbne.ne_rxn_getExtentBox(reaction['glyphObject'])
                    if bbox:
                        reaction['features']['boundingBox'] = {
                            'x': sbne.ne_bb_getX(bbox) + 0.5 * sbne.ne_bb_getWidth(bbox),
                            'y': sbne.ne_bb_getY(bbox) + 0.5 * sbne.ne_bb_getHeight(bbox),
                            'width': 15.0,
                            'height': 15.0}

            # get group features
            if 'style' in list(reaction.keys()) and sbne.ne_stl_isSetGroup(reaction['style']):
                if 'curve' in list(reaction['features'].keys()):
                    reaction['features']['graphicalCurve'] = \
                        self.extract_curve_features(sbne.ne_stl_getGroup(reaction['style']))

    def extract_species_reference_features(self, species_reference):
        species_reference['features'] = {}
        if species_reference['glyphObject']:
            # get curve features
            if sbne.ne_sr_isSetCurve(species_reference['glyphObject']):
                crv = sbne.ne_sr_getCurve(species_reference['glyphObject'])

                if sbne.ne_crv_getNumElements(crv):
                    curve_ = []
                    for e_index in range(sbne.ne_crv_getNumElements(crv)):
                        element = sbne.ne_crv_getElement(crv, e_index)
                        start_point = sbne.ne_ls_getStart(element)
                        end_point = sbne.ne_ls_getEnd(element)
                        if start_point and end_point:
                            element_ = {'startX': sbne.ne_point_getX(start_point),
                                        'startY': sbne.ne_point_getY(start_point),
                                        'endX': sbne.ne_point_getX(end_point),
                                        'endY': sbne.ne_point_getY(end_point)}
                            if sbne.ne_ls_isCubicBezier(element):
                                base_point1 = sbne.ne_cb_getBasePoint1(element)
                                base_point2 = sbne.ne_cb_getBasePoint2(element)
                                if base_point1 and base_point2:
                                    element_['basePoint1X'] = sbne.ne_point_getX(base_point1)
                                    element_['basePoint1Y'] = sbne.ne_point_getY(base_point1)
                                    element_['basePoint2X'] = sbne.ne_point_getX(base_point2)
                                    element_['basePoint2Y'] = sbne.ne_point_getY(base_point2)

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
                            if e_index == sbne.ne_crv_getNumElements(crv) - 1:
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
            if 'style' in list(species_reference.keys()) and sbne.ne_stl_isSetGroup(species_reference['style']):
                species_reference['features']['graphicalCurve'] = \
                    self.extract_curve_features(sbne.ne_stl_getGroup(species_reference['style']))

    def extract_go_general_features(self, go):
        features = {}
        if go['glyphObject']:
            # get bounding box features
            if sbne.ne_go_isSetBoundingBox(go['glyphObject']):
                features['boundingBox'] = self.extract_bounding_box_features(go['glyphObject'])

            # get group features
            if 'style' in list(go.keys()) and sbne.ne_stl_isSetGroup(go['style']):
                features['graphicalShape'] = \
                    self.extract_graphical_shape_features(sbne.ne_stl_getGroup(go['style']))

            # get text features
            if 'texts' in list(go.keys()):
                for text in go['texts']:
                    text['features'] = self.extract_go_text_features(text)
        return features

    def extract_go_text_features(self, text):
        text_features = {}
        # get plain text
        if sbne.ne_gtxt_isSetPlainText(text['glyphObject']):
            text_features['plainText'] = sbne.ne_gtxt_getPlainText(text['glyphObject'])
        elif 'graphicalObject' in list(text.keys()):
            if sbne.ne_ne_isSetName(text['graphicalObject']):
                text_features['plainText'] = sbne.ne_ne_getName(text['graphicalObject'])
            else:
                text_features['plainText'] = sbne.ne_ne_getId(text['graphicalObject'])
        # get bounding box features of the text glyph
        if sbne.ne_go_isSetBoundingBox(text['glyphObject']):
            text_features['boundingBox'] = self.extract_bounding_box_features(text['glyphObject'])

        # get group features
        if 'style' in list(text.keys()) \
                and sbne.ne_stl_isSetGroup(text['style']):
            text_features['graphicalText'] = self.extract_text_features(sbne.ne_stl_getGroup(text['style']))
        return text_features

    @staticmethod
    def extract_color_features(color):
        color['features'] = {}
        if color['colorDefinition']:
            # get color value
            if sbne.ne_clr_isSetValue(color['colorDefinition']):
                color['features']['value'] = sbne.ne_clr_getValue(color['colorDefinition'])

    @staticmethod
    def extract_gradient_features(gradient):
        gradient['features'] = {}
        if gradient['gradientBase']:
            # get spread method
            if sbne.ne_grd_isSetSpreadMethod(gradient['gradientBase']):
                gradient['features']['spreadMethod'] = sbne.ne_grd_getSpreadMethod(gradient['gradientBase'])

            # get gradient stops
            stops_ = []
            for s_index in range(sbne.ne_grd_getNumStops(gradient['gradientBase'])):
                stop_ = {'gradientStop': sbne.ne_grd_getStop(gradient['gradientBase'], s_index)}

                # get offset
                if sbne.ne_gstp_isSetOffset(stop_['gradientStop']):
                    stop_['offset'] = \
                        {'abs': 0, 'rel': sbne.ne_rav_getRelativeValue(sbne.ne_gstp_getOffset(stop_['gradientStop']))}

                # get stop color
                if sbne.ne_gstp_isSetColor(stop_['gradientStop']):
                    stop_['color'] = sbne.ne_gstp_getColor(stop_['gradientStop'])

                stops_.append(stop_)

            gradient['features']['stops'] = stops_

            # for linear gradient
            if sbne.ne_grd_isLinearGradient(gradient['gradientBase']):
                # get start
                gradient['features']['start'] = \
                    {'x': {'abs':
                               sbne.ne_rav_getAbsoluteValue(sbne.ne_grd_getX1(gradient['gradientBase'])),
                           'rel':
                               sbne.ne_rav_getRelativeValue(sbne.ne_grd_getX1(gradient['gradientBase']))},
                     'y': {'abs':
                               sbne.ne_rav_getAbsoluteValue(sbne.ne_grd_getY1(gradient['gradientBase'])),
                           'rel':
                               sbne.ne_rav_getRelativeValue(sbne.ne_grd_getY1(gradient['gradientBase']))}}

                # get end
                gradient['features']['end'] = \
                    {'x': {'abs':
                               sbne.ne_rav_getAbsoluteValue(sbne.ne_grd_getX2(gradient['gradientBase'])),
                           'rel':
                               sbne.ne_rav_getRelativeValue(sbne.ne_grd_getX2(gradient['gradientBase']))},
                     'y': {'abs':
                               sbne.ne_rav_getAbsoluteValue(sbne.ne_grd_getY2(gradient['gradientBase'])),
                           'rel':
                               sbne.ne_rav_getRelativeValue(sbne.ne_grd_getY2(gradient['gradientBase']))}}

            # for radial gradient
            elif sbne.ne_grd_isLinearGradient(gradient['gradientBase']):
                # get center
                gradient['features']['center'] = \
                    {'x': {'abs':
                               sbne.ne_rav_getAbsoluteValue(sbne.ne_grd_getCx(gradient['gradientBase'])),
                           'rel':
                               sbne.ne_rav_getRelativeValue(sbne.ne_grd_getCx(gradient['gradientBase']))},
                     'y': {'abs':
                               sbne.ne_rav_getAbsoluteValue(sbne.ne_grd_getCy(gradient['gradientBase'])),
                           'rel':
                               sbne.ne_rav_getRelativeValue(sbne.ne_grd_getCy(gradient['gradientBase']))}}

                # get focal
                gradient['features']['focalPoint'] = \
                    {'x': {'abs':
                               sbne.ne_rav_getAbsoluteValue(sbne.ne_grd_getFx(gradient['gradientBase'])),
                           'rel':
                               sbne.ne_rav_getRelativeValue(sbne.ne_grd_getFx(gradient['gradientBase']))},
                     'y': {'abs':
                               sbne.ne_rav_getAbsoluteValue(sbne.ne_grd_getFy(gradient['gradientBase'])),
                           'rel':
                               sbne.ne_rav_getRelativeValue(sbne.ne_grd_getFy(gradient['gradientBase']))}}

                # get radius
                gradient['features']['radius'] = \
                    {'abs': sbne.ne_rav_getAbsoluteValue(sbne.ne_grd_getR(gradient['gradientBase'])),
                     'rel': sbne.ne_rav_getRelativeValue(sbne.ne_grd_getR(gradient['gradientBase']))}

    def extract_line_ending_features(self, line_ending):
        line_ending['features'] = {}
        if line_ending['lineEnding']:
            # get bounding box features
            if sbne.ne_le_isSetBoundingBox(line_ending['lineEnding']):
                bbox = sbne.ne_le_getBoundingBox(line_ending['lineEnding'])
                line_ending['features']['boundingBox'] = {'x': sbne.ne_bb_getX(bbox), 'y': sbne.ne_bb_getY(bbox),
                                                          'width': sbne.ne_bb_getWidth(bbox),
                                                          'height': sbne.ne_bb_getHeight(bbox)}

            # get group features
            if sbne.ne_le_isSetGroup(line_ending['lineEnding']):
                line_ending['features']['graphicalShape'] = \
                    self.extract_graphical_shape_features(sbne.ne_le_getGroup(line_ending['lineEnding']))

            # get enable rotation
            if sbne.ne_le_isSetEnableRotation(line_ending['lineEnding']):
                line_ending['features']['enableRotation'] = sbne.ne_le_getEnableRotation(line_ending['lineEnding'])

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
        if sbne.ne_grp_isSetStrokeColor(group):
            render_group_general_features['strokeColor'] = sbne.ne_grp_getStrokeColor(group)

        # get stroke width
        if sbne.ne_grp_isSetStrokeWidth(group):
            render_group_general_features['strokeWidth'] = sbne.ne_grp_getStrokeWidth(group)

        # get stroke dash array
        if sbne.ne_grp_isSetStrokeDashArray(group):
            dash_array = []
            for d_index in range(sbne.ne_grp_getNumStrokeDashes(group)):
                dash_array.append(sbne.ne_grp_getStrokeDash(group, d_index))
            render_group_general_features['strokeDashArray'] = tuple(dash_array)

        # get fill color
        if sbne.ne_grp_isSetFillColor(group):
            render_group_general_features['fillColor'] = sbne.ne_grp_getFillColor(group)

        # get fill rule
        if sbne.ne_grp_isSetFillRule(group):
            render_group_general_features['fillRule'] = sbne.ne_grp_getFillRule(group)
        return render_group_general_features

    def extract_render_group_geometric_shapes(self, group):
        geometric_shapes = []
        if sbne.ne_grp_getNumGeometricShapes(group):
            for gs_index in range(sbne.ne_grp_getNumGeometricShapes(group)):
                gs = sbne.ne_grp_getGeometricShape(group, gs_index)
                geometric_shape = {}
                geometric_shape.update(self.extract_geometric_shape_general_features(gs))
                geometric_shape.update(self.extract_geometric_shape_exclusive_features(gs))
                geometric_shapes.append(geometric_shape)
        return geometric_shapes

    @staticmethod
    def extract_geometric_shape_general_features(gs):
        geometric_shape_general_features = {}
        # get stroke color
        if sbne.ne_gs_isSetStrokeColor(gs):
            geometric_shape_general_features['strokeColor'] = sbne.ne_gs_getStrokeColor(gs)

        # get stroke width
        if sbne.ne_gs_isSetStrokeWidth(gs):
            geometric_shape_general_features['strokeWidth'] = sbne.ne_gs_getStrokeWidth(gs)

        # get stroke dash array
        if sbne.ne_gs_isSetStrokeDashArray(gs):
            dash_array = []
            for d_index in range(sbne.ne_gs_getNumStrokeDashes(gs)):
                dash_array.append(sbne.ne_gs_getStrokeDash(gs, d_index))
            geometric_shape_general_features['strokeDashArray'] = tuple(dash_array)
        return geometric_shape_general_features

    def extract_geometric_shape_exclusive_features(self, gs):
        if sbne.ne_gs_getShape(gs) == 0:
            return self.extract_image_shape_features(gs)
        elif sbne.ne_gs_getShape(gs) == 1:
            return self.extract_curve_shape_features(gs)
        elif sbne.ne_gs_getShape(gs) == 2:
            return self.extract_text_shape_features(gs)
        elif sbne.ne_gs_getShape(gs) == 3:
            return self.extract_rectangle_shape_features(gs)
        elif sbne.ne_gs_getShape(gs) == 4:
            return self.extract_ellipse_shape_features(gs)
        elif sbne.ne_gs_getShape(gs) == 5:
            return self.extract_polygon_shape_features(gs)

    @staticmethod
    def extract_curve_features(group):
        curve_info = {}
        if group:
            # get stroke color
            if sbne.ne_grp_isSetStrokeColor(group):
                curve_info['strokeColor'] = sbne.ne_grp_getStrokeColor(group)

            # get stroke width
            if sbne.ne_grp_isSetStrokeWidth(group):
                curve_info['strokeWidth'] = sbne.ne_grp_getStrokeWidth(group)

            # get stroke dash array
            if sbne.ne_grp_isSetStrokeDashArray(group):
                dash_array = []
                for d_index in range(sbne.ne_grp_getNumStrokeDashes(group)):
                    dash_array.append(sbne.ne_grp_getStrokeDash(group, d_index))
                curve_info['strokeDashArray'] = tuple(dash_array)

            # get heads
            heads_ = {}
            if sbne.ne_grp_isSetStartHead(group):
                heads_['start'] = sbne.ne_grp_getStartHead(group)
            if sbne.ne_grp_isSetEndHead(group):
                heads_['end'] = sbne.ne_grp_getEndHead(group)
            if heads_:
                curve_info['heads'] = heads_
        return curve_info

    @staticmethod
    def extract_text_features(group):
        text_info = {}
        if group:
            # get stroke color
            if sbne.ne_grp_isSetStrokeColor(group):
                text_info['strokeColor'] = sbne.ne_grp_getStrokeColor(group)

            # get font family
            if sbne.ne_grp_isSetFontFamily(group):
                text_info['fontFamily'] = sbne.ne_grp_getFontFamily(group)

            # get font size
            if sbne.ne_grp_isSetFontSize(group):
                rel_abs_vec = sbne.ne_grp_getFontSize(group)
                text_info['fontSize'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                         'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

            # get font weight
            if sbne.ne_grp_isSetFontWeight(group):
                text_info['fontWeight'] = sbne.ne_grp_getFontWeight(group)

            # get font style
            if sbne.ne_grp_isSetFontStyle(group):
                text_info['fontStyle'] = sbne.ne_grp_getFontStyle(group)

            # get horizontal text anchor
            if sbne.ne_grp_isSetHTextAnchor(group):
                text_info['hTextAnchor'] = sbne.ne_grp_getHTextAnchor(group)

            # get vertical text anchor
            if sbne.ne_grp_isSetVTextAnchor(group):
                text_info['vTextAnchor'] = sbne.ne_grp_getVTextAnchor(group)

            # get geometric shapes
            if sbne.ne_grp_getNumGeometricShapes(group):
                geometric_shapes = []
                for gs_index in range(sbne.ne_grp_getNumGeometricShapes(group)):
                    gs = sbne.ne_grp_getGeometricShape(group, gs_index)

                    if sbne.ne_gs_getShape(gs) == 1:
                        geometric_shape_features = {}

                        # get stroke color
                        if sbne.ne_gs_isSetStrokeColor(gs):
                            geometric_shape_features['strokeColor'] = sbne.ne_gs_getStrokeColor(gs)

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
        if sbne.ne_img_isSetPositionX(image_shape):
            rel_abs_vec = sbne.ne_img_getPositionX(image_shape)
            image_shape_info['x'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                     'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get position y
        if sbne.ne_img_isSetPositionY(image_shape):
            rel_abs_vec = sbne.ne_img_getPositionY(image_shape)
            image_shape_info['y'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                     'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension width
        if sbne.ne_img_isSetDimensionWidth(image_shape):
            rel_abs_vec = sbne.ne_img_getDimensionWidth(image_shape)
            image_shape_info['width'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                         'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension height
        if sbne.ne_img_isSetDimensionHeight(image_shape):
            rel_abs_vec = sbne.ne_img_getDimensionHeight(image_shape)
            image_shape_info['height'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                          'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get href
        if sbne.ne_img_isSetHref(image_shape):
            image_shape_info['href'] = sbne.ne_img_getHref(image_shape)

        return image_shape_info

    @staticmethod
    def extract_curve_shape_features(curve_shape):
        # set shape
        curve_shape_info = {'shape': "renderCurve"}

        vertices_ = []
        for v_index in range(sbne.ne_rc_getNumVertices(curve_shape)):
            vertex = sbne.ne_rc_getVertex(curve_shape, v_index)
            vertex_ = {}
            render_point = sbne.ne_vrx_getRenderPoint(vertex)
            if render_point:
                vertex_['renderPointX'] = dict(
                    abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getX(render_point)),
                    rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getX(render_point)))
                vertex_['renderPointY'] = dict(
                    abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getY(render_point)),
                    rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getY(render_point)))
            if sbne.ne_vertex_isRenderCubicBezier(vertex):
                base_point1 = sbne.ne_vrx_getBasePoint1(vertex)
                base_point2 = sbne.ne_vrx_getBasePoint2(vertex)
                if base_point1 and base_point2:
                    vertex_['basePoint1X'] = dict(
                        abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getX(base_point1)),
                        rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getX(base_point1)))
                    vertex_['basePoint1Y'] = dict(
                        abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getY(base_point1)),
                        rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getY(base_point1)))
                    vertex_['basePoint2X'] = dict(
                        abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getX(base_point2)),
                        rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getX(base_point2)))
                    vertex_['basePoint2Y'] = dict(
                        abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getY(base_point2)),
                        rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getY(base_point2)))
            vertices_.append(vertex_)

        curve_shape_info['vertices'] = vertices_

        return curve_shape_info

    @staticmethod
    def extract_text_shape_features(text_shape):
        # set shape
        text_shape_info = {'shape': "text"}

        # get position x
        if sbne.ne_txt_isSetPositionX(text_shape):
            rel_abs_vec = sbne.ne_txt_getPositionX(text_shape)
            text_shape_info['x'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                    'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get position y
        if sbne.ne_txt_isSetPositionY(text_shape):
            rel_abs_vec = sbne.ne_txt_getPositionY(text_shape)
            text_shape_info['y'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                    'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get font family
        if sbne.ne_txt_isSetFontFamily(text_shape):
            text_shape_info['fontFamily'] = sbne.ne_txt_getFontFamily(text_shape)

        # get font size
        if sbne.ne_txt_isSetFontSize(text_shape):
            rel_abs_vec = sbne.ne_txt_getFontSize(gs)
            text_shape_info['fontSize'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                           'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get font weight
        if sbne.ne_txt_isSetFontWeight(text_shape):
            text_shape_info['fontWeight'] = sbne.ne_txt_getFontWeight(text_shape)

        # get font style
        if sbne.ne_txt_isSetFontStyle(text_shape):
            text_shape_info['fontStyle'] = sbne.ne_grp_getFontStyle(text_shape)

        # get horizontal text anchor
        if sbne.ne_txt_isSetHTextAnchor(text_shape):
            text_shape_info['hTextAnchor'] = sbne.ne_txt_getHTextAnchor(text_shape)

        # get vertical text anchor
        if sbne.ne_txt_isSetVTextAnchor(text_shape):
            text_shape_info['vTextAnchor'] = sbne.ne_txt_getVTextAnchor(text_shape)

        return text_shape_info

    @staticmethod
    def extract_rectangle_shape_features(rectangle_shape):
        # set shape
        rectangle_shape_info = {'shape': "rectangle"}

        # get fill color
        if sbne.ne_gs_isSetFillColor(rectangle_shape):
            rectangle_shape_info['fillColor'] = sbne.ne_gs_getFillColor(rectangle_shape)

        # get position x
        if sbne.ne_rec_isSetPositionX(rectangle_shape):
            rel_abs_vec = sbne.ne_rec_getPositionX(rectangle_shape)
            rectangle_shape_info['x'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                         'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get position y
        if sbne.ne_rec_isSetPositionY(rectangle_shape):
            rel_abs_vec = sbne.ne_rec_getPositionY(rectangle_shape)
            rectangle_shape_info['y'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                         'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension width
        if sbne.ne_rec_isSetDimensionWidth(rectangle_shape):
            rel_abs_vec = sbne.ne_rec_getDimensionWidth(rectangle_shape)
            rectangle_shape_info['width'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                             'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension height
        if sbne.ne_rec_isSetDimensionHeight(rectangle_shape):
            rel_abs_vec = sbne.ne_rec_getDimensionHeight(rectangle_shape)
            rectangle_shape_info['height'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                              'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get corner curvature radius rx
        if sbne.ne_rec_isSetCornerCurvatureRX(rectangle_shape):
            rel_abs_vec = sbne.ne_rec_getCornerCurvatureRX(rectangle_shape)
            rectangle_shape_info['rx'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                          'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get corner curvature radius ry
        if sbne.ne_rec_isSetCornerCurvatureRY(rectangle_shape):
            rel_abs_vec = sbne.ne_rec_getCornerCurvatureRY(rectangle_shape)
            rectangle_shape_info['ry'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                          'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get width/height ratio
        if sbne.ne_rec_isSetRatio(rectangle_shape):
            rectangle_shape_info['ratio'] = sbne.ne_rec_getRatio(rectangle_shape)

        return rectangle_shape_info

    @staticmethod
    def extract_ellipse_shape_features(ellipse_shape):
        # set shape
        ellipse_shape_info = {'shape': "ellipse"}

        # get fill color
        if sbne.ne_gs_isSetFillColor(ellipse_shape):
            ellipse_shape_info['fillColor'] = sbne.ne_gs_getFillColor(ellipse_shape)

        # get position cx
        if sbne.ne_elp_isSetPositionCX(ellipse_shape):
            rel_abs_vec = sbne.ne_elp_getPositionCX(ellipse_shape)
            ellipse_shape_info['cx'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                        'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get position cy
        if sbne.ne_elp_isSetPositionCY(ellipse_shape):
            rel_abs_vec = sbne.ne_elp_getPositionCY(ellipse_shape)
            ellipse_shape_info['cy'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                        'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension rx
        if sbne.ne_elp_isSetDimensionRX(ellipse_shape):
            rel_abs_vec = sbne.ne_elp_getDimensionRX(ellipse_shape)
            ellipse_shape_info['rx'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                        'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension ry
        if sbne.ne_elp_isSetDimensionRY(ellipse_shape):
            rel_abs_vec = sbne.ne_elp_getDimensionRY(ellipse_shape)
            ellipse_shape_info['ry'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                        'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get radius ratio
        if sbne.ne_elp_isSetRatio(ellipse_shape):
            ellipse_shape_info['ratio'] = sbne.ne_elp_getRatio(ellipse_shape)

        return ellipse_shape_info

    @staticmethod
    def extract_polygon_shape_features(polygon_shape):
        # set shape
        polygon_shape_info = {'shape': "polygon"}

        # get fill color
        if sbne.ne_gs_isSetFillColor(polygon_shape):
            polygon_shape_info['fillColor'] = sbne.ne_gs_getFillColor(polygon_shape)

        # get fill rule
        if sbne.ne_gs_isSetFillRule(polygon_shape):
            polygon_shape_info['fillRule'] = sbne.ne_gs_getFillRule(polygon_shape)

        vertices_ = []
        for v_index in range(sbne.ne_plg_getNumVertices(polygon_shape)):
            vertex = sbne.ne_plg_getVertex(polygon_shape, v_index)
            vertex_ = {}
            render_point = sbne.ne_vrx_getRenderPoint(vertex)
            if render_point:
                vertex_['renderPointX'] = dict(
                    abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getX(render_point)),
                    rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getX(render_point)))
                vertex_['renderPointY'] = dict(
                    abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getY(render_point)),
                    rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getY(render_point)))
            if sbne.ne_vrx_isRenderCubicBezier(vertex):
                base_point1 = sbne.ne_vrx_getBasePoint1(vertex)
                base_point2 = sbne.ne_vrx_getBasePoint2(vertex)
                if base_point1 and base_point2:
                    vertex_['basePoint1X'] = dict(
                        abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getX(base_point1)),
                        rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getX(base_point1)))
                    vertex_['basePoint1Y'] = dict(
                        abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getY(base_point1)),
                        rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getY(base_point1)))
                    vertex_['basePoint2X'] = dict(
                        abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getX(base_point2)),
                        rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getX(base_point2)))
                    vertex_['basePoint2Y'] = dict(
                        abs=sbne.ne_rav_getAbsoluteValue(sbne.ne_rp_getY(base_point2)),
                        rel=sbne.ne_rav_getRelativeValue(sbne.ne_rp_getY(base_point2)))
            vertices_.append(vertex_)

        polygon_shape_info['vertices'] = vertices_

        return polygon_shape_info

    @staticmethod
    def extract_bounding_box_features(glyph_object):
        bounding_box = {}
        if sbne.ne_go_isSetBoundingBox(glyph_object):
            bbox = sbne.ne_go_getBoundingBox(glyph_object)
            bounding_box = {'x': sbne.ne_bb_getX(bbox), 'y': sbne.ne_bb_getY(bbox),
                            'width': sbne.ne_bb_getWidth(bbox),
                            'height': sbne.ne_bb_getHeight(bbox)}
        return bounding_box

    @staticmethod
    def fit_text_to_bbox(text_features):
        if 'boundingBox' in list(text_features.keys()) \
                and 'plainText' in list(text_features.keys()) \
                and 'graphicalText' in list(text_features.keys()) \
                and 'fontFamily' in list(text_features['graphicalText'].keys()) \
                and 'fontSize' in list(text_features['graphicalText'].keys()):
            fp = FontProperties(family=text_features['graphicalText']['fontFamily'],
                                size=text_features['graphicalText']['fontSize']['abs']
                                     + 0.01 * text_features['graphicalText']['fontSize']['rel']
                                     * text_features['boundingBox']['width'])
            text_width, text_height, text_descent = TextToPath().get_text_width_height_descent(
                s=text_features['plainText'],
                prop=fp, ismath=False)
            char_width = text_width / len(text_features['plainText'])
            if text_width > text_features['boundingBox']['width'] - char_width:
                while text_width > text_features['boundingBox']['width'] - char_width:
                    text_features['plainText'] = text_features['plainText'][:-1]
                    text_width -= char_width
                text_features['plainText'] += "."


class SBMLGraphInfoImportFromNetworkEditor(SBMLGraphInfoImportBase):
    def __init__(self):
        super().__init__()

    def extract_info(self, graph_info):
        super().extract_info(graph_info)
        self.extract_extents(graph_info)
        self.extract_entities(graph_info)

    def extract_extents(self, graph_info):
        if 'background-color' in list(graph_info.keys()):
            self.background_color = graph_info['background-color']
        if 'position' in list(graph_info.keys()):
            if 'x' in list(graph_info['position'].keys()):
                self.extents['minX'] = graph_info['position']['x']
            if 'y' in list(graph_info['position'].keys()):
                self.extents['minY'] = graph_info['position']['y']
        if 'dimensions' in list(graph_info.keys()):
            if 'width' in list(graph_info['dimensions'].keys()):
                self.extents['minX'] -= 0.5 * graph_info['dimensions']['width']
                self.extents['maxX'] = self.extents['minX'] + graph_info['dimensions']['width']
            if 'height' in list(graph_info['dimensions'].keys()):
                self.extents['minY'] -= 0.5 * graph_info['dimensions']['height']
                self.extents['maxY'] = self.extents['minY'] + graph_info['dimensions']['height']

    def extract_entities(self, graph_info):
        if 'nodes' in list(graph_info.keys()):
            for node in graph_info['nodes']:
                if 'style' in list(node.keys()) and 'category' in list(node['style'].keys()):
                    if node['style']['category'].lower() == "compartment":
                        self.add_compartment(node)
                    elif node['style']['category'].lower() == "species":
                        self.add_species(node)
                    elif node['style']['category'].lower() == "reaction":
                        self.add_reaction(node, graph_info)

    def add_compartment(self, compartment_info):
        compartment_ = {}
        if 'id' in list(compartment_info.keys()):
            compartment_['info'] = compartment_info
            compartment_['id'] = compartment_info['id'] + "_glyph"
            compartment_['referenceId'] = compartment_info['id']
            self.compartments.append(compartment_)

    def add_species(self, species_info):
        species_ = {}
        if 'id' in list(species_info.keys()):
            species_['info'] = species_info
            species_['id'] = species_info['id'] + "_glyph"
            species_['referenceId'] = species_info['id']
            self.species.append(species_)

    def add_reaction(self, reaction_info, graph_info):
        reaction_ = {}
        if 'id' in list(reaction_info.keys()):
            reaction_['info'] = reaction_info
            reaction_['id'] = reaction_info['id'] + "_glyph"
            reaction_['referenceId'] = reaction_info['id']

            reaction_['speciesReferences'] = []
            if 'edges' in list(graph_info.keys()):
                for edge in graph_info['edges']:
                    if ('source' in list(edge.keys()) and
                        'node' in list(edge['source'].keys()) and
                        edge['source']['node'] == reaction_['referenceId']) or \
                            ('target' in list(edge.keys()) and
                             'node' in list(edge['target'].keys()) and
                             edge['target']['node'] == reaction_['referenceId']):
                        self.add_species_reference(reaction_['speciesReferences'], edge)
            self.reactions.append(reaction_)

    @staticmethod
    def add_species_reference(species_references, species_reference_info):
        species_reference_ = {}
        if 'id' in list(species_reference_info.keys()):
            species_reference_['info'] = species_reference_info
            species_reference_['id'] = species_reference_info['id'] + "_glyph"
            species_reference_['referenceId'] = species_reference_info['id']
            species_references.append(species_reference_)

    @staticmethod
    def add_text(node, text_shape):
        if "plain-text" in list(text_shape.keys()):
            node['texts'].append({'id': node['id'] + "_" + text_shape['plain-text'] + "_text",
                            'plain-text': text_shape['plain-text'], 'info': text_shape})

    def add_color(self, color):
        if not self.find_color(color):
            self.colors.append({'id': color})

    def add_line_ending(self, line_ending):
        if 'name' in list(line_ending.keys()) and not self.find_line_ending(line_ending['name']) and \
                'shapes' in list(line_ending.keys()) and len(line_ending['shapes']):
            self.line_endings.append({'id': line_ending['name'], 'info': line_ending})

    def extract_compartment_features(self, compartment):
        self.extract_node_features(compartment)

    def extract_species_features(self, species):
        if 'parent' in list(species['info'].keys()):
            species['compartment'] = species['info']['parent']
        self.extract_node_features(species)

    def extract_reaction_features(self, reaction):
        if 'parent' in list(reaction['info'].keys()):
            reaction['compartment'] = reaction['info']['parent']
        if self.is_centroid_node(reaction):
            self.extract_centroid_node_features(reaction)
        else:
            self.extract_node_features(reaction)

    def extract_species_reference_features(self, species_reference):
        if 'style' in list(species_reference['info'].keys()) and\
                'sub-category' in list(species_reference['info']['style'].keys()):
            species_reference['role'] = species_reference['info']['style']['sub-category']
        self.extract_edge_features(species_reference)

    def extract_color_features(self, color):
        if color['id']:
            if color['id'].startswith("#"):
                color['features'] = {}
                color['features']['value'] = color['id']
                color['id'] = self.find_color_unique_id()
            elif 'features' not in list(color.keys()) or 'value' not in list(color['features'].keys()):
                color['features'] = {}
                try:
                    color['features']['value'] = webcolors.name_to_hex(color['id'])
                except:
                    color['features']['value'] = webcolors.name_to_hex("white")

    def extract_line_ending_features(self, line_ending):
        line_ending['features'] = {}

        # get bounding box features
        line_ending['features']['boundingBox'] = self.get_bounding_box_features(line_ending['info'])
        offset_x = line_ending['features']['boundingBox']['width']
        offset_y = 0.5 * line_ending['features']['boundingBox']['height']

        # get features
        if 'shapes' in list(line_ending['info'].keys()):
            line_ending['features']['graphicalShape'] = \
                self.extract_graphical_shape_features(line_ending['info']['shapes'], offset_x, offset_y)

        line_ending['features']['enableRotation'] = True

    def extract_node_features(self, node):
        node['features'] = {}
        node['texts'] = []
        # get bounding box features
        node['features']['boundingBox'] = self.get_bounding_box_features(node['info'])
        offset_x = 0.5 * node['features']['boundingBox']['width']
        offset_y = 0.5 * node['features']['boundingBox']['height']

        # get style features
        if 'style' in list(node['info'].keys()):
            if 'name' in list(node['info']['style']):
                node['features']['styleName'] = node['info']['style']['name']
            if 'shapes' in list(node['info']['style']):
                node['features']['graphicalShape'] = \
                    self.extract_graphical_shape_features(node['info']['style']['shapes'], offset_x, offset_y)
                for shape in node['info']['style']['shapes']:
                    if 'shape' in list(shape.keys()) and shape['shape'].lower() == "text":
                        self.add_text(node, shape)

        # get text features
        if 'texts' in list(node.keys()):
            self.extract_text_features(node)

    def extract_centroid_node_features(self, centroid_node):
        centroid_node['features'] = {'graphicalCurve': {}, 'curve': []}
        centroid_node['texts'] = []

        # get curve features
        bounding_box = self.get_bounding_box_features(centroid_node['info'])
        centroid_node['features']['curve'] = [{'startX': bounding_box['x'] + 0.5 * bounding_box['width'],
                       'startY': bounding_box['y'] + 0.5 * bounding_box['height'],
                       'endX': bounding_box['x'] + 0.5 * bounding_box['width'],
                       'endY': bounding_box['y'] + 0.5 * bounding_box['height']}]

        # get style features
        if 'style' in list(centroid_node['info'].keys()):
            if 'name' in list(centroid_node['info']['style']):
                centroid_node['features']['styleName'] = centroid_node['info']['style']['name']
            centroid_shape = centroid_node['info']['style']['shapes'][0]
            # get stroke color
            if 'border-color' in list(centroid_shape.keys()):
                centroid_node['features']['graphicalCurve']['strokeColor'] = centroid_shape['border-color']
            # get stroke width
            if 'border-width' in list(centroid_shape.keys()):
                centroid_node['features']['graphicalCurve']['strokeWidth'] = centroid_shape['border-width']
            # get fill color
            if 'fill-color' in list(centroid_shape.keys()):
                centroid_node['features']['graphicalCurve']['fillColor'] = centroid_shape['fill-color']

    @staticmethod
    def is_centroid_node(node):
        if 'style' in list(node['info'].keys()) \
                and 'shapes' in list(node['info']['style'].keys()) \
                and len(node['info']['style']['shapes']) == 1 \
                and 'shape' in list(node['info']['style']['shapes'][0].keys()) \
                and node['info']['style']['shapes'][0]['shape'] == "centroid":
            return True

        return False

    def extract_edge_features(self, edge):
        edge['features'] = {}
        if 'source' in list(edge['info'].keys()):
            if 'node' in list(edge['info']['source'].keys()):
                if self.find_species(edge['info']['source']['node']):
                    edge['species'] = edge['info']['source']['node']
                    edge['speciesGlyph'] = edge['info']['source']['node'] + "_glyph"
                elif self.find_reaction(edge['info']['source']['node']):
                    edge['reaction'] = edge['info']['source']['node']
                    edge['reactionGlyph'] = edge['info']['source']['node'] + "_glyph"
            if 'position' in list(edge['info']['source'].keys()):
                edge['features']['startPoint'] = edge['info']['source']['position']
        if 'target' in list(edge['info'].keys()):
            if 'node' in list(edge['info']['target'].keys()):
                if self.find_species(edge['info']['target']['node']):
                    edge['species'] = edge['info']['target']['node']
                    edge['speciesGlyph'] = edge['info']['target']['node'] + "_glyph"
                elif self.find_reaction(edge['info']['target']['node']):
                    edge['reaction'] = edge['info']['target']['node']
                    edge['reaction'] = edge['info']['target']['node'] + "_glyph"
            if 'position' in list(edge['info']['target'].keys()):
                edge['features']['endPoint'] = edge['info']['target']['position']

        curve_ = []
        if 'x' in list(edge['features']['startPoint'].keys()) and \
                'y' in list(edge['features']['startPoint'].keys()) and \
                'x' in list(edge['features']['endPoint'].keys()) and \
                'y' in list(edge['features']['endPoint'].keys()):
            edge['features']['startSlope'] = math.atan2(
                edge['features']['startPoint']['y'] - edge['features']['endPoint']['y'],
                edge['features']['startPoint']['x'] - edge['features']['endPoint']['x'])
            edge['features']['endSlope'] = math.atan2(
                edge['features']['endPoint']['y'] - edge['features']['startPoint']['y'],
                edge['features']['endPoint']['x'] - edge['features']['startPoint']['x'])
            curve_.append({'startX': edge['features']['startPoint']['x'],
                           'startY': edge['features']['startPoint']['y'],
                           'endX': edge['features']['endPoint']['x'],
                           'endY': edge['features']['endPoint']['y']})
        edge['features']['curve'] = curve_

        # get style features
        if 'style' in list(edge['info'].keys()):
            if 'name' in list(edge['info']['style']):
                edge['features']['styleName'] = edge['info']['style']['name']
            if 'shapes' in list(edge['info']['style']) and len(edge['info']['style']['shapes']):
                edge['features']['graphicalCurve'] = \
                    self.extract_curve_features(edge['info']['style']['shapes'][0], edge['features']['curve'])
                if 'arrow-head' in list(edge['info']['style']):
                    if 'name' in list(edge['info']['style']['arrow-head'].keys()):
                        edge['features']['graphicalCurve']['heads'] = {
                            'end': edge['info']['style']['arrow-head']['name']}
                    self.add_line_ending(edge['info']['style']['arrow-head'])

    def extract_graphical_shape_features(self, shapes, offset_x=0, offset_y=0):
        graphical_shape_info = {'geometricShapes': []}

        for shape in list(shapes):
            if 'shape' in list(shape.keys()):
                # get geometric shape specific features
                geometric_shape_info = self.extract_geometric_shape_exclusive_features(shape, offset_x, offset_y)

                # get stroke color
                if 'border-color' in list(shape.keys()):
                    geometric_shape_info['strokeColor'] = shape['border-color']
                    self.add_color(shape['border-color'])

                # get stroke width
                if 'border-width' in list(shape.keys()):
                    geometric_shape_info['strokeWidth'] = shape['border-width']

                if 'shape' in list(geometric_shape_info.keys()):
                    graphical_shape_info['geometricShapes'].append(geometric_shape_info)

        return graphical_shape_info

    def extract_curve_features(self, shape, curve):
        curve_info = {}
        if 'shape' in list(shape.keys()) and (shape['shape'].lower() == "line" or \
                                              shape['shape'].lower() == "connected-to-source-centroid-shape-line" or \
                                              shape['shape'].lower() == "connected-to-target-centroid-shape-line"):
            # get stroke color
            if 'border-color' in list(shape.keys()):
                curve_info['strokeColor'] = shape['border-color']
                self.add_color(shape['border-color'])
            # get stroke width
            if 'border-width' in list(shape.keys()):
                curve_info['strokeWidth'] = shape['border-width']

            # get bezier features
            if len(curve):
                element = curve[0]
                if 'p1' in list(shape.keys()) and \
                        'x' in list(shape['p1'].keys()) and 'y' in list(shape['p1'].keys()) and\
                        'p2' in list(shape.keys()) and \
                        'x' in list(shape['p2'].keys()) and 'y' in list(shape['p2'].keys()):
                    if shape['p1']['x'] > 0.0 or shape['p1']['y'] or shape['p2']['x'] or shape['p2']['y']:
                        element['basePoint1X'] = element['startX'] + 0.01 * shape['p1']['x'] *\
                                                 (element['endX'] - element['startX'])
                        element['basePoint1Y'] = element['startY'] + 0.01 * shape['p1']['y'] *\
                                                 (element['endY'] - element['startY'])
                        element['basePoint2X'] = element['endX'] + 0.01 * shape['p2']['x'] *\
                                                 (element['endX'] - element['startX'])
                        element['basePoint2Y'] = element['endY'] + 0.01 * shape['p2']['y'] *\
                                                 (element['endY'] - element['startY'])

        return curve_info

    def extract_text_features(self, node):
        for text in node['texts']:
            text['features'] = {}
            # get plain text
            text['features']['plainText'] = text['plain-text']
            # get bounding box features of the text glyph
            text['features']['boundingBox'] = dict(x=node['features']['boundingBox']['x'],
                                                           y=node['features']['boundingBox']['y'],
                                                           width=node['features']['boundingBox']['width'],
                                                           height=node['features']['boundingBox']['height'])
            graphical_text_info = {}
            if 'shape' in list(text['info'].keys()) and text['info']['shape'].lower() == "text":
                # get stroke color
                if 'color' in list(text['info'].keys()):
                    graphical_text_info['strokeColor'] = text['info']['color']
                    self.add_color(text['info']['color'])

                # get position x
                if 'x' in list(text['info'].keys()):
                    text['features']['boundingBox']['x'] = text['info']['x'] +\
                                                           text['features']['boundingBox']['x'] +\
                                                           0.5 * text['features']['boundingBox']['width']

                # get position y
                if 'y' in list(text['info'].keys()):
                    text['features']['boundingBox']['y'] = text['info']['y'] +\
                                                           text['features']['boundingBox']['y'] +\
                                                           0.5 * text['features']['boundingBox']['height']

                # get dimension width
                if 'width' in list(text['info'].keys()):
                    text['features']['boundingBox']['width'] = text['info']['width']

                # get dimension width
                if 'height' in list(text['info'].keys()):
                    text['features']['boundingBox']['height'] = text['info']['height']

                # get font family
                if 'font-family' in list(text['info'].keys()):
                    graphical_text_info['fontFamily'] = text['info']['font-family']

                # get font size
                if 'font-size' in list(text['info'].keys()):
                    graphical_text_info['fontSize'] = {'abs': text['info']['font-size'], 'rel': 0.0}

                # get font weight
                if 'font-wight' in list(text['info'].keys()):
                    graphical_text_info['fontWeight'] = text['info']['font-weight']

                # get font style
                if 'font-style' in list(text['info'].keys()):
                    graphical_text_info['fontStyle'] = text['info']['font-style']

                # get horizontal alignment
                if 'horizontal-alignment' in list(text['info'].keys()):
                    graphical_text_info['hTextAnchor'] = text['info']['horizontal-alignment']

                # get vertical alignment
                if 'vertical-alignment' in list(text['info'].keys()):
                    graphical_text_info['vTextAnchor'] = text['info']['vertical-alignment']

            # get group features
            text['features']['graphicalText'] = graphical_text_info

    def extract_geometric_shape_exclusive_features(self, shape, offset_x=0, offset_y=0):
        if shape['shape'].lower() == "rectangle":
            return self.extract_rectangle_shape_features(shape, offset_x, offset_y)
        elif shape['shape'].lower() == "ellipse":
            return self.extract_ellipse_shape_features(shape, offset_x, offset_y)
        elif shape['shape'].lower() == "polygon":
            return self.extract_polygon_shape_features(shape, offset_x, offset_y)
        return {}

    def extract_rectangle_shape_features(self, rect_shape, offset_x=0, offset_y=0):
        rect_shape_info = {'shape': "rectangle"}

        # get fill color
        if 'fill-color' in list(rect_shape.keys()):
            rect_shape_info['fillColor'] = rect_shape['fill-color']
            self.add_color(rect_shape['fill-color'])

        # get position x
        if 'x' in list(rect_shape.keys()):
            rect_shape_info['x'] = {'abs': rect_shape['x'] + offset_x, 'rel': 0}

        # get position y
        if 'y' in list(rect_shape.keys()):
            rect_shape_info['y'] = {'abs': rect_shape['y'] + offset_y, 'rel': 0}

        # get dimension width
        if 'width' in list(rect_shape.keys()):
            rect_shape_info['width'] = {'abs': rect_shape['width'], 'rel': 0}

        # get dimension height
        if 'height' in list(rect_shape.keys()):
            rect_shape_info['height'] = {'abs': rect_shape['height'], 'rel': 0}

        # get corner curvature radius rx
        if 'rx' in list(rect_shape.keys()):
            rect_shape_info['rx'] = {'abs': rect_shape['rx'], 'rel': 0}

        # get corner curvature radius ry
        if 'ry' in list(rect_shape.keys()):
            rect_shape_info['ry'] = {'abs': rect_shape['ry'], 'rel': 0}

        return rect_shape_info

    def extract_ellipse_shape_features(self, ellipse_shape, offset_x=0, offset_y=0):
        ellipse_shape_info = {'shape': "ellipse"}

        # get fill color
        if 'fill-color' in list(ellipse_shape.keys()):
            ellipse_shape_info['fillColor'] = ellipse_shape['fill-color']
            self.add_color(ellipse_shape['fill-color'])

        # get position cx
        if 'cx' in list(ellipse_shape.keys()):
            ellipse_shape_info['cx'] = {'abs': ellipse_shape['cx'] + offset_x, 'rel': 0}

        # get position cy
        if 'cy' in list(ellipse_shape.keys()):
            ellipse_shape_info['cy'] = {'abs': ellipse_shape['cy'] + offset_y, 'rel': 0}

        # get dimension rx
        if 'rx' in list(ellipse_shape.keys()):
            ellipse_shape_info['rx'] = {'abs': ellipse_shape['rx'], 'rel': 0}

        # get dimension ry
        if 'ry' in list(ellipse_shape.keys()):
            ellipse_shape_info['ry'] = {'abs': ellipse_shape['ry'], 'rel': 0}

        return ellipse_shape_info

    def extract_polygon_shape_features(self, polygon_shape, offset_x=0, offset_y=0):
        polygon_shape_info = {'shape': "polygon"}

        # get fill color
        if 'fill-color' in list(polygon_shape.keys()):
            polygon_shape_info['fillColor'] = polygon_shape['fill-color']
            self.add_color(polygon_shape['fill-color'])

        # set vertices
        if 'points' in list(polygon_shape.keys()):
            vertices_ = []
            for point in polygon_shape['points']:
                vertex_ = {}
                if 'x' in list(point.keys()) and 'y' in list(point.keys()):
                    vertex_['renderPointX'] = {'abs': point['x'] + offset_x, 'rel': 0}
                    vertex_['renderPointY'] = {'abs': point['y'] + offset_y, 'rel': 0}
                vertices_.append(vertex_)

            polygon_shape_info['vertices'] = vertices_
        return polygon_shape_info

    @staticmethod
    def get_bounding_box_features(info):
        bounding_box = {'x': 0.0, 'y': 0.0, 'width': 0.0, 'height': 0.0}
        if 'position' in list(info.keys()) and \
                'x' in list(info['position'].keys()) and \
                'y' in list(info['position'].keys()):
            bounding_box['x'] = info['position']['x']
            bounding_box['y'] = info['position']['y']
        if 'dimensions' in list(info.keys()) and \
                'width' in list(info['dimensions'].keys()) and \
                'height' in list(info['dimensions'].keys()):
            bounding_box['x'] -= 0.5 * info['dimensions']['width']
            bounding_box['y'] -= 0.5 * info['dimensions']['height']
            bounding_box['width'] = info['dimensions']['width']
            bounding_box['height'] = info['dimensions']['height']
        return bounding_box


class SBMLGraphInfoExportBase:
    def __init__(self):
        self.graph_info = None
        self.reset()

    def reset(self):
        self.graph_info = None

    def extract_graph_info(self, graph_info):
        self.reset()
        self.graph_info = graph_info

        # update the features of the entities
        graph_info.extract_entity_features()

        # compartments
        for c in graph_info.compartments:
            self.add_compartment(c)

        # species
        for s in graph_info.species:
            self.add_species(s)

        # reactions
        for r in graph_info.reactions:
            self.add_reaction(r)

    def add_compartment(self, compartment):
        pass

    def add_species(self, species):
        pass

    def add_reaction(self, reaction):
        pass

    def export(self, file_name):
        pass


class SBMLGraphInfoExportToSBMLModel(SBMLGraphInfoExportBase):
    def __init__(self):
        super().__init__()
        self.document = None
        self.layout = None
        self.global_render = None
        self.local_render = None
        self.layoutns = None
        self.renderns = None

    def reset(self):
        super().reset()

    def extract_graph_info(self, graph_info):
        self.create_model()
        super().extract_graph_info(graph_info)
        self.set_layout_dimensions()
        self.set_render_background_color()

        for color in self.graph_info.colors:
            self.add_color(color)

        for gradient in self.graph_info.gradients:
            self.add_gradient(gradient)

        for line_ending in self.graph_info.line_endings:
            self.add_line_ending(line_ending)

    def set_layout_dimensions(self):
        self.layout.setDimensions(libsbml.Dimensions(self.layoutns,
                                                     self.graph_info.extents['maxX'] - self.graph_info.extents['minX'],
                                                     self.graph_info.extents['maxY'] - self.graph_info.extents['minY']))

    def set_render_background_color(self):
        self.global_render.setBackgroundColor(self.graph_info.background_color)

    @staticmethod
    def check(value, message):
        if value == None:
            raise SystemExit('LibSBML returned a null value trying to ' + message + '.')
        elif type(value) is int:
            if value == libsbml.LIBSBML_OPERATION_SUCCESS:
                return
            else:
                err_msg = 'Error encountered trying to ' + message + '.' \
                          + 'LibSBML returned error code ' + str(value) + ': "' \
                          + OperationReturnValue_toString(value).strip() + '"'
                raise SystemExit(err_msg)
        else:
            return

    def create_model(self):
        # document
        sbmlns = libsbml.SBMLNamespaces(3, 1, "layout", 1)
        try:
            self.document = libsbml.SBMLDocument(sbmlns)
        except ValueError:
            raise SystemExit('Could not create SBMLDocumention object')
        self.document.setPkgRequired("layout", False)
        self.document.enablePackage(libsbml.RenderExtension.getXmlnsL3V1V1(), "render", True)
        self.document.setPkgRequired("render", False)

        # model
        model = self.document.createModel()
        self.check(model, 'create model')
        self.check(model.setId("__main"), 'setting model id')
        self.check(model.setMetaId("__main"), 'setting model meta id')

        # layout
        self.layoutns = libsbml.LayoutPkgNamespaces(3, 1, 1)
        lmplugin = model.getPlugin("layout")
        if lmplugin is None:
            print("[Fatal Error] Layout Extension Level " + str(self.layoutns.getLevel()) +
                  " Version " + str(self.layoutns.getVersion()) +
                  " package version " + str(self.layoutns.getPackageVersion()) +
                  " is not registered.")
            sys.exit(1)
        self.layout = lmplugin.createLayout()
        self.layout.setId("SBMLPlot_Layout")

        # global render
        self.renderns = libsbml.RenderPkgNamespaces(3, 1, 1)
        grplugin = lmplugin.getListOfLayouts().getPlugin("render")
        if grplugin is None:
            print("[Fatal Error] Render Extension Level " + str(self.renderns.getLevel()) +
                  " Version " + str(self.renderns.getVersion()) +
                  " package version " + str(self.renderns.getPackageVersion()) +
                  " is not registered.")
            sys.exit(1)
        self.global_render = grplugin.createGlobalRenderInformation()
        self.global_render.setId("SBMLPlot_Global_Render")

        # local render
        lrplugin = self.layout.getPlugin("render")
        if lrplugin is None:
            print("[Fatal Error] Render Extension Level " + str(self.renderns.getLevel()) +
                  " Version " + str(self.renderns.getVersion()) +
                  " package version " + str(self.renderns.getPackageVersion()) +
                  " is not registered.")
            sys.exit(1)
        self.local_render = lrplugin.createLocalRenderInformation()
        self.local_render.setId("SBMLPlot_Local_Render")
        self.local_render.setReferenceRenderInformation("SBMLPlot_Global_Render")

    def add_compartment(self, compartment):
        if 'referenceId' in list(compartment.keys()):
            c = self.document.model.createCompartment()
            self.check(c, 'create compartment ' + compartment['referenceId'])
            self.check(c.setId(compartment['referenceId']), 'set compartment id')
            self.check(c.setConstant(True), 'set compartment "constant"')
            self.check(c.setSize(1), 'set compartment "size"')
            self.check(c.setSpatialDimensions(3), 'set compartment dimensions')
            self.add_compartment_glyph(compartment)

    def add_species(self, species):
        if 'referenceId' in list(species.keys()):
            s = self.document.model.createSpecies()
            self.check(s, 'create species ' + species['referenceId'])
            self.check(s.setId(species['referenceId']), 'set species ' + species['referenceId'] + ' id')
            if 'compartment' in list(species.keys()):
                self.check(s.setCompartment(species['compartment']),
                           'set species' + species['referenceId'] + ' compartment')
            self.check(s.setConstant(False), 'set "constant" attribute on ' + species['referenceId'])
            self.check(s.setInitialAmount(0), 'set initial amount for ' + species['id'])
            self.check(s.setBoundaryCondition(False), 'set "boundaryCondition" on ' + species['id'])
            self.check(s.setHasOnlySubstanceUnits(False), 'set "hasOnlySubstanceUnits" on ' + species['id'])
            self.add_species_glyph(species)

    def add_reaction(self, reaction):
        if 'referenceId' in list(reaction.keys()):
            r = self.document.model.createReaction()
            self.check(r, 'create reaction ' + reaction['referenceId'])
            self.check(r.setId(reaction['referenceId']), 'set reaction ' + reaction['referenceId'] + ' id')
            self.check(r.setReversible(False), 'set reaction ' + reaction['referenceId'] + ' reversibility flag')
            self.check(r.setFast(False), 'set reaction ' + reaction['referenceId'] + ' "fast" attribute')

            # species references
            if 'speciesReferences' in list(reaction.keys()):
                for sr in reaction['speciesReferences']:
                    self.add_species_reference(sr, r)

            self.add_reaction_glyph(reaction)

    def add_species_reference(self, species_reference, reaction):
        if 'referenceId' in list(species_reference.keys()) and \
                'role' in list(species_reference.keys()) and \
                'species' in list(species_reference.keys()):
            sr = None
            if species_reference['role'].lower() == "substrate" or species_reference['role'].lower() == "sidesubstrate"\
                    or species_reference['role'].lower() == "side substrate"\
                    or species_reference['role'].lower() == "reactant":
                sr = reaction.createReactant()
                self.check(sr.setConstant(True),
                           'set species_reference ' + species_reference['referenceId'] + ' "constant" attribute')
            elif species_reference['role'].lower() == "product" or species_reference['role'].lower() == "sideproduct"\
                    or species_reference['role'].lower() == "side product":
                sr = reaction.createProduct()
                self.check(sr.setConstant(True),
                           'set species_reference ' + species_reference['referenceId'] + ' "constant" attribute')
            else:
                sr = reaction.createModifier()

            if sr:
                self.check(sr, 'create species_reference ' + species_reference['referenceId'])
                self.check(sr.setId(species_reference['referenceId']),
                           'set species_reference ' + species_reference['referenceId'] + ' id')
                self.check(sr.setSpecies(species_reference['species']),
                           'assign species_reference ' + species_reference['referenceId'] + ' species')

    def add_compartment_glyph(self, compartment):
        if 'id' in list(compartment.keys()):
            compartment_glyph = self.layout.createCompartmentGlyph()
            compartment_glyph.setId(compartment['id'])
            compartment_glyph.setCompartmentId(compartment['referenceId'])
            self.set_glyph_bounding_box(compartment, compartment_glyph)
            self.add_local_style(compartment)

            # text
            if 'texts' in list(compartment.keys()):
                for text in compartment['texts']:
                    self.add_text_glyph(text, compartment_glyph)

    def add_species_glyph(self, species):
        if 'id' in list(species.keys()):
            species_glyph = self.layout.createSpeciesGlyph()
            species_glyph.setId(species['id'])
            species_glyph.setSpeciesId(species['referenceId'])
            self.set_glyph_bounding_box(species, species_glyph)
            self.add_local_style(species)

            # text
            for text in species['texts']:
                self.add_text_glyph(text, species_glyph)

    def add_reaction_glyph(self, reaction):
        if 'id' in list(reaction.keys()):
            reaction_glyph = self.layout.createReactionGlyph()
            reaction_glyph.setId(reaction['id'])
            reaction_glyph.setReactionId(reaction['referenceId'])
            self.set_glyph_bounding_box(reaction, reaction_glyph)
            self.set_glyph_curve(reaction, reaction_glyph)
            self.add_local_style(reaction)

            # text
            for text in reaction['texts']:
                self.add_text_glyph(text, reaction_glyph)

            # species references
            if 'speciesReferences' in list(reaction.keys()):
                for sr in reaction['speciesReferences']:
                    self.add_species_reference_glyph(sr, reaction_glyph)

    def add_species_reference_glyph(self, species_reference, reaction_glyph):
        if 'id' in list(species_reference.keys()) and 'speciesGlyph' in list(species_reference.keys()):
            species_reference_glyph = reaction_glyph.createSpeciesReferenceGlyph()
            species_reference_glyph.setId(species_reference['id'])
            species_reference_glyph.setSpeciesGlyphId(species_reference['speciesGlyph'])
            species_reference_glyph.setSpeciesReferenceId(species_reference['referenceId'])
            if species_reference['role'].lower() == "substrate" or species_reference['role'].lower() == "reactant":
                species_reference_glyph.setRole(libsbml.SPECIES_ROLE_SUBSTRATE)
            elif species_reference['role'].lower() == "sidesubstrate" or species_reference['role'].lower() == "side substrate"\
                or species_reference['role'].lower() == "sidereactant" or species_reference['role'].lower() == "side reactant":
                species_reference_glyph.setRole(libsbml.SPECIES_ROLE_SIDESUBSTRATE)
            elif species_reference['role'].lower() == "product":
                species_reference_glyph.setRole(libsbml.SPECIES_ROLE_PRODUCT)
            elif species_reference['role'].lower() == "sideproduct" or species_reference['role'].lower() == "side product":
                species_reference_glyph.setRole(libsbml.SPECIES_ROLE_SIDEPRODUCT)
            self.set_glyph_curve(species_reference, species_reference_glyph)
            self.add_local_style(species_reference)

    def add_text_glyph(self, text, go_glyph):
        if 'id' in list(text.keys()):
            text_glyph = self.layout.createTextGlyph()
            text_glyph.setId(text['id'])
            text_glyph.setOriginOfTextId(go_glyph.getId())
            text_glyph.setGraphicalObjectId(go_glyph.getId())
            self.set_glyph_bounding_box(text, text_glyph)
            self.set_text_glyph_plain_text(text, text_glyph)
            self.add_local_style(text)

    def add_local_style(self, go):
        if 'features' in list(go.keys()):
            style = self.local_render.createLocalStyle()
            if 'styleName' in list(go['features'].keys()):
                style.setId(go['features']['styleName'])
            else:
                style.setId(go['id'] + "_style")
            style.addId(go['id'])
            render_group = style.createGroup()
            self.set_render_group_features(render_group, go['features'])

    def set_glyph_bounding_box(self, go, go_glyph):
        if 'features' in list(go.keys()) and 'boundingBox' in list(go['features'].keys()):
            go_glyph.setBoundingBox(libsbml.BoundingBox(self.layoutns,
                                                        go_glyph.getId() + "_bb",
                                                        go['features']['boundingBox']['x'],
                                                        go['features']['boundingBox']['y'],
                                                        go['features']['boundingBox']['width'],
                                                        go['features']['boundingBox']['height']))

    def set_glyph_curve(self, go, go_glyph):
        if 'features' in list(go.keys()) and 'curve' in list(go['features'].keys()):
            for go_curve_element in go['features']['curve']:
                if all(k in go_curve_element.keys() for k in ('startX', 'startY', 'endX', 'endY')):
                    go_glyph_curve = go_glyph.getCurve()
                    element = None
                    if all(k in go_curve_element.keys() for k in
                           ('basePoint1X', 'basePoint1Y', 'basePoint2X', 'basePoint2Y')):
                        element = go_glyph_curve.createCubicBezier()
                        element.setBasePoint1(libsbml.Point(self.layoutns,
                                                            go_curve_element['basePoint1X'],
                                                            go_curve_element['basePoint1Y']))
                        element.setBasePoint2(libsbml.Point(self.layoutns,
                                                            go_curve_element['basePoint2X'],
                                                            go_curve_element['basePoint2Y']))
                    else:
                        element = go_glyph_curve.createLineSegment()
                    element.setStart(libsbml.Point(self.layoutns,
                                                   go_curve_element['startX'],
                                                   go_curve_element['startY']))
                    element.setEnd(libsbml.Point(self.layoutns,
                                                 go_curve_element['endX'],
                                                 go_curve_element['endY']))

    @staticmethod
    def set_text_glyph_plain_text(text, text_glyph):
        if 'features' in list(text.keys()) and 'plainText' in list(text['features'].keys()):
            text_glyph.setText(text['features']['plainText'])

    def set_render_group_features(self, render_group, features):
        if 'graphicalShape' in list(features.keys()):
            self.set_group_general_features(render_group, features['graphicalShape'])
            if 'geometricShapes' in list(features['graphicalShape'].keys()):
                for shape in features['graphicalShape']['geometricShapes']:
                    self.set_group_geometric_shape_features(render_group, shape)
        if 'graphicalCurve' in list(features.keys()):
            self.set_group_curve_features(render_group, features['graphicalCurve'])
        if 'graphicalText' in list(features.keys()):
            self.set_group_text_features(render_group, features['graphicalText'])

    @staticmethod
    def set_group_general_features(render_group, features):
        # stroke color
        if 'strokeColor' in list(features.keys()):
            render_group.setStroke(features['strokeColor'])

        # stroke width
        if 'strokeWidth' in list(features.keys()):
            render_group.setStrokeWidth(features['strokeWidth'])

        # fill color
        if 'fillColor' in list(features.keys()):
            render_group.setFill(features['fillColor'])

    def set_group_geometric_shape_features(self, render_group, shape):
        if 'shape' in list(shape.keys()):
            if shape['shape'] == "image":
                self.set_image_shape_features(render_group, shape)
            elif shape['shape'] == "renderCurve":
                self.set_render_curve_shape_features(render_group, shape)
            elif shape['shape'] == "text":
                self.set_text_shape_features(render_group, shape)
            elif shape['shape'] == "rectangle":
                self.set_rectangle_shape_features(render_group, shape)
            elif shape['shape'] == "ellipse":
                self.set_ellipse_shape_features(render_group, shape)
            elif shape['shape'] == "polygon":
                self.set_polygon_shape_features(render_group, shape)

    @staticmethod
    def set_image_shape_features(render_group, image_shape):
        render_image = render_group.createImage()

        # x
        if 'x' in list(image_shape.keys()):
            render_image.setX(libsbml.RelAbsVector(image_shape['x']['abs'],
                                                   image_shape['x']['rel']))

        # y
        if 'y' in list(rectangle_shape.keys()):
            render_image.setY(libsbml.RelAbsVector(image_shape['y']['abs'],
                                                   image_shape['y']['rel']))

        # width
        if 'width' in list(rectangle_shape.keys()):
            render_image.setWidth(libsbml.RelAbsVector(image_shape['width']['abs'],
                                                       image_shape['width']['rel']))

        # height
        if 'height' in list(rectangle_shape.keys()):
            render_image.setHeight(libsbml.RelAbsVector(image_shape['height']['abs'],
                                                        image_shape['height']['rel']))

        # href
        if 'href' in list(rectangle_shape.keys()):
            render_image.setHref(image_shape['href'])

    def set_render_curve_shape_features(self, render_group, curve_shape):
        render_curve = render_group.createCurve()

        # stroke color
        if 'strokeColor' in list(curve_shape.keys()):
            render_curve.setStroke(curve_shape['strokeColor'])

        # stroke width
        if 'strokeWidth' in list(curve_shape.keys()):
            render_curve.setStrokeWidth(curve_shape['strokeWidth'])

        if 'vertices' in list(curve_shape.keys()):
            for vertex in curve_shape['vertices']:
                if all(k in vertex.keys() for k in ('basePoint1X', 'basePoint1Y', 'basePoint2X', 'basePoint2Y')):
                    render_curve.addElement(libsbml.RenderCubicBezier(self.renderns,
                                                                      libsbml.RelAbsVector(vertex['basePoint1X']['abs'],
                                                                                           vertex['basePoint1X'][
                                                                                               'rel']),
                                                                      libsbml.RelAbsVector(vertex['basePoint2X']['abs'],
                                                                                           vertex['basePoint2X'][
                                                                                               'rel']),
                                                                      libsbml.RelAbsVector(
                                                                          vertex['renderPointX']['abs'],
                                                                          vertex['renderPointX']['rel']),
                                                                      libsbml.RelAbsVector(
                                                                          vertex['renderPointY']['abs'],
                                                                          vertex['renderPointY']['rel'])))
                else:
                    render_curve.addElement(libsbml.RenderPoint(self.renderns,
                                                                libsbml.RelAbsVector(vertex['renderPointX']['abs'],
                                                                                     vertex['renderPointX']['rel']),
                                                                libsbml.RelAbsVector(vertex['renderPointY']['abs'],
                                                                                     vertex['renderPointY']['rel'])))

    @staticmethod
    def set_text_shape_features(render_group, text_shape):
        render_text = render_group.createText()

        # stroke color
        if 'strokeColor' in list(text_shape.keys()):
            render_text.setStroke(text_shape['strokeColor'])

        # x
        if 'x' in list(text_shape.keys()):
            render_text.setX(libsbml.RelAbsVector(text_shape['x']['abs'],
                                                  text_shape['x']['rel']))

        # y
        if 'y' in list(text_shape.keys()):
            render_text.setY(libsbml.RelAbsVector(text_shape['y']['abs'],
                                                  text_shape['y']['rel']))

        # font family
        if 'fontFamily' in list(text_shape.keys()):
            render_text.setFontFamily(text_shape['fontFamily'])

        # font Size
        if 'fontSize' in list(text_shape.keys()):
            render_text.setFontSize(libsbml.RelAbsVector(text_shape['fontSize']['abs'],
                                                         text_shape['fontSize']['rel']))

        # font weight
        if 'fontWeight' in list(text_shape.keys()):
            render_text.setFontWeight(text_shape['fontWeight'])

        # font weight
        if 'fontStyle' in list(text_shape.keys()):
            render_text.setFontStyle(text_shape['fontStyle'])

        # horizontal text anchor
        if 'hTextAnchor' in list(text_shape.keys()):
            render_text.setTextAnchor(text_shape['hTextAnchor'])

        # vertical text anchor
        if 'vTextAnchor' in list(text_shape.keys()):
            render_text.setVTextAnchor(text_shape['vTextAnchor'])

    @staticmethod
    def set_rectangle_shape_features(render_group, rectangle_shape):
        render_rectangle = render_group.createRectangle()

        # stroke color
        if 'strokeColor' in list(rectangle_shape.keys()):
            render_rectangle.setStroke(rectangle_shape['strokeColor'])

        # stroke width
        if 'strokeWidth' in list(rectangle_shape.keys()):
            render_rectangle.setStrokeWidth(rectangle_shape['strokeWidth'])

        # fill color
        if 'fillColor' in list(rectangle_shape.keys()):
            render_rectangle.setFill(rectangle_shape['fillColor'])

        # x
        if 'x' in list(rectangle_shape.keys()):
            render_rectangle.setX(libsbml.RelAbsVector(rectangle_shape['x']['abs'],
                                                       rectangle_shape['x']['rel']))

        # y
        if 'y' in list(rectangle_shape.keys()):
            render_rectangle.setY(libsbml.RelAbsVector(rectangle_shape['y']['abs'],
                                                       rectangle_shape['y']['rel']))

        # width
        if 'width' in list(rectangle_shape.keys()):
            render_rectangle.setWidth(libsbml.RelAbsVector(rectangle_shape['width']['abs'],
                                                           rectangle_shape['width']['rel']))

        # height
        if 'height' in list(rectangle_shape.keys()):
            render_rectangle.setHeight(libsbml.RelAbsVector(rectangle_shape['height']['abs'],
                                                            rectangle_shape['height']['rel']))

        # ratio
        if 'ratio' in list(rectangle_shape.keys()):
            render_rectangle.setRatio(rectangle_shape['ratio'])

        # rx
        if 'rx' in list(rectangle_shape.keys()):
            render_rectangle.setRX(libsbml.RelAbsVector(rectangle_shape['rx']['abs'],
                                                        rectangle_shape['rx']['rel']))

        # ry
        if 'ry' in list(rectangle_shape.keys()):
            render_rectangle.setRY(libsbml.RelAbsVector(rectangle_shape['ry']['abs'],
                                                        rectangle_shape['ry']['rel']))

    @staticmethod
    def set_ellipse_shape_features(render_group, ellipse_shape):
        render_ellipse = render_group.createEllipse()

        # stroke color
        if 'strokeColor' in list(ellipse_shape.keys()):
            render_ellipse.setStroke(ellipse_shape['strokeColor'])

        # stroke width
        if 'strokeWidth' in list(ellipse_shape.keys()):
            render_ellipse.setStrokeWidth(ellipse_shape['strokeWidth'])

        # fill color
        if 'fillColor' in list(ellipse_shape.keys()):
            render_ellipse.setFill(ellipse_shape['fillColor'])

        # cx
        if 'cx' in list(ellipse_shape.keys()):
            render_ellipse.setCX(libsbml.RelAbsVector(ellipse_shape['cx']['abs'],
                                                      ellipse_shape['cx']['rel']))

        # cy
        if 'cy' in list(ellipse_shape.keys()):
            render_ellipse.setCY(libsbml.RelAbsVector(ellipse_shape['cy']['abs'],
                                                      ellipse_shape['cy']['rel']))

        # rx
        if 'rx' in list(ellipse_shape.keys()):
            render_ellipse.setRX(libsbml.RelAbsVector(ellipse_shape['rx']['abs'],
                                                      ellipse_shape['rx']['rel']))

        # ry
        if 'ry' in list(ellipse_shape.keys()):
            render_ellipse.setRY(libsbml.RelAbsVector(ellipse_shape['ry']['abs'],
                                                      ellipse_shape['ry']['rel']))

        # ratio
        if 'ratio' in list(ellipse_shape.keys()):
            render_ellipse.setRatio(ellipse_shape['ratio'])

    def set_polygon_shape_features(self, render_group, polygon_shape):
        render_polygon = render_group.createPolygon()

        # stroke color
        if 'strokeColor' in list(polygon_shape.keys()):
            render_polygon.setStroke(polygon_shape['strokeColor'])

        # stroke width
        if 'strokeWidth' in list(polygon_shape.keys()):
            render_polygon.setStrokeWidth(polygon_shape['strokeWidth'])

        # fill color
        if 'fillColor' in list(polygon_shape.keys()):
            render_polygon.setFill(polygon_shape['fillColor'])

        # fill rule
        if 'fillRule' in list(polygon_shape.keys()):
            render_polygon.setFillRule(polygon_shape['fillRule'])

        if 'vertices' in list(polygon_shape.keys()):
            for vertex in polygon_shape['vertices']:
                if all(k in vertex.keys() for k in ('basePoint1X', 'basePoint1Y', 'basePoint2X', 'basePoint2Y')):
                    render_polygon.addElement(libsbml.RenderCubicBezier(self.renderns,
                                                                        libsbml.RelAbsVector(
                                                                            vertex['basePoint1X']['abs'],
                                                                            vertex['basePoint1X']['rel']),
                                                                        libsbml.RelAbsVector(
                                                                            vertex['basePoint2X']['abs'],
                                                                            vertex['basePoint2X']['rel']),
                                                                        libsbml.RelAbsVector(
                                                                            vertex['renderPointX']['abs'],
                                                                            vertex['renderPointX']['rel']),
                                                                        libsbml.RelAbsVector(
                                                                            vertex['renderPointY']['abs'],
                                                                            vertex['renderPointY']['rel'])))
                else:
                    render_polygon.addElement(libsbml.RenderPoint(self.renderns,
                                                                  libsbml.RelAbsVector(vertex['renderPointX']['abs'],
                                                                                       vertex['renderPointX']['rel']),
                                                                  libsbml.RelAbsVector(vertex['renderPointY']['abs'],
                                                                                       vertex['renderPointY']['rel'])))

    @staticmethod
    def set_group_curve_features(render_group, features):
        # stroke color
        if 'strokeColor' in list(features.keys()):
            render_group.setStroke(features['strokeColor'])

        # stroke width
        if 'strokeWidth' in list(features.keys()):
            render_group.setStrokeWidth(features['strokeWidth'])

        # heads
        if 'heads' in list(features.keys()):
            if 'start' in list(features['heads'].keys()):
                render_group.setStartHead(features['heads']['start'])
            if 'end' in list(features['heads'].keys()):
                render_group.setEndHead(features['heads']['end'])

    @staticmethod
    def set_group_text_features(render_group, features):
        # stroke color
        if 'strokeColor' in list(features.keys()):
            render_group.setStroke(features['strokeColor'])

        # font family
        if 'fontFamily' in list(features.keys()):
            render_group.setFontFamily(features['fontFamily'])

        # font Size
        if 'fontSize' in list(features.keys()):
            render_group.setFontSize(libsbml.RelAbsVector(features['fontSize']['abs'],
                                                          features['fontSize']['rel']))

        # font weight
        if 'fontWeight' in list(features.keys()):
            render_group.setFontWeight(features['fontWeight'])

        # font weight
        if 'fontStyle' in list(features.keys()):
            render_group.setFontStyle(features['fontStyle'])

        # horizontal text anchor
        if 'hTextAnchor' in list(features.keys()):
            render_group.setTextAnchor(features['hTextAnchor'])

        # vertical text anchor
        if 'vTextAnchor' in list(features.keys()):
            render_group.setVTextAnchor(features['vTextAnchor'])

    def add_color(self, color):
        color_definition = self.global_render.createColorDefinition()
        color_definition.setId(color['id'])
        if 'features' in list(color.keys()):
            color_definition.setValue(color['features']['value'])

    def add_gradient(self, gradient):
        if 'features' in list(gradient.keys()):
            gradient_definition = None
            # linear gradient
            if 'start' in list(gradient['features'].keys()) and 'end' in list(gradient['features'].keys()):
                gradient_definition = self.global_render.createLinearGradientDefinition()
                gradient_definition.setX1(libsbml.RelAbsVector(gradient['features']['start']['x']['abs'],
                                                               gradient['features']['start']['x']['rel']))
                gradient_definition.setY1(libsbml.RelAbsVector(gradient['features']['start']['y']['abs'],
                                                               gradient['features']['start']['y']['rel']))
                gradient_definition.setX2(libsbml.RelAbsVector(gradient['features']['end']['x']['abs'],
                                                               gradient['features']['end']['x']['rel']))
                gradient_definition.setY2(libsbml.RelAbsVector(gradient['features']['end']['y']['abs'],
                                                               gradient['features']['end']['y']['rel']))
            # radial gradient
            elif 'center' in list(gradient['features'].keys()) and \
                    'focalPoint' in list(gradient['features'].keys() and \
                                         'radius' in list(gradient['features'].keys())):
                gradient_definition = self.global_render.createRadialGradientDefinition()
                gradient_definition.setCx(libsbml.RelAbsVector(gradient['features']['center']['x']['abs'],
                                                               gradient['features']['center']['x']['rel']))
                gradient_definition.setCy(libsbml.RelAbsVector(gradient['features']['center']['y']['abs'],
                                                               gradient['features']['center']['y']['rel']))
                gradient_definition.setFx(libsbml.RelAbsVector(gradient['features']['focalPoint']['x']['abs'],
                                                               gradient['features']['focalPoint']['x']['rel']))
                gradient_definition.setFy(libsbml.RelAbsVector(gradient['features']['focalPoint']['y']['abs'],
                                                               gradient['features']['focalPoint']['y']['rel']))
                gradient_definition.setR(libsbml.RelAbsVector(gradient['features']['radius']['abs'],
                                                              gradient['features']['radius']['rel']))

            if gradient_definition:
                # spread method
                if 'spreadMethod' in list(gradient['features'].keys()):
                    gradient_definition.setSpreadMethod(gradient['features']['spreadMethod'])

                # stops
                for stop in gradient['features']['stops']:
                    gradient_stop = gradient_definition.createGradientStop()
                    if 'offset' in list(stop.keys()):
                        gradient_stop.setOffset(libsbml.RelAbsVector(stop['offset']['abs'], stop['offset']['rel']))
                    if 'color' in list(stop.keys()):
                        gradient_stop.setStopColor(stop['color'])

    def add_line_ending(self, line_ending):
        line_ending_definition = self.global_render.createLineEnding()
        line_ending_definition.setId(line_ending['id'])
        self.set_glyph_bounding_box(line_ending, line_ending_definition)
        if 'features' in list(line_ending.keys()):
            render_group = line_ending_definition.createGroup()
            self.set_render_group_features(render_group, line_ending['features'])
            if 'enableRotation' in list(line_ending['features'].keys()):
                line_ending_definition.setEnableRotationalMapping(line_ending['features']['enableRotation'])

    def export(self, file_name):
        libsbml.writeSBMLToFile(self.document, file_name.split('.')[0] + ".xml")


class SBMLGraphInfoExportToJsonBase(SBMLGraphInfoExportBase):
    def __init__(self):
        self.nodes = []
        self.edges = []
        super().__init__()

    def reset(self):
        super().reset()
        self.nodes.clear()
        self.edges.clear()

    def add_compartment(self, compartment):
        if 'id' in list(compartment.keys()) and 'referenceId' in list(compartment.keys()):
            self.add_node(compartment, "Compartment")

    def add_species(self, species):
        if 'id' in list(species.keys()) and 'referenceId' in list(species.keys()):
            self.add_node(species, "Species")

    def add_reaction(self, reaction):
        if 'id' in list(reaction.keys()) and 'referenceId' in list(reaction.keys()):
            self.add_node(reaction, "Reaction")

            if 'speciesReferences' in list(reaction.keys()):
                for sr in reaction['speciesReferences']:
                    self.add_species_reference(reaction, sr)

    def add_species_reference(self, reaction, species_reference):
        if 'id' in list(species_reference.keys()) and 'referenceId' in list(species_reference.keys()) \
                and 'species' in list(species_reference.keys()):
            self.add_edge(species_reference, reaction)

    def add_node(self, go):
        pass

    def add_edge(self, species_reference, reaction):
        pass

class SBMLGraphInfoExportToCytoscapeJs(SBMLGraphInfoExportToJsonBase):
    def __init__(self):
        self.styles = []
        super().__init__()

    def reset(self):
        super().reset()
        self.styles.clear()

    def add_node(self, go, category = ""):
        node = self.initialize_entity(go)
        self.set_entity_metaid(node, go)
        style = self.initialize_node_style(go)
        selected_style = self.initialize_node_selected_style(go)
        self.set_entity_compartment(node, go)
        self.extract_node_features(go, node, style)
        self.set_entity_selected(node, False)
        self.nodes.append(node)
        self.styles.append(style)
        self.styles.append(selected_style)

    def add_edge(self, species_reference, reaction):
        edge = self.initialize_entity(species_reference)
        self.set_entity_metaid(edge, species_reference)
        style = self.initialize_edge_style(species_reference)
        selected_style = self.initialize_edge_selected_style(species_reference)
        self.set_edge_nodes(edge, species_reference, reaction)
        self.extract_edge_features(species_reference, style)
        self.set_entity_selected(edge, False)
        self.edges.append(edge)
        self.styles.append(style)
        self.styles.append(selected_style)

    @staticmethod
    def initialize_entity(go):
        return {'data': {'id': go['id'], 'referenceId': go['referenceId']}}

    @staticmethod
    def set_entity_metaid(entity, go):
        if 'metaId' in list(go.keys()):
            entity['data']['metaId'] = go['metaId']

    def set_entity_compartment(self, entity, go):
        if 'compartment' in list(go.keys()):
            for c in self.graph_info.compartments:
                if c['referenceId'] == go['compartment']:
                    entity['data']['parent'] = c['id']
                    break

    @staticmethod
    def set_entity_selected(entity, selected):
        entity['selected'] = selected

    @staticmethod
    def initialize_node_style(go):
        return {'selector': "node[id = '" + go['id'] + "']", 'css': {'content': 'data(name)'}}

    @staticmethod
    def initialize_edge_style(species_reference):
        return {'selector': "edge[id = '" + species_reference['id'] + "']",
                'css': {'content': "", 'curve-style': 'bezier'}}

    @staticmethod
    def initialize_node_selected_style(go):
        return {'selector': "node[id = '" + go['id'] + "']:selected",
                'css': {'background-color': '#4169e1'}}

    @staticmethod
    def initialize_edge_selected_style(go):
        return {'selector': "edge[id = '" + go['id'] + "']:selected",
                'css': {'line-color': '#4169e1',
                        'source-arrow-color': '#4169e1',
                        'target-arrow-color': '#4169e1'}}

    def set_edge_nodes(self, edge, species_reference, reaction):
        species = None
        for s in self.graph_info.species:
            if s['referenceId'] == species_reference['species']:
                species = s
                break
        if species and 'role' in list(species_reference.keys()):
            if species_reference['role'].lower() == "product" or species_reference['role'].lower() == "sideproduct" or species_reference['role'].lower() == "side product":
                edge['data']['source'] = reaction['id']
                edge['data']['target'] = species['id']
            else:
                edge['data']['source'] = species['id']
                edge['data']['target'] = reaction['id']

    def extract_node_features(self, go, node, style):
        if 'features' in list(go.keys()):
            if 'boundingBox' in list(go['features'].keys()):
                node['position'] = self.get_node_position(go)
                style['css'].update(self.get_node_dimensions(go))
            if 'graphicalShape' in list(go['features'].keys()):
                style['css'].update(self.set_shape_style(go))
        if 'texts' in list(go.keys()) and len(go['texts']):
            text = go['texts'][0]
            if 'features' in list(text.keys()):
                if 'plainText' in list(text['features'].keys()):
                    node['data']['name'] = text['features']['plainText']
                if 'graphicalText' in list(text['features'].keys()):
                    style['css'].update(self.set_node_text_style(text))

    def extract_edge_features(self, go, style):
        if 'features' in list(go.keys()):
            if 'graphicalCurve' in list(go['features'].keys()):
                style['css'].update(self.set_curve_style(go))

    @staticmethod
    def get_node_position(go):
        return {'x': go['features']['boundingBox']['x']
                     + 0.5 * go['features']['boundingBox']['width'],
                'y': go['features']['boundingBox']['y']
                     + 0.5 * go['features']['boundingBox']['height']}

    @staticmethod
    def get_node_dimensions(go):
        return {'width': go['features']['boundingBox']['width'],
                'height': go['features']['boundingBox']['height']}

    def set_shape_style(self, go):
        shape_style = {}
        if 'strokeColor' in list(go['features']['graphicalShape'].keys()):
            shape_style['border-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalShape']['strokeColor'])
        if 'strokeWidth' in list(go['features']['graphicalShape'].keys()):
            shape_style['border-width'] = go['features']['graphicalShape']['strokeWidth']
        if 'fillColor' in list(go['features']['graphicalShape'].keys()):
            shape_style['background-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalShape']['fillColor'])
        if 'geometricShapes' in list(go['features']['graphicalShape'].keys()):
            if 'strokeColor' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                shape_style['border-color'] = \
                    self.graph_info.find_color_value(go['features']['graphicalShape']
                                                     ['geometricShapes'][0]['strokeColor'])
            if 'strokeWidth' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                shape_style['border-width'] = \
                    go['features']['graphicalShape']['geometricShapes'][0]['strokeWidth']
            if 'fillColor' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                shape_style['background-color'] = \
                    self.graph_info.find_color_value(
                        go['features']['graphicalShape']['geometricShapes'][0]['fillColor'])
            if 'shape' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                if go['features']['graphicalShape']['geometricShapes'][0]['shape'].lower() == "rectangle":
                    shape_style['shape'] = 'roundrectangle'
                elif go['features']['graphicalShape']['geometricShapes'][0]['shape'].lower() == "ellipse":
                    shape_style['shape'] = 'ellipse'
        return shape_style

    def set_curve_style(self, go):
        curve_style = {}
        if 'strokeColor' in list(go['features']['graphicalCurve'].keys()):
            curve_style['line-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalCurve']['strokeColor'])
            curve_style['source-arrow-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalCurve']['strokeColor'])
            curve_style['target-arrow-color'] = \
                self.graph_info.find_color_value(go['features']['graphicalCurve']['strokeColor'])
        if 'strokeWidth' in list(go['features']['graphicalCurve'].keys()):
            curve_style['width'] = go['features']['graphicalCurve']['strokeWidth']
        if 'role' in list(go.keys()):
            curve_style['target-arrow-shape'] = self.set_edge_target_arrow_shape(go)
        return curve_style

    def set_node_text_style(self, text):
        text_style = {}
        if 'strokeColor' in list(text['features']['graphicalText'].keys()):
            text_style['color'] = \
                self.graph_info.find_color_value(text['features']['graphicalText']['strokeColor'])
        if 'fontFamily' in list(text['features']['graphicalText'].keys()):
            text_style['font-family'] = text['features']['graphicalText']['fontFamily']
        if 'fontWeight' in list(text['features']['graphicalText'].keys()):
            text_style['font-weight'] = text['features']['graphicalText']['fontWeight']
        if 'fontStyle' in list(text['features']['graphicalText'].keys()):
            text_style['font-style'] = text['features']['graphicalText']['fontStyle']
        if 'fontSize' in list(text['features']['graphicalText'].keys()) and \
                'boundingBox' in list(text['features'].keys()):
            text_style['font-size'] = text['features']['graphicalText']['fontSize']['abs'] +\
                                      text['features']['boundingBox']['width'] *\
                                      text['features']['graphicalText']['fontSize']['rel']
        if 'vTextAnchor' in list(text['features']['graphicalText'].keys()):
            if text['features']['graphicalText']['vTextAnchor'] == 'middle':
                text_style['text-valign'] = 'center'
            else:
                text_style['text-valign'] = text['features']['graphicalText']['vTextAnchor']
        if 'hTextAnchor' in list(text['features']['graphicalText'].keys()):
            if text['features']['graphicalText']['hTextAnchor'] == 'start':
                text_style['text-halign'] = 'left'
            elif text['features']['graphicalText']['hTextAnchor'] == 'middle':
                text_style['text-halign'] = 'center'
            elif text['features']['graphicalText']['hTextAnchor'] == 'end':
                text_style['text-halign'] = 'right'
        return text_style

    @staticmethod
    def set_edge_target_arrow_shape(go):
        if go['role'].lower() == "product":
            return "triangle"
        elif go['role'].lower() == "modifier":
            return "diamond"
        elif go['role'].lower() == "activator":
            return "circle"
        elif go['role'].lower() == "inhibitor":
            return "tee"
        return ""

    def export(self, file_name):
        graph_info = dict(data={'generated_by': "SBMLplot", 'name': pathlib(file_name).stem,
                                'shared_name': pathlib(file_name).stem, 'selected': True})
        graph_info['elements'] = {'nodes': self.nodes, 'edges': self.edges}
        graph_info['style'] = self.styles
        with open(file_name.split('.')[0] + ".js", 'w', encoding='utf8') as js_file:
            js_file.write("graph_info = ")
            json.dump(graph_info, js_file, indent=1)
            js_file.write(";")


class SBMLGraphInfoExportToNetworkEditor(SBMLGraphInfoExportToJsonBase):
    def __init__(self):
        super().__init__()

    def reset(self):
        super().reset()

    def add_node(self, go, category = ""):
        node_ = self.initialize_entity(go)
        self.set_entity_metaid(node_, go)
        style_ = self.initialize_node_style(go, category)
        self.set_entity_compartment(node_, go)
        self.extract_node_features(go, node_, style_)
        node_['style'] = style_
        self.nodes.append(node_)

    def add_edge(self, species_reference, reaction):
        edge_ = self.initialize_entity(species_reference)
        self.set_entity_metaid(edge_, species_reference)
        style_ = self.initialize_edge_style(species_reference)
        self.set_edge_nodes(edge_, species_reference, reaction)
        self.extract_edge_features(species_reference, style_)
        edge_['style'] = style_
        self.edges.append(edge_)

    @staticmethod
    def initialize_entity(go):
        return {'id': go['id']}

    @staticmethod
    def set_entity_metaid(item, go):
        if 'metaId' in list(go.keys()):
            item['metaId'] = go['metaId']

    def set_entity_compartment(self, item, go):
        if 'compartment' in list(go.keys()):
            for c in self.graph_info.compartments:
                if c['referenceId'] == go['compartment']:
                    item['parent'] = c['id']
                    break

    @staticmethod
    def initialize_node_style(go, category):
        parent_category = ""
        convertible_parent_category = ""
        parent_title = ""
        parent_categories = []
        if category == "Compartment":
            parent_category = "Compartment"
            convertible_parent_category = "Compartment"
        else:
            parent_categories = ["Compartment"]
            parent_title = "Compartment"
        return {'name': go['referenceId'] + "_style", 'category': category, 'sub-category': "",
                'convertible-parent-category': convertible_parent_category, 'parent-category': parent_category,
                'parent-categories': parent_categories, 'parent-title': parent_title,
                'is-name-editable': True, 'name-title': "Id",
                'shapes': []}

    @staticmethod
    def initialize_edge_style(species_reference):
        connectable_source_node_title = "Species"
        connectable_source_node_categories = ["Species"]
        connectable_target_node_title = "Reaction"
        connectable_target_node_categories = ["Reaction"]
        if species_reference['role'].lower() == "product" or species_reference['role'].lower() == "side product":
            connectable_source_node_title = "Reaction"
            connectable_source_node_categories = ["Reaction"]
            connectable_target_node_title = "Species"
            connectable_target_node_categories = ["Species"]
        return {'name': species_reference['referenceId'] + "_style", 'category': "SpeciesReference",
                'sub-category': species_reference['role'],
                'connectable-source-node-title': connectable_source_node_title, 'connectable-source-node-categories': connectable_source_node_categories,
                'connectable-target-node-title': connectable_target_node_title, 'connectable-target-node-categories': connectable_target_node_categories,
                'name-title': "Id", 'is-name-editable': True, 'shapes': []}

    def set_edge_nodes(self, edge, species_reference, reaction):
        species = {}
        for s in self.graph_info.species:
            if s['referenceId'] == species_reference['species'] and s['id'] == species_reference['speciesGlyph']:
                species = s
                break
        if 'role' in list(species_reference.keys()):
            if species_reference['role'].lower() == "product" or species_reference['role'].lower() == "side product":
                edge['source'], edge['target'] = self.get_edge_nodes_features(reaction, species)
            else:
                edge['source'], edge['target'] = self.get_edge_nodes_features(species, reaction)

    def extract_node_features(self, go, node, style):
        if 'features' in list(go.keys()):
            if 'boundingBox' in list(go['features'].keys()):
                node['position'] = self.get_node_position(go)
                node['dimensions'] = self.get_node_dimensions(go)
            if 'graphicalShape' in list(go['features'].keys())\
                    and 'geometricShapes' in list(go['features']['graphicalShape'].keys()):
                if len(go['features']['graphicalShape']['geometricShapes']):
                    style['shapes'] = self.get_shape_style(go, offset_x=-0.5 * go['features']['boundingBox']['width'],
                                                           offset_y=-0.5 * go['features']['boundingBox']['height'])
                elif 'curve' in list(go['features'].keys()):
                    style['shapes'] = self.get_centroid_shape_style(go)
            if 'texts' in list(go.keys()):
                for text in go['texts']:
                    if 'features' in list(text.keys()):
                        style['shapes'].append(self.get_node_text(text, go['features']['boundingBox']))

    def extract_edge_features(self, go, style):
        if 'features' in list(go.keys()) and 'graphicalCurve' in list(go['features'].keys()):
            curve_style = self.get_curve_style(go)
            curve_style["shape"] = self.get_curve_style_shape_type(style)
            style['shapes'].append(curve_style)
            if 'heads' in list(go['features']['graphicalCurve'].keys()) \
                    and 'end' in list(go['features']['graphicalCurve']['heads'].keys()):
                style['arrow-head'] =\
                    self.get_arrow_heads(go['features']['graphicalCurve']['heads'], style['name'])

    @staticmethod
    def get_curve_style_shape_type(style):
        if style['connectable-source-node-title'] == "Reaction":
            return "connected-to-source-centroid-shape-line"
        else:
            return "connected-to-target-centroid-shape-line"

    @staticmethod
    def get_node_position(go):
        return {'x': go['features']['boundingBox']['x']
                     + 0.5 * go['features']['boundingBox']['width'],
                'y': go['features']['boundingBox']['y']
                     + 0.5 * go['features']['boundingBox']['height']}

    @staticmethod
    def get_node_dimensions(go):
        return {'width': go['features']['boundingBox']['width'],
                'height': go['features']['boundingBox']['height']}

    def get_edge_nodes_features(self, start_go, end_go):
        start_node_features = {'node': start_go['id']}
        end_node_features = {'node': end_go['id']}
        start_node_position = self.get_node_position(start_go)
        start_node_dimensions = self.get_node_dimensions(start_go)
        end_node_position = self.get_node_position(end_go)
        end_node_dimensions = self.get_node_dimensions(end_go)
        start_node_radius = 0.5 * max(start_node_dimensions['width'], start_node_dimensions['height'])
        end_node_radius = 0.5 * max(end_node_dimensions['width'], end_node_dimensions['height'])
        slope = math.atan2(end_node_position['y'] - start_node_position['y'],
                           end_node_position['x'] - start_node_position['x']);
        start_node_features['position'] = {'x': start_node_position['x'] + start_node_radius * math.cos(slope),
                                           'y': start_node_position['y'] + start_node_radius * math.sin(slope)}
        end_node_features['position'] = {'x': end_node_position['x'] - end_node_radius * math.cos(slope),
                                         'y': end_node_position['y'] + end_node_radius * math.sin(slope)}

        return start_node_features, end_node_features

    def get_shape_style(self, go, offset_x=0.0, offset_y=0.0):
        geometric_shapes = []
        for gs in go['features']['graphicalShape']['geometricShapes']:
            geometric_shape = {}
            if 'strokeColor' in list(go['features']['graphicalShape'].keys()):
                default_stroke = \
                    self.graph_info.find_color_value(go['features']['graphicalShape']['strokeColor'])
                if default_stroke:
                    geometric_shape['border-color'] = default_stroke
            if 'strokeWidth' in list(go['features']['graphicalShape'].keys()):
                geometric_shape['border-width'] = go['features']['graphicalShape']['strokeWidth']
            if 'fillColor' in list(go['features']['graphicalShape'].keys()):
                default_fill = \
                    self.graph_info.find_color_value(go['features']['graphicalShape']['fillColor'])
                if default_fill:
                    geometric_shape['fill-color'] = default_fill
            geometric_shape.update(
                self.get_geometric_shape_features(gs, self.get_node_dimensions(go), offset_x, offset_y))
            if 'shape' in list(geometric_shape.keys()):
                geometric_shapes.append(geometric_shape)
        return geometric_shapes

    @staticmethod
    def get_centroid_shape_style(go):
        geometric_shape = {'shape': "centroid"}
        if 'strokeColor' in list(go['features']['graphicalShape'].keys()):
            geometric_shape['border-color'] = go['features']['graphicalShape']['strokeColor']
        if 'strokeWidth' in list(go['features']['graphicalShape'].keys()):
            geometric_shape['border-width'] = go['features']['graphicalShape']['strokeWidth']
        if 'fillColor' in list(go['features']['graphicalShape'].keys()):
            geometric_shape['fill-color'] = go['features']['graphicalShape']['fillColor']
        return [geometric_shape]

    def get_curve_style(self, go):
        geometric_shape = {}
        if 'strokeColor' in list(go['features']['graphicalCurve'].keys()):
            default_stroke = \
                self.graph_info.find_color_value(go['features']['graphicalCurve']['strokeColor'])
            if default_stroke:
                geometric_shape['border-color'] = default_stroke
        if 'strokeWidth' in list(go['features']['graphicalCurve'].keys()):
            geometric_shape['border-width'] = go['features']['graphicalCurve']['strokeWidth']
        geometric_shape.update(self.get_curve_style_features(go['features']['graphicalCurve']))
        if len(go['features']['curve']):
            geometric_shape.update(self.get_curve_features(go['features']['curve']))

        return geometric_shape

    def get_geometric_shape_features(self, gs, dimensions, offset_x, offset_y):
        geometric_shape = {}
        if 'strokeColor' in list(gs.keys()):
            geometric_shape['border-color'] = self.graph_info.find_color_value(gs['strokeColor'])
        if 'strokeWidth' in list(gs.keys()):
            geometric_shape['border-width'] = gs['strokeWidth']
        if 'fillColor' in list(gs.keys()):
            geometric_shape['fill-color'] = self.graph_info.find_color_value(gs['fillColor'])
        if 'shape' in list(gs.keys()):
            if gs['shape'].lower() == "rectangle":
                geometric_shape.update(
                    self.get_rectangle_features(gs, dimensions, offset_x, offset_y))
            elif gs['shape'].lower() == "ellipse":
                geometric_shape.update(
                    self.get_ellipse_features(gs, dimensions, offset_x, offset_y))
            elif gs['shape'].lower() == "polygon":
                geometric_shape.update(
                    self.get_polygon_features(gs, dimensions, offset_x, offset_y))
        return geometric_shape

    def get_curve_style_features(self, gc):
        geometric_shape = {}
        if 'strokeColor' in list(gc.keys()):
            geometric_shape['border-color'] = self.graph_info.find_color_value(gc['strokeColor'])
        if 'strokeWidth' in list(gc.keys()):
            geometric_shape['border-width'] = gc['strokeWidth']
        if 'fillColor' in list(gc.keys()):
            geometric_shape['fill-color'] = self.graph_info.find_color_value(gc['fillColor'])
        return geometric_shape

    @staticmethod
    def get_curve_features(curve):
        curve_shape = {}
        start_element = curve[0]
        end_element = curve[len(curve) - 1]
        curve_shape['p1'] = {'x': 0, 'y': 0}
        curve_shape['p2'] = {'x': 0, 'y': 0}
        if all(k in start_element.keys() for k in ('startX', 'startY', 'endX', 'endY',
                                             'basePoint1X', 'basePoint1Y', 'basePoint2X', 'basePoint2Y')):
            if abs(end_element['endX'] - start_element['startX']) > 0:
                curve_shape['p1']['x'] = \
                    round((start_element['basePoint1X'] - start_element['startX']) / (
                            0.01 * (end_element['endX'] - start_element['startX'])))
            if abs(end_element['endY'] - start_element['startY']) > 0:
                curve_shape['p1']['y'] = \
                    round((start_element['basePoint1Y'] - start_element['startY']) / (
                            0.01 * (end_element['endY'] - start_element['startY'])))
        if all(k in end_element.keys() for k in ('startX', 'startY', 'endX', 'endY',
                                                          'basePoint1X', 'basePoint1Y', 'basePoint2X',
                                                          'basePoint2Y')):
            if abs(end_element['endX'] - start_element['startX']) > 0:
                curve_shape['p2']['x'] = \
                    round(
                        (end_element['basePoint2X'] - end_element['endX']) / (0.01 * (end_element['endX'] - start_element['startX'])))
            if abs(end_element['endY'] - start_element['startY']) > 0:
                curve_shape['p2']['y'] = \
                    round(
                        (end_element['basePoint2Y'] - end_element['endY']) / (0.01 * (end_element['endY'] - start_element['startY'])))
        return curve_shape

    @staticmethod
    def get_ellipse_features(gs, dimensions, offset_x, offset_y):
        ellipse_shape = {'shape': "ellipse"}
        if 'cx' in list(gs.keys()):
            ellipse_shape['cx'] = gs['cx']['abs'] + 0.01 * gs['cx'][
                'rel'] * dimensions['width'] + offset_x
        if 'cy' in list(gs.keys()):
            ellipse_shape['cy'] = gs['cy']['abs'] + 0.01 * gs['cy'][
                'rel'] * dimensions['height'] + offset_y
        if 'rx' in list(gs.keys()):
            ellipse_shape['rx'] = gs['rx']['abs'] + 0.01 * gs['rx'][
                'rel'] * dimensions['width']
        if 'ry' in list(gs.keys()):
            ellipse_shape['ry'] = gs['ry']['abs'] + \
                                  0.01 * gs['ry']['rel'] * dimensions['height']
        if 'ratio' in list(gs.keys()) and gs['ratio'] > 0.0:
            if (dimensions['width'] / dimensions['height']) <= gs['ratio']:
                ellipse_shape['rx'] = 0.5 * dimensions['width']
                ellipse_shape['ry'] = (0.5 * dimensions['width'] / gs['ratio'])
            else:
                ellipse_shape['ry'] = 0.5 * dimensions['height']
                ellipse_shape['rx'] = gs['ratio'] * 0.5 * dimensions['height']
        return ellipse_shape

    @staticmethod
    def get_rectangle_features(gs, dimensions, offset_x, offset_y):
        rectangle_shape = {'shape': "rectangle"}
        if 'x' in list(gs.keys()):
            rectangle_shape['x'] = gs['x']['abs'] + \
                                   0.01 * gs['x']['rel'] * dimensions['width'] + offset_x
        if 'y' in list(gs.keys()):
            rectangle_shape['y'] = gs['y']['abs'] + \
                                   0.01 * gs['y']['rel'] * dimensions['height'] + offset_y
        if 'width' in list(gs.keys()):
            rectangle_shape['width'] = gs['width']['abs'] + \
                                       0.01 * gs['width']['rel'] * dimensions['width']
        if 'height' in list(gs.keys()):
            rectangle_shape['height'] = gs['height']['abs'] + \
                                        0.01 * gs['height']['rel'] * dimensions['height']
        if 'ratio' in list(gs.keys()) and gs['ratio'] > 0.0:
            if (dimensions['width'] / dimensions['height']) <= gs['ratio']:
                rectangle_shape['width'] = dimensions['width']
                rectangle_shape['height'] = dimensions['height'] / gs['ratio']
                rectangle_shape['y'] += 0.5 * (dimensions['height'] - rectangle_shape['height'])
            else:
                rectangle_shape['height'] = dimensions['height']
                rectangle_shape['width'] = gs['ratio'] * dimensions['height']
                rectangle_shape['x'] += 0.5 * (dimensions['width'] - rectangle_shape['width'])
        if 'rx' in list(gs.keys()):
            rectangle_shape['rx'] = gs['rx']['abs'] + \
                                    0.01 * gs['rx']['rel'] * 0.5 * dimensions['width']
        if 'ry' in list(gs.keys()):
            rectangle_shape['ry'] = gs['ry']['abs'] + \
                                    0.01 * gs['ry']['rel'] * 0.5 * dimensions['height']
            return rectangle_shape

    @staticmethod
    def get_polygon_features(gs, dimensions, offset_x, offset_y):
        polygon_shape = {'shape': "polygon"}
        if 'vertices' in list(gs.keys()):
            points = []
            for v_index in range(len(gs['vertices'])):
                points.append({'x': gs['vertices'][v_index]['renderPointX']['abs'] + 0.01 *
                                    gs['vertices'][v_index]['renderPointX']['rel'] * dimensions['width'] + offset_x,
                               'y': gs['vertices'][v_index]['renderPointY']['abs'] + 0.01 *
                                    gs['vertices'][v_index]['renderPointY']['rel'] * dimensions['height'] + offset_y})
        polygon_shape['points'] = points
        return polygon_shape

    def get_node_text(self, text, go_bounding_box):
        text_shape = {'shape': "text"}
        if 'plainText' in list(text['features'].keys()):
            text_shape['plain-text'] = text['features']['plainText']
        if 'graphicalText' in list(text['features'].keys()):
            text_shape.update(self.get_text_features(text, go_bounding_box))
        return text_shape

    def get_text_features(self, text, go_bounding_box):
        features = {}
        if 'strokeColor' in list(text['features']['graphicalText'].keys()):
            features['color'] = \
                self.graph_info.find_color_value(text['features']['graphicalText']['strokeColor'])
        if 'fontFamily' in list(text['features']['graphicalText'].keys()):
            features['font-family'] = text['features']['graphicalText']['fontFamily']
        if 'fontWeight' in list(text['features']['graphicalText'].keys()):
            features['font-weight'] = text['features']['graphicalText']['fontWeight']
        if 'fontStyle' in list(text['features']['graphicalText'].keys()):
            features['font-style'] = text['features']['graphicalText']['fontStyle']
        if 'hTextAnchor' in list(text['features']['graphicalText'].keys()):
            features['horizontal-alignment'] = text['features']['graphicalText']['hTextAnchor']
        if 'vTextAnchor' in list(text['features']['graphicalText'].keys()):
            features['vertical-alignment'] = text['features']['graphicalText']['vTextAnchor']
        if 'boundingBox' in list(text['features'].keys()):
            features['x'] = text['features']['boundingBox']['x'] -\
                            (go_bounding_box['x'] + 0.5 * go_bounding_box['width'])
            features['y'] = text['features']['boundingBox']['y'] -\
                            (go_bounding_box['y'] + 0.5 * go_bounding_box['height'])
            features['width'] = text['features']['boundingBox']['width']
            features['height'] = text['features']['boundingBox']['height']
            if 'fontSize' in list(text['features']['graphicalText'].keys()):
                features['font-size'] = text['features']['graphicalText']['fontSize']['abs'] +\
                                        text['features']['boundingBox']['width'] * \
                                        text['features']['graphicalText']['fontSize']['rel']
        return features

    def get_arrow_heads(self, heads, style_name):
        line_ending_style = {'name': style_name + "_ArrowHead", 'category': "LineEnding", 'shapes': []}
        line_ending = self.graph_info.find_line_ending(heads['end'])
        if line_ending and 'graphicalShape' in list(line_ending['features'].keys())\
            and 'geometricShapes' in list(line_ending['features']['graphicalShape'].keys()):
            line_ending_style['shapes'] =\
                self.get_shape_style(line_ending,
                                     offset_x=line_ending['features']['boundingBox']['x'],
                                     offset_y=line_ending['features']['boundingBox']['y'])
        return line_ending_style

    def export(self, file_name="file"):
        position = {'x': self.graph_info.extents['minX'] + 0.5 * (self.graph_info.extents['maxX'] - self.graph_info.extents['minX']),
                    'y': self.graph_info.extents['minY'] + 0.5 * (self.graph_info.extents['maxY'] - self.graph_info.extents['minY'])}
        dimensions = {'width': self.graph_info.extents['maxX'] - self.graph_info.extents['minX'],
                      'height': self.graph_info.extents['maxY'] - self.graph_info.extents['minY']}
        graph_info = {'generated_by': "SBMLplot",
                      'name': pathlib(file_name).stem + "_graph",
                      'background-color': self.graph_info.background_color,
                      'position': position,
                      'dimensions': dimensions,
                      'nodes': self.nodes,
                      'edges': self.edges}
        with open(file_name.split('.')[0] + ".json", 'w', encoding='utf8') as js_file:
            json.dump(graph_info, js_file, indent=1)
        return graph_info

"""
sbml_graph_info = SBMLGraphInfoImportFromNetworkEditor()
f = open("/Users/home/Downloads/network1.json")
sbml_graph_info.extract_info(json.load(f))
sbml_export = SBMLGraphInfoExportToSBMLModel()
sbml_export.extract_graph_info(sbml_graph_info)
sbml_export.export("/Users/home/Downloads/Model.xml")
"""