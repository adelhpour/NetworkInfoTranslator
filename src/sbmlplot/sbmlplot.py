import libsbne as sbne
import numpy as np
import math
import json
from pathlib import Path as pathlib
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse, Polygon, Path, PathPatch
import matplotlib.transforms as plttransform
import matplotlib.colors as mcolors
import matplotlib.cbook as cbook
from matplotlib.textpath import TextToPath
from matplotlib.font_manager import FontProperties

matplotlib.use('Agg')

colors = []
gradients = []
lineEndings = []
is_layout_modified = False
is_render_modified = False


class SBMLRenderer:
    def __init__(self, inputfilename=None, export_graph_info=False, export_figure_format=""):
        colors.clear()
        gradients.clear()
        lineEndings.clear()
        self.sbmlDocument = None
        self.layoutInfo = None
        self.renderInfo = None
        self.network = None
        self.veneer = None
        self.compartments = []
        self.species = []
        self.reactions = []
        self.sbml_figure, self.sbml_axes = plt.subplots()
        self.sbml_axes.invert_yaxis()
        self.extents = {'minX': 0, 'maxX': 0, 'minY': 0, 'maxY': 0}

        if inputfilename:
            # load sbml model
            self.load_sbml(inputfilename)

            # export info of the network as .js file
            if export_graph_info:
                self.create_graph_info(inputfilename)

            # render the network of the model and save it
            if export_figure_format:
                self.render_sbml(inputfilename, export_figure_format)

    def load_sbml(self, filename):
        # get SBML document from and .xml model file
        self.sbmlDocument = sbne.ne_doc_readSBML(filename)

        # get the layout info from the document
        self.load_layout_info()

        # get the render info from the document
        self.load_render_info()

    def load_layout_info(self):
        global is_layout_modified
        self.layoutInfo = sbne.ne_doc_processLayoutInfo(self.sbmlDocument)
        self.network = sbne.ne_li_getNetwork(self.layoutInfo)

        if self.network:
            # if layout is not specified
            if not sbne.ne_net_isLayoutSpecified(self.network):

                # implement layout algorithm
                sbne.ne_li_addLayoutFeaturesToNetowrk(self.layoutInfo)

                # set the layout modification flag as true
                is_layout_modified = True
            # if layout has already specified
            else:
                is_layout_modified = False

            # if now layout is specified
            if sbne.ne_net_isLayoutSpecified(self.network):
                # get compartments info
                for c_index in range(sbne.ne_net_getNumCompartments(self.network)):
                    compartment_ = {}
                    if sbne.ne_go_isSetGlyphId(sbne.ne_net_getCompartment(self.network, c_index)):
                        compartment_['compartmentGlyph'] = sbne.ne_net_getCompartment(self.network, c_index)
                        compartment_['referenceId'] = sbne.ne_ne_getId(compartment_['compartmentGlyph'])
                        compartment_['id'] = sbne.ne_go_getGlyphId(compartment_['compartmentGlyph'])
                        if sbne.ne_ne_isSetMetaId(compartment_['compartmentGlyph']):
                            compartment_['metaId'] = sbne.ne_ne_getMetaId(compartment_['compartmentGlyph'])

                        # set the text associated with the compartment
                        if sbne.ne_go_getNumTexts(compartment_['compartmentGlyph']):
                            compartment_['text'] = {}
                            compartment_['text']['textGlyph'] = sbne.ne_go_getText(compartment_['compartmentGlyph'], 0)
                            update_text_features(self.network, compartment_)

                        self.compartments.append(compartment_)

                # get species info
                for s_index in range(sbne.ne_net_getNumSpecies(self.network)):
                    species_ = {}
                    if sbne.ne_go_isSetGlyphId(sbne.ne_net_getSpecies(self.network, s_index)):
                        species_['speciesGlyph'] = sbne.ne_net_getSpecies(self.network, s_index)
                        species_['referenceId'] = sbne.ne_ne_getId(species_['speciesGlyph'])
                        species_['id'] = sbne.ne_go_getGlyphId(species_['speciesGlyph'])
                        if sbne.ne_ne_isSetMetaId(species_['speciesGlyph']):
                            species_['metaId'] = sbne.ne_ne_getMetaId(species_['speciesGlyph'])

                        # set the compartment
                        if sbne.ne_spc_isSetCompartment(species_['speciesGlyph']):
                            for c in self.compartments:
                                if sbne.ne_spc_getCompartment(species_['speciesGlyph']) == c['referenceId']:
                                    species_['compartment'] = c['id']
                                    break

                        # set the text associated with the species
                        if sbne.ne_go_getNumTexts(species_['speciesGlyph']):
                            species_['text'] = {}
                            species_['text']['textGlyph'] = sbne.ne_go_getText(species_['speciesGlyph'], 0)
                            update_text_features(self.network, species_)

                        self.species.append(species_)

                # get reactions info
                for r_index in range(sbne.ne_net_getNumReactions(self.network)):
                    reaction_ = {}
                    if sbne.ne_go_isSetGlyphId(sbne.ne_net_getReaction(self.network, r_index)):
                        reaction_['reactionGlyph'] = sbne.ne_net_getReaction(self.network, r_index)
                        reaction_['referenceId'] = sbne.ne_ne_getId(reaction_['reactionGlyph'])
                        reaction_['id'] = sbne.ne_go_getGlyphId(reaction_['reactionGlyph'])
                        if sbne.ne_ne_isSetMetaId(reaction_['reactionGlyph']):
                            reaction_['metaId'] = sbne.ne_ne_getMetaId(reaction_['reactionGlyph'])

                        # set the compartment
                        r_compartment = sbne.ne_rxn_findCompartment(reaction_['reactionGlyph'])
                        if r_compartment:
                            for c in self.compartments:
                                if r_compartment == c['referenceId']:
                                    reaction_['compartment'] = c['id']
                                    break

                        # set the text associated with the reaction
                        if sbne.ne_go_getNumTexts(reaction_['reactionGlyph']):
                            reaction_['text'] = {}
                            reaction_['text']['textGlyph'] = sbne.ne_go_getText(reaction_['reactionGlyph'], 0)
                            update_text_features(self.network, reaction_)

                        # get species reference info
                        species_references = []
                        for sr_index in range(sbne.ne_rxn_getNumSpeciesReferences(reaction_['reactionGlyph'])):
                            species_reference_ = {}
                            if sbne.ne_go_isSetGlyphId(sbne.ne_rxn_getSpeciesReference(
                                    reaction_['reactionGlyph'], sr_index)):
                                species_reference_['sReferenceGlyph'] = sbne.ne_rxn_getSpeciesReference(
                                    reaction_['reactionGlyph'], sr_index)
                                species_reference_['id'] = \
                                    sbne.ne_go_getGlyphId(species_reference_['sReferenceGlyph'])
                                species_reference_['referenceId'] = \
                                    sbne.ne_ne_getId(species_reference_['sReferenceGlyph'])
                                if sbne.ne_ne_isSetMetaId(species_reference_['sReferenceGlyph']):
                                    species_reference_['metaId'] = \
                                        sbne.ne_ne_getMetaId(species_reference_['sReferenceGlyph'])
                                if sbne.ne_sr_isSetSpecies(species_reference_['sReferenceGlyph']):
                                    species_reference_['species'] = sbne.ne_go_getGlyphId(sbne.ne_sr_getSpecies(
                                        species_reference_['sReferenceGlyph']))
                                if sbne.ne_sr_isSetRole(species_reference_['sReferenceGlyph']):
                                    species_reference_['role'] = sbne.ne_sr_getRoleAsString(
                                        species_reference_['sReferenceGlyph'])
                                species_references.append(species_reference_)
                        reaction_['speciesReferences'] = species_references
                        self.reactions.append(reaction_)

    def load_render_info(self):
        global is_render_modified
        if self.network:
            self.renderInfo = sbne.ne_doc_processRenderInfo(self.sbmlDocument)
            self.veneer = sbne.ne_ri_getVeneer(self.renderInfo)

            # if render is not specified
            if not sbne.ne_ven_isRenderSpecified(self.veneer):

                # implement layout algorithm
                sbne.ne_ri_addDefaultRenderFeaturesToVeneer(self.renderInfo)

                # set the render modification flag as true
                is_render_modified = True
            # if layout has already specified
            else:
                is_render_modified = False

            # if now render is specified
            if sbne.ne_ven_isRenderSpecified(self.veneer):
                # get colors info
                for c_index in range(sbne.ne_ven_getNumColors(self.veneer)):
                    color_ = {'colorDefinition': sbne.ne_ven_getColor(self.veneer, c_index)}
                    color_['id'] = sbne.ne_ve_getId(color_['colorDefinition'])
                    colors.append(color_)
                    update_color_features(color_)

                # get gradients info
                for g_index in range(sbne.ne_ven_getNumGradients(self.veneer)):
                    gradient_ = {'gradientBase': sbne.ne_ven_getGradient(self.veneer, g_index)}
                    gradient_['id'] = sbne.ne_ve_getId(gradient_['gradientBase'])
                    gradients.append(gradient_)
                    update_gradient_features(gradient_)

                # get line ending info
                for le_index in range(sbne.ne_ven_getNumLineEndings(self.veneer)):
                    line_ending_ = {'lineEnding': sbne.ne_ven_getLineEnding(self.veneer, le_index)}
                    line_ending_['id'] = sbne.ne_ve_getId(line_ending_['lineEnding'])
                    lineEndings.append(line_ending_)
                    update_line_ending_features(line_ending_)

                # get compartments style from veneer
                for c_index in range(len(self.compartments)):
                    self.compartments[c_index]['style'] = \
                        sbne.ne_ven_findStyle(self.veneer, self.compartments[c_index]['compartmentGlyph'])

                    # get text style from veneer
                    if 'text' in list(self.compartments[c_index].keys())\
                            and 'textGlyph' in list(self.compartments[c_index]['text'].keys()):
                        self.compartments[c_index]['text']['style'] = \
                            sbne.ne_ven_findStyle(self.veneer, self.compartments[c_index]['text']['textGlyph'],
                                                  sbne.ST_TYPE_COMP)

                    # update compartment features
                    update_compartment_features(self.compartments[c_index], self.extents)

                    # display compartment
                    if 'features' in list(self.compartments[c_index].keys()):
                        draw_graphical_shape(self.sbml_axes, self.compartments[c_index]['features'], z_order=0)

                    # display compartment text
                    if 'text' in list(self.compartments[c_index].keys()) and \
                            'features' in list(self.compartments[c_index]['text'].keys()):
                        draw_text(self.sbml_axes, self.compartments[c_index]['text']['features'])

                # get species style from veneer
                for s_index in range(len(self.species)):
                    self.species[s_index]['style'] = \
                        sbne.ne_ven_findStyle(self.veneer, self.species[s_index]['speciesGlyph'])

                    # get text style from veneer
                    if 'text' in list(self.species[s_index].keys())\
                            and 'textGlyph' in list(self.species[s_index]['text'].keys()):
                        self.species[s_index]['text']['style'] =\
                            sbne.ne_ven_findStyle(self.veneer, self.species[s_index]['text']['textGlyph'],
                                                  sbne.ST_TYPE_TXT)

                    # update species features
                    update_species_features(self.species[s_index])

                    # display species
                    if 'features' in list(self.species[s_index].keys()):
                        draw_graphical_shape(self.sbml_axes, self.species[s_index]['features'], z_order=4)

                    # display species text
                    if 'text' in list(self.species[s_index].keys()) and \
                            'features' in list(self.species[s_index]['text'].keys()):
                        draw_text(self.sbml_axes, self.species[s_index]['text']['features'])

                # get reactions style from veneer
                for r_index in range(len(self.reactions)):
                    self.reactions[r_index]['style'] = \
                        sbne.ne_ven_findStyle(self.veneer, self.reactions[r_index]['reactionGlyph'])

                    # update reaction features
                    update_reaction_features(self.reactions[r_index])

                    # display reaction
                    if 'features' in list(self.reactions[r_index].keys()):
                        # display reaction curve
                        if 'curve' in list(self.reactions[r_index]['features']):
                            draw_curve(self.sbml_axes, self.reactions[r_index]['features'], z_order=3)
                        # display reaction graphical shape
                        elif 'boundingBox' in list(self.reactions[r_index]['features']):
                            draw_graphical_shape(self.sbml_axes, self.reactions[r_index]['features'], z_order=3)

                    # get species references style from veneer
                    if 'speciesReferences' in list(self.reactions[r_index].keys()):
                        for sr_index in range(len(self.reactions[r_index]['speciesReferences'])):
                            self.reactions[r_index]['speciesReferences'][sr_index]['style'] = \
                                sbne.ne_ven_findStyle(self.veneer,
                                                      self.reactions[r_index]['speciesReferences']
                                                      [sr_index]['sReferenceGlyph'])
                            # update species reference features
                            update_species_reference_features(self.reactions[r_index]['speciesReferences'][sr_index])

                            if 'features' in list(self.reactions[r_index]['speciesReferences'][sr_index]):
                                # display species reference
                                draw_curve(self.sbml_axes,
                                           self.reactions[r_index]['speciesReferences'][sr_index]['features'],
                                           z_order=1)

                                # display line endings
                                draw_line_endings(self.sbml_axes, self.reactions[
                                    r_index]['speciesReferences'][sr_index]['features'])

    def create_graph_info(self, filename):
        nodes = []
        edges = []
        styles = []
        for c in self.compartments:
            if 'id' in list(c.keys()) and 'referenceId' in list(c.keys()):
                node_ = dict(data={'id': c['referenceId'] + "_" + c['id'],
                                   'referenceId': c['referenceId']})
                if 'metaId' in list(c.keys()):
                    node_['data']['metaId'] = c['metaId']
                style_ = dict(selector="node[id = '" + c['referenceId'] + "_" + c['id'] + "']",
                              css={'content': 'data(name)'})
                get_node_features(c, node_, style_)
                node_['selected'] = False
                nodes.append(node_)
                styles.append(style_)
                styles.append(dict(selector="node[id = '" + c['referenceId'] + "_" + c['id'] + "']:selected",
                                   css={'border-color': '#4169e1'}))

        for s in self.species:
            if 'id' in list(s.keys()) and 'referenceId' in list(s.keys()):
                node_ = dict(data={'id': s['referenceId'] + "_" + s['id'],
                                   'referenceId': s['referenceId']})
                if 'metaId' in list(s.keys()):
                    node_['data']['metaId'] = s['metaId']
                style_ = dict(selector="node[id = '" + s['referenceId'] + "_" + s['id'] + "']",
                              css={'content': 'data(name)'})
                if 'compartment' in list(s.keys()):
                    for c in self.compartments:
                        if c['id'] == s['compartment']:
                            node_['data']['parent'] = c['referenceId'] + "_" + c['id']
                            break
                get_node_features(s, node_, style_)
                node_['selected'] = False
                nodes.append(node_)
                styles.append(style_)
                styles.append(dict(selector="node[id = '" + s['referenceId'] + "_" + s['id'] + "']:selected",
                              css={'background-color': '#4169e1'}))

        for r in self.reactions:
            if 'id' in list(r.keys()) and 'referenceId' in list(r.keys()):
                node_ = dict(data={'id': r['referenceId'] + "_" + r['id'],
                                   'referenceId': r['referenceId']})
                if 'metaId' in list(r.keys()):
                    node_['data']['metaId'] = r['metaId']
                r_style_ = dict(selector="node[id = '" + r['referenceId'] + "_" + r['id'] + "']",
                                css={'content': ""})
                if 'compartment' in list(r.keys()):
                    for c in self.compartments:
                        if c['id'] == r['compartment']:
                            node_['data']['parent'] = c['referenceId'] + "_" + c['id']
                            break
                get_node_features(r, node_, r_style_)
                node_['selected'] = False
                nodes.append(node_)
                styles.append(r_style_)
                styles.append(dict(selector="node[id = '" + r['referenceId'] + "_" + r['id'] + "']:selected",
                                   css={'border-color': '#4169e1'}))

                for sr in r['speciesReferences']:
                    if 'id' in list(sr.keys()) and 'referenceId' in list(sr.keys()) and 'species' in list(sr.keys()):
                        edge_ = dict(data={'id': sr['referenceId'] + "_" + sr['id'],
                                           'referenceId': sr['referenceId']})
                        if 'metaId' in list(sr.keys()):
                            edge_['data']['metaId'] = sr['metaId']
                        sr_style_ = dict(selector="edge[id = '" + sr['referenceId'] + "_" + sr['id'] + "']",
                                         css={'content': "", 'curve-style': 'bezier'})

                        species = {}
                        for s in self.species:
                            if s['id'] == sr['species']:
                                species = s
                                break
                        if 'role' in list(sr.keys()):
                            if sr['role'] == "product" or sr['role'] == "side product":
                                edge_['data']['source'] = r['referenceId'] + "_" + r['id']
                                edge_['data']['target'] = species['referenceId'] + "_" + species['id']
                            else:
                                edge_['data']['source'] = species['referenceId'] + "_" + species['id']
                                edge_['data']['target'] = r['referenceId'] + "_" + r['id']

                        get_edge_features(sr, edge_, sr_style_)
                        edge_['selected'] = False
                        edges.append(edge_)
                        styles.append(sr_style_)
                        styles.append(dict(selector="edge[id = '" + sr['referenceId'] + "_" + sr['id'] + "']:selected",
                                           css={'line-color': '#4169e1',
                                                'source-arrow-color': '#4169e1',
                                                'target-arrow-color': '#4169e1'}))

        graph_info = dict(data={'generated_by': "SBMLplot", 'name': pathlib(filename).stem,
                                'shared_name': pathlib(filename).stem, 'selected': True})
        graph_info['elements'] = {'nodes': nodes, 'edges': edges}
        graph_info['style'] = styles
        with open(filename.split('.')[0] + ".js", 'w', encoding='utf8') as js_file:
            js_file.write("graph_info = ")
            json.dump(graph_info, js_file, indent=1)
            js_file.write(";")

    def render_sbml(self, filename, export_figure_format):
        if export_figure_format in [".pdf", ".svg", ".png"]:
            if len(self.sbml_axes.patches):
                self.sbml_axes.set_aspect('equal')
                self.sbml_figure.set_size_inches(max(1.0, (self.extents['maxX'] - self.extents['minX']) / 72.0),
                                                 max(1.0, (self.extents['maxY'] - self.extents['minY']) / 72.0))

                plt.axis('equal')
                plt.axis('off')
                plt.tight_layout()
                self.sbml_figure.savefig(filename.split('.')[0] + export_figure_format, transparent=True, dpi=300)
                plt.close('all')


