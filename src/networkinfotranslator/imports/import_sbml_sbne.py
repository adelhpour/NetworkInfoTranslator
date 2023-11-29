from .import_base import NetworkInfoImportBase


class NetworkInfoImportFromSBMLModelUsingLibSBNE(NetworkInfoImportBase):
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
            if sbne.ne_ven_isSetBackgroundColor(veneer):
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
                text_features['text-name'] = sbne.ne_ne_getName(text['graphicalObject'])
            if sbne.ne_ne_isSetId(text['graphicalObject']):
                text_features['text-id'] = sbne.ne_ne_getId(text['graphicalObject'])
        if 'plainText' not in list(text_features.keys()):
            if 'text-name' in list(text_features.keys()):
                text_features['plainText'] = text_features['text-name']
            elif 'text-id' in list(text_features.keys()):
                text_features['plainText'] = text_features['text-id']
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