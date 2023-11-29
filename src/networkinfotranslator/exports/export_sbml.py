from .export_base import NetworkInfoExportBase
import libsbml


class NetworkInfoExportToSBMLModel(NetworkInfoExportBase):
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
        self.layout.setId("NetworkInfoTranslator_Layout")

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
        self.global_render.setId("NetworkInfoTranslator_Global_Render")

        # local render
        lrplugin = self.layout.getPlugin("render")
        if lrplugin is None:
            print("[Fatal Error] Render Extension Level " + str(self.renderns.getLevel()) +
                  " Version " + str(self.renderns.getVersion()) +
                  " package version " + str(self.renderns.getPackageVersion()) +
                  " is not registered.")
            sys.exit(1)
        self.local_render = lrplugin.createLocalRenderInformation()
        self.local_render.setId("NetworkInfoTranslator_Local_Render")
        self.local_render.setReferenceRenderInformation("NetworkInfoTranslator_Global_Render")

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
            if species_reference['role'].lower() == "substrate" or species_reference['role'].lower() == "sidesubstrate" \
                    or species_reference['role'].lower() == "side substrate" \
                    or species_reference['role'].lower() == "reactant":
                sr = reaction.createReactant()
                self.check(sr.setConstant(True),
                           'set species_reference ' + species_reference['referenceId'] + ' "constant" attribute')
            elif species_reference['role'].lower() == "product" or species_reference[
                    'role'].lower() == "sideproduct" \
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
            elif species_reference['role'].lower() == "sidesubstrate" or species_reference[
                'role'].lower() == "side substrate" \
                    or species_reference['role'].lower() == "sidereactant" or species_reference[
                'role'].lower() == "side reactant":
                species_reference_glyph.setRole(libsbml.SPECIES_ROLE_SIDESUBSTRATE)
            elif species_reference['role'].lower() == "product":
                species_reference_glyph.setRole(libsbml.SPECIES_ROLE_PRODUCT)
            elif species_reference['role'].lower() == "sideproduct" or species_reference[
                'role'].lower() == "side product":
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