def update_color_features(color):
    color['features'] = {}
    if color['colorDefinition']:
        # get color value
        if sbne.ne_clr_isSetValue(color['colorDefinition']):
            color['features']['value'] = sbne.ne_clr_getValue(color['colorDefinition'])


def find_color_value(color_id, search_among_gradients=True):
    # search among the gradients
    if search_among_gradients:
        for g_index in range(len(gradients)):
            if color_id == gradients[g_index]['id'] and 'stops' in list(gradients[g_index]['features'].keys()):
                stop_colors = []
                for s_index in range(len(gradients[g_index]['features']['stops'])):
                    if 'color' in list(gradients[g_index]['features']['stops'][s_index].keys()):
                        stop_colors.append(mcolors.to_rgb(
                            find_color_value(gradients[g_index]['features']['stops'][s_index]['color'])))
                if len(stop_colors):
                    return mcolors.to_hex(np.average(np.array(stop_colors), axis=0).tolist())

    # search among the colors
    for c_index in range(len(colors)):
        if color_id == colors[c_index]['id'] and 'value' in list(colors[c_index]['features'].keys()):
            return colors[c_index]['features']['value']

    return color_id


def update_gradient_features(gradient):
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
                    {'rel': sbne.ne_rav_getRelativeValue(sbne.ne_gstp_getOffset(stop_['gradientStop']))}

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


def update_line_ending_features(line_ending):
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
                get_graphical_shape_features(sbne.ne_le_getGroup(line_ending['lineEnding']))

        # get enable rotation
        if sbne.ne_le_isSetEnableRotation(line_ending['lineEnding']):
            line_ending['features']['enableRotation'] = sbne.ne_le_getEnableRotation(line_ending['lineEnding'])


def find_line_ending(line_ending):
    for le_index in range(len(lineEndings)):
        if line_ending == lineEndings[le_index]['id']:
            return lineEndings[le_index]


def update_compartment_features(compartment, extents):
    compartment['features'] = {}
    if compartment['compartmentGlyph']:
        # get bounding box features
        if sbne.ne_go_isSetBoundingBox(compartment['compartmentGlyph']):
            bbox = sbne.ne_go_getBoundingBox(compartment['compartmentGlyph'])
            compartment['features']['boundingBox'] = {'x': sbne.ne_bb_getX(bbox), 'y': sbne.ne_bb_getY(bbox),
                                                      'width': sbne.ne_bb_getWidth(bbox),
                                                      'height': sbne.ne_bb_getHeight(bbox)}

            extents['minX'] = min(extents['minX'], compartment['features']['boundingBox']['x'])
            extents['maxX'] = max(extents['maxX'], compartment['features']['boundingBox']['x'] +
                                  compartment['features']['boundingBox']['width'])
            extents['minY'] = min(extents['minY'], compartment['features']['boundingBox']['y'])
            extents['maxY'] = max(extents['maxY'], compartment['features']['boundingBox']['y'] +
                                  compartment['features']['boundingBox']['height'])

        # get group features
        if 'style' in list(compartment.keys()) and sbne.ne_stl_isSetGroup(compartment['style']):
            compartment['features']['graphicalShape'] = \
                get_graphical_shape_features(sbne.ne_stl_getGroup(compartment['style']))

        # get text features
        if 'text' in list(compartment.keys()):
            compartment['text']['features'] = {}
            # get plain text
            if sbne.ne_gtxt_isSetPlainText(compartment['text']['textGlyph']):
                compartment['text']['features']['plainText'] =\
                    sbne.ne_gtxt_getPlainText(compartment['text']['textGlyph'])
            elif 'graphicalObject' in list(compartment['text'].keys()):
                if sbne.ne_ne_isSetName(compartment['text']['graphicalObject']):
                    compartment['text']['features']['plainText'] =\
                        sbne.ne_ne_getName(compartment['text']['graphicalObject'])
                else:
                    compartment['text']['features']['plainText'] = \
                        sbne.ne_ne_getId(compartment['text']['graphicalObject'])
            # get bounding box features of the text glyph
            if sbne.ne_go_isSetBoundingBox(compartment['text']['textGlyph']):
                bbox = sbne.ne_go_getBoundingBox(compartment['text']['textGlyph'])
                compartment['text']['features']['boundingBox'] = {'x': sbne.ne_bb_getX(bbox),
                                                                  'y': sbne.ne_bb_getY(bbox),
                                                                  'width': sbne.ne_bb_getWidth(bbox),
                                                                  'height': sbne.ne_bb_getHeight(bbox)}
            # get bounding box features of the species glyph
            else:
                compartment['text']['features']['boundingBox'] = compartment['features']['boundingBox']

            # get group features
            if 'style' in list(compartment['text'].keys()) \
                    and sbne.ne_stl_isSetGroup(compartment['text']['style']):
                compartment['text']['features']['graphicalText'] = \
                    get_text_features(sbne.ne_stl_getGroup(compartment['text']['style']))


def update_species_features(species):
    species['features'] = {}
    if species['speciesGlyph']:
        # get bounding box features
        if sbne.ne_go_isSetBoundingBox(species['speciesGlyph']):
            bbox = sbne.ne_go_getBoundingBox(species['speciesGlyph'])
            species['features']['boundingBox'] = {'x': sbne.ne_bb_getX(bbox), 'y': sbne.ne_bb_getY(bbox),
                                                  'width': sbne.ne_bb_getWidth(bbox),
                                                  'height': sbne.ne_bb_getHeight(bbox)}

        # get group features
        if 'style' in list(species.keys()) and sbne.ne_stl_isSetGroup(species['style']):
            species['features']['graphicalShape'] = \
                get_graphical_shape_features(sbne.ne_stl_getGroup(species['style']))

        # get text features
        if 'text' in list(species.keys()):
            species['text']['features'] = {}
            # get plain text
            if sbne.ne_gtxt_isSetPlainText(species['text']['textGlyph']):
                species['text']['features']['plainText'] = sbne.ne_gtxt_getPlainText(species['text']['textGlyph'])
            elif 'graphicalObject' in list(species['text'].keys()):
                if sbne.ne_ne_isSetName(species['text']['graphicalObject']):
                    species['text']['features']['plainText'] = \
                        sbne.ne_ne_getName(species['text']['graphicalObject'])
                else:
                    species['text']['features']['plainText'] = \
                        sbne.ne_ne_getId(species['text']['graphicalObject'])
            # get bounding box features of the text glyph
            if 'id' in list(species['text'].keys()) and sbne.ne_go_isSetBoundingBox(species['text']['textGlyph']):
                bbox = sbne.ne_go_getBoundingBox(species['text']['textGlyph'])
                species['text']['features']['boundingBox'] = {'x': sbne.ne_bb_getX(bbox),
                                                              'y': sbne.ne_bb_getY(bbox),
                                                              'width': sbne.ne_bb_getWidth(bbox),
                                                              'height': sbne.ne_bb_getHeight(bbox)}
            # get bounding box features of the species glyph
            else:
                species['text']['features']['boundingBox'] = species['features']['boundingBox']

            # get group features
            if 'style' in list(species['text'].keys()) \
                    and sbne.ne_stl_isSetGroup(species['text']['style']):
                species['text']['features']['graphicalText'] = \
                    get_text_features(sbne.ne_stl_getGroup(species['text']['style']))

            # fit text to its bounding box
            fit_text_to_bbox(species['text']['features'])


def update_reaction_features(reaction):
    reaction['features'] = {}
    if reaction['reactionGlyph']:
        # get curve features
        if sbne.ne_rxn_isSetCurve(reaction['reactionGlyph']):
            crv = sbne.ne_rxn_getCurve(reaction['reactionGlyph'])

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
                bbox = sbne.ne_rxn_getExtentBox(reaction['reactionGlyph'])
                if (bbox):
                    reaction['features']['boundingBox'] = {'x': sbne.ne_bb_getX(bbox) + 0.5 * sbne.ne_bb_getWidth(bbox),
                                                           'y': sbne.ne_bb_getY(bbox) + 0.5 * sbne.ne_bb_getHeight(bbox),
                                                           'width': 15.0,
                                                           'height': 15.0}
        # get bounding box features
        elif sbne.ne_go_isSetBoundingBox(reaction['reactionGlyph']):
            bbox = sbne.ne_go_getBoundingBox(reaction['reactionGlyph'])
            reaction['features']['boundingBox'] = {'x': sbne.ne_bb_getX(bbox), 'y': sbne.ne_bb_getY(bbox),
                                                   'width': sbne.ne_bb_getWidth(bbox),
                                                   'height': sbne.ne_bb_getHeight(bbox)}
        # get group features
        if 'style' in list(reaction.keys()) and sbne.ne_stl_isSetGroup(reaction['style']):
            if 'curve' in list(reaction['features'].keys()):
                reaction['features']['graphicalCurve'] = \
                    get_curve_features(sbne.ne_stl_getGroup(reaction['style']))
            if 'boundingBox' in list(reaction['features'].keys()):
                reaction['features']['graphicalShape'] = \
                    get_graphical_shape_features(sbne.ne_stl_getGroup(reaction['style']))


def update_species_reference_features(species_reference):
    species_reference['features'] = {}
    if species_reference['sReferenceGlyph']:
        # get curve features
        if sbne.ne_sr_isSetCurve(species_reference['sReferenceGlyph']):
            crv = sbne.ne_sr_getCurve(species_reference['sReferenceGlyph'])

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
                get_curve_features(sbne.ne_stl_getGroup(species_reference['style']))


def update_text_features(network, go):
    if 'text' in list(go.keys()) and 'textGlyph' in list(go['text'].keys()):
        if sbne.ne_go_isSetGlyphId(go['text']['textGlyph']):
            go['text']['id'] = sbne.ne_go_getGlyphId(go['text']['textGlyph'])
        if sbne.ne_gtxt_isSetGraphicalObjectId(go['text']['textGlyph']):
            go['text']['graphicalObject'] = \
                sbne.ne_net_getNetworkElement(network, sbne.ne_gtxt_getGraphicalObjectId(go['text']['textGlyph']))
        elif sbne.ne_gtxt_isSetOriginOfTextId(go['text']['textGlyph']):
            go['text']['graphicalObject'] = \
                sbne.ne_net_getNetworkElement(network, sbne.ne_gtxt_getOriginOfTextId(go['text']['textGlyph']))


def get_graphical_shape_features(group):
    graphical_shape_features = {}
    if group:
        # get stroke color
        if sbne.ne_grp_isSetStrokeColor(group):
            graphical_shape_features['strokeColor'] = sbne.ne_grp_getStrokeColor(group)

        # get stroke width
        if sbne.ne_grp_isSetStrokeWidth(group):
            graphical_shape_features['strokeWidth'] = sbne.ne_grp_getStrokeWidth(group)

        # get stroke dash array
        if sbne.ne_grp_isSetStrokeDashArray(group):
            dash_array = []
            for d_index in range(sbne.ne_grp_getNumStrokeDashes(group)):
                dash_array.append(sbne.ne_grp_getStrokeDash(group, d_index))
            graphical_shape_features['strokeDashArray'] = tuple(dash_array)

        # get fill color
        if sbne.ne_grp_isSetFillColor(group):
            graphical_shape_features['fillColor'] = sbne.ne_grp_getFillColor(group)

        # get fill rule
        if sbne.ne_grp_isSetFillRule(group):
            graphical_shape_features['fillRule'] = sbne.ne_grp_getFillRule(group)

        # get geometric shapes
        if sbne.ne_grp_getNumGeometricShapes(group):
            geometric_shapes = []
            for gs_index in range(sbne.ne_grp_getNumGeometricShapes(group)):
                gs = sbne.ne_grp_getGeometricShape(group, gs_index)
                geometric_shape_features = {}

                # get geometric shape general features
                # get stroke color
                if sbne.ne_gs_isSetStrokeColor(gs):
                    geometric_shape_features['strokeColor'] = sbne.ne_gs_getStrokeColor(gs)

                # get stroke width
                if sbne.ne_gs_isSetStrokeWidth(gs):
                    geometric_shape_features['strokeWidth'] = sbne.ne_gs_getStrokeWidth(gs)

                # get stroke dash array
                if sbne.ne_gs_isSetStrokeDashArray(gs):
                    dash_array = []
                    for d_index in range(sbne.ne_gs_getNumStrokeDashes(gs)):
                        dash_array.append(sbne.ne_gs_getStrokeDash(gs, d_index))
                    geometric_shape_features['strokeDashArray'] = tuple(dash_array)

                # get geometric shape specific features
                get_geometric_shape_exclusive_features(gs, geometric_shape_features)

                geometric_shapes.append(geometric_shape_features)

            graphical_shape_features['geometricShapes'] = geometric_shapes

    return graphical_shape_features


def get_curve_features(group):
    curve_features = {}
    if group:
        # get stroke color
        if sbne.ne_grp_isSetStrokeColor(group):
            curve_features['strokeColor'] = sbne.ne_grp_getStrokeColor(group)

        # get stroke width
        if sbne.ne_grp_isSetStrokeWidth(group):
            curve_features['strokeWidth'] = sbne.ne_grp_getStrokeWidth(group)

        # get stroke dash array
        if sbne.ne_grp_isSetStrokeDashArray(group):
            dash_array = []
            for d_index in range(sbne.ne_grp_getNumStrokeDashes(group)):
                dash_array.append(sbne.ne_grp_getStrokeDash(group, d_index))
            curve_features['strokeDashArray'] = tuple(dash_array)

        # get heads
        heads_ = {}
        if sbne.ne_grp_isSetStartHead(group):
            heads_['start'] = sbne.ne_grp_getStartHead(group)
        if sbne.ne_grp_isSetEndHead(group):
            heads_['end'] = sbne.ne_grp_getEndHead(group)
        if heads_:
            curve_features['heads'] = heads_

    return curve_features


def get_text_features(group):
    text_features = {}
    if group:
        # get stroke color
        if sbne.ne_grp_isSetStrokeColor(group):
            text_features['strokeColor'] = sbne.ne_grp_getStrokeColor(group)

        # get font family
        if sbne.ne_grp_isSetFontFamily(group):
            text_features['fontFamily'] = sbne.ne_grp_getFontFamily(group)

        # get font size
        if sbne.ne_grp_isSetFontSize(group):
            rel_abs_vec = sbne.ne_grp_getFontSize(group)
            text_features['fontSize'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                         'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get font weight
        if sbne.ne_grp_isSetFontWeight(group):
            text_features['fontWeight'] = sbne.ne_grp_getFontWeight(group)

        # get font style
        if sbne.ne_grp_isSetFontStyle(group):
            text_features['fontStyle'] = sbne.ne_grp_getFontStyle(group)

        # get horizontal text anchor
        if sbne.ne_grp_isSetHTextAnchor(group):
            text_features['hTextAnchor'] = sbne.ne_grp_getHTextAnchor(group)

        # get vertical text anchor
        if sbne.ne_grp_isSetVTextAnchor(group):
            text_features['vTextAnchor'] = sbne.ne_grp_getVTextAnchor(group)

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

            text_features['geometricShapes'] = geometric_shapes

    return text_features


def get_geometric_shape_exclusive_features(gs, geometric_shape_features):
    # get image shape features
    if sbne.ne_gs_getShape(gs) == 0:
        # set shape
        geometric_shape_features['shape'] = "image"

        # get position x
        if sbne.ne_img_isSetPositionX(gs):
            rel_abs_vec = sbne.ne_img_getPositionX(gs)
            geometric_shape_features['x'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                             'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get position y
        if sbne.ne_img_isSetPositionY(gs):
            rel_abs_vec = sbne.ne_img_getPositionY(gs)
            geometric_shape_features['y'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                             'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension width
        if sbne.ne_img_isSetDimensionWidth(gs):
            rel_abs_vec = sbne.ne_img_getDimensionWidth(gs)
            geometric_shape_features['width'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                                 'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension height
        if sbne.ne_img_isSetDimensionHeight(gs):
            rel_abs_vec = sbne.ne_img_getDimensionHeight(gs)
            geometric_shape_features['height'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                                  'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get href
        if sbne.ne_img_isSetHref(gs):
            geometric_shape_features['href'] = sbne.ne_img_getHref(gs)

    # get render curve shape features
    if sbne.ne_gs_getShape(gs) == 1:
        # set shape
        geometric_shape_features['shape'] = "renderCurve"

        vertices_ = []
        for v_index in range(sbne.ne_rc_getNumVertices(gs)):
            vertex = sbne.ne_rc_getVertex(gs, v_index)
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

        geometric_shape_features['vertices'] = vertices_

    # get text shape features
    if sbne.ne_gs_getShape(gs) == 2:
        # set shape
        geometric_shape_features['shape'] = "text"

        # get position x
        if sbne.ne_txt_isSetPositionX(gs):
            rel_abs_vec = sbne.ne_txt_getPositionX(gs)
            geometric_shape_features['x'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                             'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get position y
        if sbne.ne_txt_isSetPositionY(gs):
            rel_abs_vec = sbne.ne_txt_getPositionY(gs)
            geometric_shape_features['y'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                             'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get font family
        if sbne.ne_txt_isSetFontFamily(gs):
            geometric_shape_features['fontFamily'] = sbne.ne_txt_getFontFamily(gs)

        # get font size
        if sbne.ne_txt_isSetFontSize(gs):
            rel_abs_vec = sbne.ne_txt_getFontSize(gs)
            geometric_shape_features['fontSize'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                                    'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get font weight
        if sbne.ne_txt_isSetFontWeight(gs):
            geometric_shape_features['fontWeight'] = sbne.ne_txt_getFontWeight(gs)

        # get font style
        if sbne.ne_txt_isSetFontStyle(gs):
            geometric_shape_features['fontStyle'] = sbne.ne_grp_getFontStyle(gs)

        # get horizontal text anchor
        if sbne.ne_txt_isSetHTextAnchor(gs):
            geometric_shape_features['hTextAnchor'] = sbne.ne_txt_getHTextAnchor(gs)

        # get vertical text anchor
        if sbne.ne_txt_isSetVTextAnchor(gs):
            geometric_shape_features['vTextAnchor'] = sbne.ne_txt_getVTextAnchor(gs)

    # get rectangle shape features
    elif sbne.ne_gs_getShape(gs) == 3:
        # set shape
        geometric_shape_features['shape'] = "rectangle"

        # get fill color
        if sbne.ne_gs_isSetFillColor(gs):
            geometric_shape_features['fillColor'] = sbne.ne_gs_getFillColor(gs)

        # get position x
        if sbne.ne_rec_isSetPositionX(gs):
            rel_abs_vec = sbne.ne_rec_getPositionX(gs)
            geometric_shape_features['x'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                             'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get position y
        if sbne.ne_rec_isSetPositionY(gs):
            rel_abs_vec = sbne.ne_rec_getPositionY(gs)
            geometric_shape_features['y'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                             'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension width
        if sbne.ne_rec_isSetDimensionWidth(gs):
            rel_abs_vec = sbne.ne_rec_getDimensionWidth(gs)
            geometric_shape_features['width'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                                 'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension height
        if sbne.ne_rec_isSetDimensionHeight(gs):
            rel_abs_vec = sbne.ne_rec_getDimensionHeight(gs)
            geometric_shape_features['height'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                                  'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get corner curvature radius rx
        if sbne.ne_rec_isSetCornerCurvatureRX(gs):
            rel_abs_vec = sbne.ne_rec_getCornerCurvatureRX(gs)
            geometric_shape_features['rx'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                              'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get corner curvature radius ry
        if sbne.ne_rec_isSetCornerCurvatureRY(gs):
            rel_abs_vec = sbne.ne_rec_getCornerCurvatureRY(gs)
            geometric_shape_features['ry'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                              'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get width/height ratio
        if sbne.ne_rec_isSetRatio(gs):
            geometric_shape_features['ratio'] = sbne.ne_rec_getRatio(gs)

    # get ellipse shape features
    elif sbne.ne_gs_getShape(gs) == 4:
        # set shape
        geometric_shape_features['shape'] = "ellipse"

        # get fill color
        if sbne.ne_gs_isSetFillColor(gs):
            geometric_shape_features['fillColor'] = sbne.ne_gs_getFillColor(gs)

        # get position cx
        if sbne.ne_elp_isSetPositionCX(gs):
            rel_abs_vec = sbne.ne_elp_getPositionCX(gs)
            geometric_shape_features['cx'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                              'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get position cy
        if sbne.ne_elp_isSetPositionCY(gs):
            rel_abs_vec = sbne.ne_elp_getPositionCY(gs)
            geometric_shape_features['cy'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                              'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension rx
        if sbne.ne_elp_isSetDimensionRX(gs):
            rel_abs_vec = sbne.ne_elp_getDimensionRX(gs)
            geometric_shape_features['rx'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                              'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get dimension ry
        if sbne.ne_elp_isSetDimensionRY(gs):
            rel_abs_vec = sbne.ne_elp_getDimensionRY(gs)
            geometric_shape_features['ry'] = {'abs': sbne.ne_rav_getAbsoluteValue(rel_abs_vec),
                                              'rel': sbne.ne_rav_getRelativeValue(rel_abs_vec)}

        # get radius ratio
        if sbne.ne_elp_isSetRatio(gs):
            geometric_shape_features['ratio'] = sbne.ne_elp_getRatio(gs)

    # get polygon shape features
    elif sbne.ne_gs_getShape(gs) == 5:
        # set shape
        geometric_shape_features['shape'] = "polygon"

        # get fill color
        if sbne.ne_gs_isSetFillColor(gs):
            geometric_shape_features['fillColor'] = sbne.ne_gs_getFillColor(gs)

        # get fill rule
        if sbne.ne_gs_isSetFillRule(gs):
            geometric_shape_features['fillRule'] = sbne.ne_gs_getFillRule(gs)

        vertices_ = []
        for v_index in range(sbne.ne_plg_getNumVertices(gs)):
            vertex = sbne.ne_plg_getVertex(gs, v_index)
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

        geometric_shape_features['vertices'] = vertices_


def draw_graphical_shape(ax, features, offest_x=0.0, offest_y=0.0, slope=0.0, z_order=0):
    if 'boundingBox' in list(features.keys()):
        if (offest_x or offest_y) and slope:
            offest_x += 1.5 * math.cos(slope)
            offest_y += 1.5 * math.sin(slope)
        bbox_x = features['boundingBox']['x'] + offest_x
        bbox_y = features['boundingBox']['y'] + offest_y
        bbox_width = features['boundingBox']['width']
        bbox_height = features['boundingBox']['height']

        # default features
        stroke_color = 'black'
        stroke_width = '1.0'
        stroke_dash_array = 'solid'
        fill_color = 'white'

        if 'graphicalShape' in list(features.keys()):
            if 'strokeColor' in list(features['graphicalShape'].keys()):
                stroke_color = features['graphicalShape']['strokeColor']
            if 'strokeWidth' in list(features['graphicalShape'].keys()):
                stroke_width = features['graphicalShape']['strokeWidth']
            if 'strokeDashArray' in list(features['graphicalShape'].keys()):
                stroke_dash_array = (0, features['graphicalShape']['strokeDashArray'])
            if 'fillColor' in list(features['graphicalShape'].keys()):
                fill_color = features['graphicalShape']['fillColor']

            if 'geometricShapes' in list(features['graphicalShape'].keys()):
                for gs_index in range(len(features['graphicalShape']['geometricShapes'])):
                    # draw an image
                    if features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'image':
                        image_shape = features['graphicalShape']['geometricShapes'][gs_index]

                        # default features
                        position_x = bbox_x
                        position_y = bbox_y
                        dimension_width = bbox_width
                        dimension_height = bbox_height

                        if 'x' in list(image_shape.keys()):
                            position_x += image_shape['x']['abs'] + \
                                          0.01 * image_shape['x']['rel'] * bbox_width
                        if 'y' in list(image_shape.keys()):
                            position_y += image_shape['y']['abs'] + \
                                          0.01 * image_shape['y']['rel'] * bbox_height
                        if 'width' in list(image_shape.keys()):
                            dimension_width = image_shape['width']['abs'] + \
                                              0.01 * image_shape['width']['rel'] * bbox_width
                        if 'height' in list(image_shape.keys()):
                            dimension_height = image_shape['height']['abs'] + \
                                               0.01 * image_shape['height']['rel'] * bbox_height

                        # add a rounded rectangle to plot
                        if 'href' in list(image_shape.keys()):
                            with cbook.get_sample_data(image_shape['href']) as image_file:
                                image = plt.imread(image_file)
                                image_axes = ax.imshow(image)
                                image_axes.set_extent([position_x, position_x + dimension_width, position_y +
                                                       dimension_height, position_y])
                                image_axes.set_zorder(z_order)
                                if offest_x or offest_y:
                                    image_axes.set_transform(plttransform.Affine2D().
                                                             rotate_around(offest_x, offest_y, slope) + ax.transData)
                                else:
                                    image_axes.set_transform(plttransform.Affine2D().
                                                             rotate_around(position_x + 0.5 * dimension_width,
                                                                           position_y + 0.5 * dimension_height,
                                                                           slope) + ax.transData)

                    # draw a render curve
                    if features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'renderCurve':
                        curve_shape = features['graphicalShape']['geometricShapes'][gs_index]
                        if 'strokeColor' in list(curve_shape.keys()):
                            stroke_color = curve_shape['strokeColor']
                        if 'strokeWidth' in list(curve_shape.keys()):
                            stroke_width = curve_shape['strokeWidth']
                        if 'strokeDashArray' in list(curve_shape.keys()):
                            stroke_dash_array = (0, curve_shape['graphicalShape']['strokeDashArray'])

                        curve_features = {'graphicalCurve': {'strokeColor': stroke_color,
                                                             'strokeWidth': stroke_width,
                                                             'strokeDashArray': stroke_dash_array}}

                        # add a render curve to plot
                        if 'vertices' in list(curve_shape.keys()):
                            curve_features['curve'] = []
                            for v_index in range(len(curve_shape['vertices']) - 1):
                                element_ = {'startX': curve_shape['vertices'][v_index]['renderPointX']['abs'] +
                                                      0.01 * curve_shape['vertices'][v_index]['renderPointX']['rel'] *
                                                      bbox_width + bbox_x,
                                            'startY': curve_shape['vertices'][v_index]['renderPointY']['abs'] +
                                                      0.01 * curve_shape['vertices'][v_index]['renderPointY']['rel'] *
                                                      bbox_height + bbox_y,
                                            'endX': curve_shape['vertices'][v_index + 1]['renderPointX']['abs'] +
                                                    0.01 * curve_shape['vertices'][v_index + 1]['renderPointX']['rel'] *
                                                    bbox_width + bbox_x,
                                            'endY': curve_shape['vertices'][v_index + 1]['renderPointY']['abs'] +
                                                    0.01 * curve_shape['vertices'][v_index + 1]['renderPointY']['rel'] *
                                                    bbox_height + + bbox_y}

                                if 'basePoint1X' in list(curve_shape['vertices'][v_index].keys()):
                                    element_ = {'basePoint1X': curve_shape['vertices'][v_index]['basePoint1X']['abs'] +
                                                               0.01 * curve_shape['vertices'][v_index]['basePoint1X'][
                                                                   'rel'] *
                                                               bbox_width + bbox_x,
                                                'basePoint1Y': curve_shape['vertices'][v_index]['basePoint1Y']['abs'] +
                                                               0.01 * curve_shape['vertices'][v_index]['basePoint1Y'][
                                                                   'rel'] *
                                                               bbox_height + bbox_y,
                                                'basePoint2X': curve_shape['vertices'][v_index]['basePoint2X']['abs'] +
                                                               0.01 * curve_shape['vertices'][v_index]['basePoint2X'][
                                                                   'rel'] *
                                                               bbox_width + bbox_x,
                                                'basePoint2Y': curve_shape['vertices'][v_index]['basePoint2Y']['abs'] +
                                                               0.01 * curve_shape['vertices'][v_index]['basePoint2Y'][
                                                                   'rel'] *
                                                               bbox_height + bbox_y}

                                curve_features['curve'].append(element_)

                            draw_curve(ax, curve_features, z_order=3)

                    # draw a rounded rectangle
                    elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'rectangle':
                        rectangle_shape = features['graphicalShape']['geometricShapes'][gs_index]

                        # default features
                        position_x = bbox_x
                        position_y = bbox_y
                        dimension_width = bbox_width
                        dimension_height = bbox_height
                        corner_radius = 0.0

                        if 'strokeColor' in list(rectangle_shape.keys()):
                            stroke_color = rectangle_shape['strokeColor']
                        if 'strokeWidth' in list(rectangle_shape.keys()):
                            stroke_width = rectangle_shape['strokeWidth']
                        if 'strokeDashArray' in list(rectangle_shape.keys()):
                            stroke_dash_array = (0, rectangle_shape['strokeDashArray'])
                        if 'fillColor' in list(rectangle_shape.keys()):
                            fill_color = rectangle_shape['fillColor']
                        if 'x' in list(rectangle_shape.keys()):
                            position_x += rectangle_shape['x']['abs'] + \
                                          0.01 * rectangle_shape['x']['rel'] * bbox_width
                        if 'y' in list(rectangle_shape.keys()):
                            position_y += rectangle_shape['y']['abs'] + \
                                          0.01 * rectangle_shape['y']['rel'] * bbox_height
                        if 'width' in list(rectangle_shape.keys()):
                            dimension_width = rectangle_shape['width']['abs'] + \
                                              0.01 * rectangle_shape['width']['rel'] * bbox_width
                        if 'height' in list(rectangle_shape.keys()):
                            dimension_height = rectangle_shape['height']['abs'] + \
                                               0.01 * rectangle_shape['height']['rel'] * bbox_height
                        if 'ratio' in list(rectangle_shape.keys()) and rectangle_shape['ratio'] > 0.0:
                            if (bbox_width / bbox_height) <= rectangle_shape['ratio']:
                                dimension_width = bbox_width
                                dimension_height = bbox_width / rectangle_shape['ratio']
                                position_y += 0.5 * (bbox_height - dimension_height)
                            else:
                                dimension_height = bbox_height
                                dimension_width = rectangle_shape['ratio'] * bbox_height
                                position_x += 0.5 * (bbox_width - dimension_width)
                        if 'rx' in list(rectangle_shape.keys()):
                            corner_radius = rectangle_shape['rx']['abs'] +\
                                       0.01 * rectangle_shape['rx']['rel'] * 0.5 * (bbox_width + bbox_height)
                        elif 'ry' in list(rectangle_shape.keys()):
                            corner_radius = rectangle_shape['ry']['abs'] + \
                                     0.01 * rectangle_shape['ry']['rel'] * 0.5 * (bbox_width + bbox_height)

                        # add a rounded rectangle to plot
                        fancy_box = FancyBboxPatch((position_x, position_y), dimension_width, dimension_height,
                                                   edgecolor=find_color_value(stroke_color, False),
                                                   facecolor=find_color_value(fill_color), fill=True,
                                                   linewidth=stroke_width, linestyle=stroke_dash_array,
                                                   zorder=z_order, antialiased=True)
                        fancy_box.set_boxstyle("round", rounding_size=corner_radius)
                        if offest_x or offest_y:
                            fancy_box.set_transform(plttransform.Affine2D().
                                                    rotate_around(offest_x, offest_y, slope) + ax.transData)
                        else:
                            fancy_box.set_transform(plttransform.Affine2D().
                                                    rotate_around(position_x + 0.5 * dimension_width,
                                                                  position_y + 0.5 * dimension_height,
                                                                  slope) + ax.transData)
                        ax.add_patch(fancy_box)

                    # draw an ellipse
                    elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'ellipse':
                        ellipse_shape = features['graphicalShape']['geometricShapes'][gs_index]

                        # default features
                        position_cx = bbox_x
                        position_cy = bbox_y
                        dimension_rx = 0.5 * bbox_width
                        dimension_ry = 0.5 * bbox_height

                        if 'strokeColor' in list(ellipse_shape.keys()):
                            stroke_color = ellipse_shape['strokeColor']
                        if 'strokeWidth' in list(ellipse_shape.keys()):
                            stroke_width = ellipse_shape['strokeWidth']
                        if 'strokeDashArray' in list(ellipse_shape.keys()):
                            stroke_dash_array = (0, ellipse_shape['strokeDashArray'])
                        if 'fillColor' in list(ellipse_shape.keys()):
                            fill_color = ellipse_shape['fillColor']
                        if 'cx' in list(ellipse_shape.keys()):
                            position_cx += ellipse_shape['cx']['abs'] + 0.01 * ellipse_shape['cx']['rel'] * bbox_width
                        if 'cy' in list(ellipse_shape.keys()):
                            position_cy += ellipse_shape['cy']['abs'] + 0.01 * ellipse_shape['cy']['rel'] * bbox_height
                        if 'rx' in list(ellipse_shape.keys()):
                            dimension_rx = ellipse_shape['rx']['abs'] + 0.01 * ellipse_shape['rx']['rel'] * bbox_width
                        if 'ry' in list(ellipse_shape.keys()):
                            dimension_ry = ellipse_shape['ry']['abs'] + \
                                           0.01 * ellipse_shape['ry']['rel'] * bbox_height
                        if 'ratio' in list(ellipse_shape.keys()) and ellipse_shape['ratio'] > 0.0:
                            if (bbox_width / bbox_height) <= ellipse_shape['ratio']:
                                dimension_rx = 0.5 * bbox_width
                                dimension_ry = (0.5 * bbox_width / ellipse_shape['ratio'])
                            else:
                                dimension_ry = 0.5 * bbox_height
                                dimension_rx = ellipse_shape['ratio'] * 0.5 * bbox_height

                        # add an ellipse to plot
                        ellipse = Ellipse((position_cx, position_cy), 2 * dimension_rx, 2 * dimension_ry,
                                          edgecolor=find_color_value(stroke_color, False),
                                          facecolor=find_color_value(fill_color), fill=True,
                                          linewidth=stroke_width, linestyle=stroke_dash_array,
                                          zorder=z_order, antialiased=True)
                        if offest_x or offest_y:
                            ellipse.set_transform(plttransform.Affine2D().rotate_around(offest_x,
                                                                                        offest_y, slope) + ax.transData)
                        else:
                            ellipse.set_transform(plttransform.Affine2D().
                                                  rotate_around(position_cx, position_cy, slope) + ax.transData)
                        ax.add_patch(ellipse)

                    # draw a polygon
                    elif features['graphicalShape']['geometricShapes'][gs_index]['shape'] == 'polygon':
                        polygon_shape = features['graphicalShape']['geometricShapes'][gs_index]

                        if 'strokeColor' in list(polygon_shape.keys()):
                            stroke_color = polygon_shape['strokeColor']
                        if 'strokeWidth' in list(polygon_shape.keys()):
                            stroke_width = polygon_shape['strokeWidth']
                        if 'strokeDashArray' in list(polygon_shape.keys()):
                            stroke_dash_array = (0, polygon_shape['strokeDashArray'])
                        if 'fillColor' in list(polygon_shape.keys()):
                            fill_color = polygon_shape['fillColor']
                        # if 'fillRule' in list(polygon_shape.keys()):
                        # fill_rule = polygon_shape['fillRule']

                        # add a polygon to plot
                        if 'vertices' in list(polygon_shape.keys()):
                            vertices = np.empty((0, 2))
                            for v_index in range(len(polygon_shape['vertices'])):
                                vertices = np.append(vertices,
                                                     np.array([[polygon_shape['vertices'][v_index]
                                                                ['renderPointX']['abs'] +
                                                                0.01 * polygon_shape['vertices'][v_index]
                                                                ['renderPointX']['rel'] * bbox_width,
                                                                polygon_shape['vertices'][v_index]
                                                                ['renderPointY']['abs'] +
                                                                0.01 * polygon_shape['vertices'][v_index]
                                                                ['renderPointY']['rel'] * bbox_height]]), axis=0)

                            if offest_x or offest_y:
                                vertices[:, 0] += offest_x - bbox_width
                                vertices[:, 1] += offest_y - 0.5 * bbox_height
                                polygon = Polygon(vertices, closed=True,
                                                  edgecolor=find_color_value(stroke_color, False),
                                                  facecolor=find_color_value(fill_color),
                                                  fill=True, linewidth=stroke_width, linestyle=stroke_dash_array,
                                                  antialiased=True)
                                polygon.set_transform(
                                    plttransform.Affine2D().rotate_around(offest_x, offest_y, slope) + ax.transData)
                            else:
                                polygon = Polygon(vertices, closed=True,
                                                  edgecolor=find_color_value(stroke_color, False),
                                                  facecolor=find_color_value(fill_color),
                                                  fill=True, linewidth=stroke_width, linestyle=stroke_dash_array,
                                                  zorder=z_order, antialiased=True)
                            ax.add_patch(polygon)

            else:
                # add a simple rectangle to plot
                rectangle = Rectangle((bbox_x, bbox_y), bbox_width, bbox_height, slope * (180.0 / math.pi),
                                      edgecolor=find_color_value(stroke_color, False),
                                      facecolor=find_color_value(fill_color), fill=True,
                                      linewidth=stroke_width, linestyle=stroke_dash_array,
                                      zorder=z_order, antialiased=True)
                ax.add_patch(rectangle)


def draw_curve(ax, features, z_order=1):
    if 'curve' in list(features.keys()):
        # default features
        stroke_color = 'black'
        stroke_width = '1.0'
        stroke_dash_array = 'solid'

        if 'graphicalCurve' in list(features.keys()):
            if 'strokeColor' in list(features['graphicalCurve'].keys()):
                stroke_color = features['graphicalCurve']['strokeColor']
            if 'strokeWidth' in list(features['graphicalCurve'].keys()):
                stroke_width = features['graphicalCurve']['strokeWidth']
            if 'strokeDashArray' in list(features['graphicalCurve'].keys()) \
                    and not features['graphicalCurve']['strokeDashArray'] == 'solid':
                stroke_dash_array = (0, features['graphicalCurve']['strokeDashArray'])

        for v_index in range(len(features['curve'])):
            vertices = [(features['curve'][v_index]['startX'], features['curve'][v_index]['startY'])]
            codes = [Path.MOVETO]
            if 'basePoint1X' in list(features['curve'][v_index].keys()):
                vertices.append((features['curve'][v_index]['basePoint1X'], features['curve'][v_index]['basePoint1Y']))
                vertices.append((features['curve'][v_index]['basePoint2X'], features['curve'][v_index]['basePoint2Y']))
                codes.append(Path.CURVE4)
                codes.append(Path.CURVE4)
                codes.append(Path.CURVE4)
            else:
                codes.append(Path.LINETO)
            vertices.append((features['curve'][v_index]['endX'], features['curve'][v_index]['endY']))

            # draw a curve
            curve = PathPatch(Path(vertices, codes), edgecolor=find_color_value(stroke_color, False),
                              facecolor='none', linewidth=stroke_width, linestyle=stroke_dash_array,
                              capstyle='butt', zorder=z_order, antialiased=True)
            ax.add_patch(curve)


def draw_text(ax, features):
    if 'plainText' in list(features.keys()) and 'boundingBox' in list(features.keys()):
        plain_text = features['plainText']
        bbox_x = features['boundingBox']['x']
        bbox_y = features['boundingBox']['y']
        bbox_width = features['boundingBox']['width']
        bbox_height = features['boundingBox']['height']

        # default features
        font_color = 'black'
        font_family = 'monospace'
        font_size = '12.0'
        font_style = 'normal'
        font_weight = 'normal'
        h_text_anchor = 'center'
        v_text_anchor = 'center'

        if 'graphicalText' in list(features.keys()):
            if 'strokeColor' in list(features['graphicalText'].keys()):
                font_color = find_color_value(features['graphicalText']['strokeColor'], False)
            if 'fontFamily' in list(features['graphicalText'].keys()):
                font_family = features['graphicalText']['fontFamily']
            if 'fontSize' in list(features['graphicalText'].keys()):
                font_size = features['graphicalText']['fontSize']['abs'] + \
                            0.01 * features['graphicalText']['fontSize']['rel'] * bbox_width
            if 'fontStyle' in list(features['graphicalText'].keys()):
                font_style = features['graphicalText']['fontStyle']
            if 'fontWeight' in list(features['graphicalText'].keys()):
                font_weight = features['graphicalText']['fontWeight']
            if 'hTextAnchor' in list(features['graphicalText'].keys()):
                if features['graphicalText']['hTextAnchor'] == 'start':
                    h_text_anchor = 'left'
                elif features['graphicalText']['hTextAnchor'] == 'middle':
                    h_text_anchor = 'center'
                elif features['graphicalText']['hTextAnchor'] == 'end':
                    h_text_anchor = 'right'
            if 'vTextAnchor' in list(features['graphicalText'].keys()):
                if features['graphicalText']['vTextAnchor'] == 'middle':
                    v_text_anchor = 'center'
                else:
                    v_text_anchor = features['graphicalText']['vTextAnchor']

            # get geometric shape features
            if 'geometricShapes' in list(features['graphicalText'].keys()):
                for gs_index in range(len(features['graphicalText']['geometricShapes'])):
                    position_x = bbox_x
                    position_y = bbox_y

                    if 'x' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                        position_x += features['graphicalText']['geometricShapes'][gs_index]['x']['abs'] + \
                                      0.01 * features['graphicalText']['geometricShapes'][gs_index]['x']['rel'] \
                                      * bbox_width
                    if 'y' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                        position_y += features['graphicalText']['geometricShapes'][gs_index]['y']['abs'] + \
                                      0.01 * features['graphicalText']['geometricShapes'][gs_index]['y']['rel'] \
                                      * bbox_height
                    if 'strokeColor' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                        font_color = find_color_value(
                            features['graphicalText']['geometricShapes'][gs_index]['strokeColor'], False)
                    if 'fontFamily' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                        font_family = features['graphicalText']['geometricShapes'][gs_index]['fontFamily']
                    if 'fontSize' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                        font_size = features['graphicalText']['geometricShapes'][gs_index]['fontSize']['abs'] + \
                                    0.01 * features['graphicalText']['geometricShapes'][gs_index]['fontSize']['rel'] \
                                    * bbox_width
                    if 'fontStyle' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                        font_style = features['graphicalText']['geometricShapes'][gs_index]['fontStyle']
                    if 'fontWeight' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                        font_weight = features['graphicalText']['geometricShapes'][gs_index]['fontWeight']
                    if 'hTextAnchor' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                        if features['graphicalText']['geometricShapes'][gs_index]['hTextAnchor'] == 'start':
                            h_text_anchor = 'left'
                        elif features['graphicalText']['geometricShapes'][gs_index]['hTextAnchor'] == 'middle':
                            h_text_anchor = 'center'
                        elif features['graphicalText']['geometricShapes'][gs_index]['hTextAnchor'] == 'end':
                            h_text_anchor = 'right'
                    if 'vTextAnchor' in list(features['graphicalText']['geometricShapes'][gs_index].keys()):
                        if features['graphicalText']['geometricShapes'][gs_index]['vTextAnchor'] == 'middle':
                            v_text_anchor = 'center'
                        else:
                            v_text_anchor = features['graphicalText']['geometricShapes'][gs_index]['vTextAnchor']

                    # draw text
                    ax.text(position_x + 0.5 * bbox_width, position_y + 0.5 * bbox_height, plain_text,
                            color=font_color, fontfamily=font_family, fontsize=font_size,
                            fontstyle=font_style, fontweight=font_weight,
                            va=v_text_anchor, ha=h_text_anchor, zorder=5)

            # draw the text itself
            else:
                ax.text(bbox_x + 0.5 * bbox_width, bbox_y + 0.5 * bbox_height, plain_text,
                        color=font_color, fontfamily=font_family, fontsize=font_size,
                        fontstyle=font_style, fontweight=font_weight,
                        va=v_text_anchor, ha=h_text_anchor, zorder=5)


def draw_line_endings(ax, features):
    if 'graphicalCurve' in list(features.keys()) and 'heads' in list(features['graphicalCurve'].keys()):
        # draw start head
        if 'start' in list(features['graphicalCurve']['heads'].keys()):
            line_ending = find_line_ending(features['graphicalCurve']['heads']['start'])
            if 'features' in list(line_ending.keys()):
                if 'enableRotation' in list(line_ending['features'].keys()) \
                        and not line_ending['features']['enableRotation']:
                    draw_graphical_shape(ax, line_ending['features'],
                                         offset_x=features['startPoint']['x'],
                                         offset_y=features['startPoint']['y'], z_order=2)
                else:
                    draw_graphical_shape(ax, line_ending['features'],
                                         offest_x=features['startPoint']['x'], offest_y=features['startPoint']['y'],
                                         slope=features['startSlope'], z_order=2)

        # draw end head
        if 'end' in list(features['graphicalCurve']['heads'].keys()):
            line_ending = find_line_ending(features['graphicalCurve']['heads']['end'])
            if 'features' in list(line_ending.keys()):
                if 'enableRotation' in list(line_ending['features'].keys()) \
                        and not line_ending['features']['enableRotation']:
                    draw_graphical_shape(ax, line_ending['features'],
                                         offset_x=features['endPoint']['x'],
                                         offset_y=features['endPoint']['y'], z_order=2)
                else:
                    draw_graphical_shape(ax, line_ending['features'],
                                         offest_x=features['endPoint']['x'], offest_y=features['endPoint']['y'],
                                         slope=features['endSlope'], z_order=2)


def fit_text_to_bbox(text_features):
    if is_layout_modified \
            and 'boundingBox' in list(text_features.keys()) \
            and 'plainText' in list(text_features.keys()) \
            and 'graphicalText' in list(text_features.keys()) \
            and 'fontFamily' in list(text_features['graphicalText'].keys()) \
            and 'fontSize' in list(text_features['graphicalText'].keys()):
        fp = FontProperties(family=text_features['graphicalText']['fontFamily'],
                            size=text_features['graphicalText']['fontSize']['abs']
                            + 0.01 * text_features['graphicalText']['fontSize']['rel']
                            * text_features['boundingBox']['width'])
        text_width, text_height, text_descent = TextToPath().get_text_width_height_descent(s=text_features['plainText'],
                                                                                           prop=fp, ismath=False)
        char_width = text_width / len(text_features['plainText'])
        if text_width > text_features['boundingBox']['width'] - char_width:
            while text_width > text_features['boundingBox']['width'] - char_width:
                text_features['plainText'] = text_features['plainText'][:-1]
                text_width -= char_width
            text_features['plainText'] += "."


def get_node_features(go, node, style):
    if 'text' in list(go.keys()) and 'features' in list(go['text'].keys()):
        if 'plainText' in list(go['text']['features'].keys()):
            node['data']['name'] = go['text']['features']['plainText']
        if 'graphicalText' in list(go['text']['features'].keys()):
            if 'strokeColor' in list(go['text']['features']['graphicalText'].keys()):
                style['css']['color'] = \
                    find_color_value(go['text']['features']['graphicalText']['strokeColor'])
            if 'fontFamily' in list(go['text']['features']['graphicalText'].keys()):
                style['css']['font-family'] = go['text']['features']['graphicalText']['fontFamily']
            if 'fontWeight' in list(go['text']['features']['graphicalText'].keys()):
                style['css']['font-weight'] = go['text']['features']['graphicalText']['fontWeight']
            if 'fontStyle' in list(go['text']['features']['graphicalText'].keys()):
                style['css']['font-style'] = go['text']['features']['graphicalText']['fontStyle']
            if 'fontSize' in list(go['text']['features']['graphicalText'].keys()) and \
                    'boundingBox' in list(go['text']['features'].keys()):
                style['css']['font-size'] = go['text']['features']['graphicalText']['fontSize']['abs'] + \
                                             go['text']['features']['boundingBox']['width'] \
                                             * go['text']['features']['graphicalText']['fontSize']['rel']
            if 'vTextAnchor' in list(go['text']['features']['graphicalText'].keys()):
                if go['text']['features']['graphicalText']['vTextAnchor'] == 'middle':
                    style['css']['text-valign'] = 'center'
                else:
                    style['css']['text-valign'] = go['text']['features']['graphicalText']['vTextAnchor']
            if 'hTextAnchor' in list(go['text']['features']['graphicalText'].keys()):
                if go['text']['features']['graphicalText']['hTextAnchor'] == 'start':
                    style['css']['text-halign'] = 'left'
                elif go['text']['features']['graphicalText']['hTextAnchor'] == 'middle':
                    style['css']['text-halign'] = 'center'
                elif go['text']['features']['graphicalText']['hTextAnchor'] == 'end':
                    style['css']['text-halign'] = 'right'
    if 'features' in list(go.keys()):
        if 'boundingBox' in list(go['features'].keys()):
            node['position'] = {'x': go['features']['boundingBox']['x']
                                + 0.5 * go['features']['boundingBox']['width'],
                                'y': go['features']['boundingBox']['y']
                                + 0.5 * go['features']['boundingBox']['height']}
            style['css']['width'] = go['features']['boundingBox']['width']
            style['css']['height'] = go['features']['boundingBox']['height']
        if 'graphicalShape' in list(go['features'].keys()):
            if 'strokeColor' in list(go['features']['graphicalShape'].keys()):
                style['css']['border-color'] = \
                    find_color_value(go['features']['graphicalShape']['strokeColor'])
            if 'strokeWidth' in list(go['features']['graphicalShape'].keys()):
                style['css']['border-width'] = go['features']['graphicalShape']['strokeWidth']
            if 'fillColor' in list(go['features']['graphicalShape'].keys()):
                style['css']['background-color'] = \
                    find_color_value(go['features']['graphicalShape']['fillColor'])
            if 'geometricShapes' in list(go['features']['graphicalShape'].keys()):
                if 'strokeColor' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                    style['css']['border-color'] = \
                        find_color_value(go['features']['graphicalShape']
                                         ['geometricShapes'][0]['strokeColor'])
                if 'strokeWidth' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                    style['css']['border-width'] = \
                        go['features']['graphicalShape']['geometricShapes'][0]['strokeWidth']
                if 'fillColor' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                    style['css']['background-color'] = \
                        find_color_value(go['features']['graphicalShape']['geometricShapes'][0]['fillColor'])
                if 'shape' in list(go['features']['graphicalShape']['geometricShapes'][0].keys()):
                    if go['features']['graphicalShape']['geometricShapes'][0]['shape'] == "rectangle":
                        style['css']['shape'] = 'roundrectangle'
                    elif go['features']['graphicalShape']['geometricShapes'][0]['shape'] == "ellipse":
                        style['css']['shape'] = 'ellipse'


def get_edge_features(go, edge, style):
    if 'features' in list(go.keys()):
        if 'graphicalCurve' in list(go['features'].keys()):
            if 'strokeColor' in list(go['features']['graphicalCurve'].keys()):
                style['css']['line-color'] = \
                    find_color_value(go['features']['graphicalCurve']['strokeColor'])
                style['css']['source-arrow-color'] = \
                    find_color_value(go['features']['graphicalCurve']['strokeColor'])
                style['css']['target-arrow-color'] = \
                    find_color_value(go['features']['graphicalCurve']['strokeColor'])
            if 'strokeWidth' in list(go['features']['graphicalCurve'].keys()):
                style['css']['width'] = go['features']['graphicalCurve']['strokeWidth']
            if 'role' in list(go.keys()):
                if go['role'] == "product":
                    style['css']['target-arrow-shape'] = "triangle"
                if go['role'] == "modifier":
                    style['css']['target-arrow-shape'] = "diamond"
                if go['role'] == "activator":
                    style['css']['target-arrow-shape'] = "circle"
                if go['role'] == "inhibitor":
                    style['css']['target-arrow-shape'] = "tee"
